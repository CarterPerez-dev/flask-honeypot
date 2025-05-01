# honeypot/backend/app.py
from flask import Flask, g
from flask_cors import CORS
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import redis
import logging
import geoip2.database
from honeypot.config.settings import get_config
from honeypot.database.mongodb import init_app as init_db, get_db
from honeypot.backend.helpers.geoip_manager import GeoIPManager
from honeypot.backend.helpers.proxy_detector import ProxyCache, get_proxy_detector


# Global instances for GeoIP readers
asn_reader = None
country_reader = None

def create_app(config=None):
    """
    Create and configure the Flask application for honeypot functionality
    
    Args:
        config (dict, optional): Configuration dictionary to override defaults
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Get configuration
    app_config = get_config()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app_config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=app_config.LOG_FILE
    )
    logger = logging.getLogger(__name__)
    
    # Apply default configuration
    app.config.update(
        SECRET_KEY=app_config.SECRET_KEY,
        SESSION_TYPE='redis',
        SESSION_PERMANENT=True,
        SESSION_USE_SIGNER=True,
        SESSION_KEY_PREFIX='honeypot_session:',
        SESSION_REDIS=redis.StrictRedis(
            host=app_config.REDIS_HOST,
            port=app_config.REDIS_PORT,
            db=app_config.REDIS_DB,
            password=app_config.REDIS_PASSWORD
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=not app_config.DEBUG,
        JSON_SORT_KEYS=False,
        PROPAGATE_EXCEPTIONS=True,
        PRESERVE_CONTEXT_ON_EXCEPTION=False,
        HONEYPOT_RATE_LIMIT=app_config.HONEYPOT_RATE_LIMIT,
        HONEYPOT_RATE_PERIOD=app_config.HONEYPOT_RATE_PERIOD
    )
    
    # Apply custom configuration if provided
    if config:
        app.config.update(config)
    
    # Ensure data directory exists
    os.makedirs(app_config.DATA_DIRECTORY, exist_ok=True)
    
    # Initialize GeoIP manager
    geoip_dir = app_config.GEOIP_DB_DIRECTORY
    if not geoip_dir:
        geoip_dir = os.path.join(app_config.DATA_DIRECTORY, 'geoip_db')
    
    geoip_manager = GeoIPManager(
        db_directory=geoip_dir,
        license_key=app_config.MAXMIND_LICENSE_KEY
    )
    
    # Auto-update GeoIP databases if configured
    if app_config.GEOIP_AUTO_UPDATE and app_config.MAXMIND_LICENSE_KEY:
        logger.info("Auto-updating GeoIP databases...")
        geoip_manager.update_databases()
    
    # Load GeoIP databases if they exist
    db_info = geoip_manager.get_database_info()
    
    if db_info['asn']['exists']:
        global asn_reader
        asn_reader = geoip2.database.Reader(db_info['asn']['path'])
        logger.info(f"Loaded ASN database: {db_info['asn']['path']}")
    
    if db_info['country']['exists']:
        global country_reader
        country_reader = geoip2.database.Reader(db_info['country']['path'])
        logger.info(f"Loaded Country database: {db_info['country']['path']}")
    
    # Initialize proxy cache
    proxy_cache_dir = app_config.PROXY_CACHE_DIRECTORY
    if not proxy_cache_dir:
        proxy_cache_dir = os.path.join(app_config.DATA_DIRECTORY, 'proxy_cache')
    
    proxy_cache = ProxyCache(cache_dir=proxy_cache_dir)
    
    # Store instances in app config for easy access
    app.config['GEOIP_MANAGER'] = geoip_manager
    app.config['PROXY_CACHE'] = proxy_cache
    app.config['ASN_READER'] = asn_reader
    app.config['COUNTRY_READER'] = country_reader
    
    # Setup CORS and Session
    CORS(app, supports_credentials=True)
    Session(app)


    db = init_db(app) 
    with app.app_context(): 
         from honeypot.database.mongodb import initialize_collections
         mongo_db = get_db() 
         if mongo_db:
             initialize_collections(mongo_db)
         else:
             logger.error("Failed to get MongoDB database instance for collection initialization.")
    

         app.config['PROXY_DETECTOR'] = get_proxy_detector(cache=proxy_cache)

    # Fix for proper forwarded headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    
    # Register blueprints
    from honeypot.backend.routes.admin import admin_bp
    from honeypot.backend.routes.admin import honeypot_bp
    from honeypot.backend.routes.honeypot_pages import honeypot_pages_bp
    from honeypot.backend.routes.honeypot_routes import register_routes_with_blueprint
    
    app.register_blueprint(admin_bp, url_prefix='/honeypot/admin')
    app.register_blueprint(honeypot_bp, url_prefix='/honeypot')
    app.register_blueprint(honeypot_pages_bp)
    
    # Register routes with honeypot handler
    register_routes_with_blueprint(
        blueprint=honeypot_pages_bp,
        handler_function=honeypot_bp.view_functions['honeypot_handler']
    )
    
    # Context processor for CSRF token
    from honeypot.backend.middleware.csrf_protection import generate_csrf_token
    
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf_token()}
    
    # Helper function to access GeoIP data
    @app.before_request
    def setup_geoip_readers():
        """Make GeoIP readers available in the request context"""
        g.asn_reader = asn_reader
        g.country_reader = country_reader
    
    # Basic health check endpoint
    @app.route('/health')
    def health_check():
        return 'Honeypot is running'
    
    return app

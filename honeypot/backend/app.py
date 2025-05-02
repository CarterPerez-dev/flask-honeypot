# honeypot/backend/app.py
from flask import Flask, g
from flask_cors import CORS
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import redis
import logging
from datetime import datetime, timedelta
import geoip2.database
from honeypot.config.settings import get_config
from honeypot.database.mongodb import init_app as init_db, get_db, initialize_collections
from honeypot.backend.helpers.geoip_manager import GeoIPManager
from honeypot.backend.helpers.proxy_detector import ProxyCache, get_proxy_detector


# GeoIP readers
asn_reader = None
country_reader = None

def create_app(config=None):
    """
    Flask application for honeypot config
    
    Args:
        config (dict, optional): Configuration dictionary to override defaults
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Get config
    app_config = get_config()
    
    # Logging
    logging.basicConfig(
        level=getattr(logging, app_config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=app_config.LOG_FILE
    )
    logger = logging.getLogger(__name__)
    
    
    # Ensure the secret key is set properly
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    
    # Session configuration
    app.config.update(
        SESSION_TYPE='redis',
        SESSION_PERMANENT=True,
        SESSION_USE_SIGNER=True,  # This requires SECRET_KEY to be set
        SESSION_KEY_PREFIX='honeypot_session:',
        SESSION_REDIS=redis.StrictRedis(
            host=app_config.REDIS_HOST,
            port=app_config.REDIS_PORT,
            db=app_config.REDIS_DB,
            password=app_config.REDIS_PASSWORD
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=False,  # Set to False for http development
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    )
    
    # Initialize Session AFTER setting all configs
    Session(app) 
    

###########################################################
# Apply custom configuration HERE! ########################
###########################################################

    if config:
        app.config.update(config)
        

##########################################################   
###########################################################


    os.makedirs(app_config.DATA_DIRECTORY, exist_ok=True)
    
    # Initialize GeoIP manager
    geoip_dir = app_config.GEOIP_DB_DIRECTORY
    if not geoip_dir:
        geoip_dir = os.path.join(app_config.DATA_DIRECTORY, 'geoip_db')
    
    geoip_manager = GeoIPManager(
        db_directory=geoip_dir,
        license_key=app_config.MAXMIND_LICENSE_KEY
    )
    
    # Auto-update GeoIP databases
    if app_config.GEOIP_AUTO_UPDATE and app_config.MAXMIND_LICENSE_KEY:
        logger.info("Auto-updating GeoIP databases...")
        geoip_manager.update_databases()
    
    # Load GeoIP databases
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

    # Initialize MongoDB
    init_db(app)

    # Initialize collections within app context
    with app.app_context():
        try:
            # Get DB connection
            mongo_db = get_db()

            if mongo_db is not None:
                initialize_collections(mongo_db)
                logger.info("MongoDB collections initialized successfully")
                
                try:
                    paths_cursor = mongo_db.scan_paths.find({"common": True}, {"_id": 0, "path": 1})
                    common_paths = [item['path'] for item in paths_cursor]
                    app.config['COMMON_SCAN_PATHS'] = common_paths
                    logger.info(f"Loaded {len(common_paths)} common scan paths.")
                except Exception as path_e:
                    logger.error(f"Error loading common scan paths from DB: {path_e}", exc_info=True)
                    app.config['COMMON_SCAN_PATHS'] = [] 
            else:

                logger.error("Failed to get MongoDB database instance for context setup.")
                app.config['COMMON_SCAN_PATHS'] = [] 

            try:
                app.config['PROXY_DETECTOR'] = get_proxy_detector(cache=proxy_cache)
                logger.info("Proxy detector initialized successfully")
            except Exception as proxy_e:
                logger.error(f"Error initializing proxy detector: {str(proxy_e)}", exc_info=True)
        except Exception as e: 
            logger.error(f"Error during app context setup (DB connection/collection init): {str(e)}", exc_info=True)

            app.config.setdefault('COMMON_SCAN_PATHS', [])
            app.config.setdefault('PROXY_DETECTOR', None) 



    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    
    # Blueprints
    from honeypot.backend.routes.admin import angela_bp
    from honeypot.backend.routes.honeypot import honeypot_bp
    from honeypot.backend.routes.honeypot_pages import honeypot_pages_bp, catch_all_honeypot
    from honeypot.backend.routes.honeypot_routes import register_routes_with_blueprint
 


###########################################################
##########################################################
# ██████╗    ██████╗  ██╗   ██╗ ████████╗ ███████╗ ███████╗
# ██╔══██╗  ██╔═══██╗ ██║   ██║ ╚══██╔══╝ ██╔════╝ ██╔════╝
# ██████╔╝  ██║   ██║ ██║   ██║    ██║    ███████╗ ███████╗
# ██╔══██╗  ██║   ██║ ██║   ██║    ██║    ██╔════╝ ╚════██║
# ██║  ██║  ╚██████╔╝ ╚██████╔╝    ██║    ███████║ ███████║
# ╚═╝  ╚═╝   ╚═════╝   ╚═════╝     ╚═╝    ╚══════╝ ╚══════╝
###########################################################
###########################################################
   
    app.register_blueprint(angela_bp, url_prefix='/honeypot/angela')
    app.register_blueprint(honeypot_bp, url_prefix='/honeypot')
       

    register_routes_with_blueprint(
        blueprint=honeypot_pages_bp,
        handler_function=catch_all_honeypot
    )
    
    
    app.register_blueprint(honeypot_pages_bp)   
    
    
###############################################################
###############################################################
###############################################################

    from honeypot.backend.middleware.csrf_protection import generate_csrf_token
    
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf_token()}
   
 
    # Access GeoIP data
    @app.before_request
    def setup_geoip_readers():
        """Make GeoIP readers available in the request context"""
        g.asn_reader = asn_reader
        g.country_reader = country_reader
    

    @app.route('/api/health')
    def health_check():
        return 'Honeypot is running'
    
    return app

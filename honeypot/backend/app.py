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
import traceback
from honeypot.config.settings import get_config
from honeypot.database.mongodb import init_app as init_db, get_db, get_mongo_client, initialize_collections
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
    

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    
    # Session configuration
    app.config.update(
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
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    )
    
    # Initialize Session AFTER setting all configs
    try:
        Session(app)
        logger.info("Flask-Session initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Flask-Session: {e}")
        logger.error(traceback.format_exc())


    # custom config
    if config:
        app.config.update(config)
        

    try:
        os.makedirs(app_config.DATA_DIRECTORY, exist_ok=True)
        logger.info(f"Ensured data directory exists: {app_config.DATA_DIRECTORY}")
    except Exception as e:
        logger.error(f"Failed to create data directory: {e}")
    
    # Initialize GeoIP manager
    geoip_dir = app_config.GEOIP_DB_DIRECTORY
    if not geoip_dir:
        geoip_dir = os.path.join(app_config.DATA_DIRECTORY, 'geoip_db')
    
    try:
        geoip_manager = GeoIPManager(
            db_directory=geoip_dir,
            license_key=app_config.MAXMIND_LICENSE_KEY
        )
        logger.info(f"GeoIP manager initialized with directory: {geoip_dir}")
    except Exception as e:
        logger.error(f"Error initializing GeoIP manager: {e}")
        geoip_manager = None
    
    # Auto-update GeoIP databases
    if geoip_manager and app_config.GEOIP_AUTO_UPDATE and app_config.MAXMIND_LICENSE_KEY:
        try:
            logger.info("Auto-updating GeoIP databases...")
            geoip_manager.update_databases()
        except Exception as e:
            logger.error(f"Error updating GeoIP databases: {e}")
    
    # Load GeoIP databases
    global asn_reader, country_reader
    
    if geoip_manager:
        try:
            db_info = geoip_manager.get_database_info()
            
            if db_info['asn']['exists']:
                try:
                    asn_reader = geoip2.database.Reader(db_info['asn']['path'])
                    logger.info(f"Loaded ASN database: {db_info['asn']['path']}")
                except Exception as e:
                    logger.error(f"Error loading ASN database: {e}")
            
            if db_info['country']['exists']:
                try:
                    country_reader = geoip2.database.Reader(db_info['country']['path'])
                    logger.info(f"Loaded Country database: {db_info['country']['path']}")
                except Exception as e:
                    logger.error(f"Error loading Country database: {e}")
        except Exception as e:
            logger.error(f"Error getting GeoIP database info: {e}")
    
    # Initialize proxy cache
    proxy_cache_dir = app_config.PROXY_CACHE_DIRECTORY
    if not proxy_cache_dir:
        proxy_cache_dir = os.path.join(app_config.DATA_DIRECTORY, 'proxy_cache')
    
    try:
        proxy_cache = ProxyCache(cache_dir=proxy_cache_dir)
        logger.info(f"Proxy cache initialized with directory: {proxy_cache_dir}")
    except Exception as e:
        logger.error(f"Error initializing proxy cache: {e}")
        proxy_cache = None
    
    # Store instances in app config for easy access
    app.config['GEOIP_MANAGER'] = geoip_manager
    app.config['PROXY_CACHE'] = proxy_cache
    app.config['ASN_READER'] = asn_reader
    app.config['COUNTRY_READER'] = country_reader
    
    # Setup CORS and Session
    try:
        CORS(app, supports_credentials=True)
        logger.info("CORS middleware initialized")
    except Exception as e:
        logger.error(f"Error initializing CORS: {e}")
    
    # Initialize MongoDB
    try:
        init_db(app)
        logger.info("MongoDB initialization initiated")
    except Exception as e:
        logger.error(f"Error initializing MongoDB connection: {e}")
        # Create empty mongodb extension to prevent attribute errors
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['mongodb'] = {'db': None}

    # Initialize app.extensions dictionary if it doesn't exist
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    
    # Initialize app.config defaults
    app.config.setdefault('COMMON_SCAN_PATHS', [])
    app.config.setdefault('PROXY_DETECTOR', None)

    # Initialize collections within app context
    with app.app_context():
        try:
            # Get DB connection
            mongo_db = get_db()

            if mongo_db is not None:
                # Store in app extensions for convenience
                app.extensions['mongodb'] = {'db': mongo_db}
                
                # Try to load common scan paths if the collection exists
                try:
                    paths_cursor = mongo_db.scan_paths.find({"common": True}, {"_id": 0, "path": 1})
                    common_paths = [item['path'] for item in paths_cursor]
                    app.config['COMMON_SCAN_PATHS'] = common_paths
                    logger.info(f"Loaded {len(common_paths)} common scan paths.")
                except Exception as path_e:
                    logger.error(f"Error loading common scan paths from DB: {path_e}")
                    logger.error(traceback.format_exc())
                    app.config['COMMON_SCAN_PATHS'] = [] 
            else:
                # Handle case when DB connection failed
                logger.error("Failed to get MongoDB database instance for context setup.")
                app.extensions['mongodb'] = {'db': None}
                app.config['COMMON_SCAN_PATHS'] = [] 

            # Initialize proxy detector with fallback
            try:
                if proxy_cache:
                    app.config['PROXY_DETECTOR'] = get_proxy_detector(cache=proxy_cache)
                    logger.info("Proxy detector initialized successfully")
                else:
                    logger.warning("Skipped proxy detector initialization - proxy cache not available")
                    app.config['PROXY_DETECTOR'] = None
            except Exception as proxy_e:
                logger.error(f"Error initializing proxy detector: {str(proxy_e)}")
                logger.error(traceback.format_exc())
                app.config['PROXY_DETECTOR'] = None
        except Exception as e: 
            logger.error(f"Error during app context setup: {str(e)}")
            logger.error(traceback.format_exc())
            app.extensions.setdefault('mongodb', {'db': None})
            app.config.setdefault('COMMON_SCAN_PATHS', [])
            app.config.setdefault('PROXY_DETECTOR', None)

    # Configure for proxy headers
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
   
    try:
        app.register_blueprint(angela_bp, url_prefix='/honeypot/angela')
        logger.info("Registered angela_bp blueprint")
    except Exception as e:
        logger.error(f"Error registering angela_bp blueprint: {e}")
    
    try:
        app.register_blueprint(honeypot_bp, url_prefix='/honeypot')
        logger.info("Registered honeypot_bp blueprint")
    except Exception as e:
        logger.error(f"Error registering honeypot_bp blueprint: {e}")

    try:
        register_routes_with_blueprint(
            blueprint=honeypot_pages_bp,
            handler_function=catch_all_honeypot
        )
        logger.info("Registered routes with honeypot_pages_bp blueprint")
    except Exception as e:
        logger.error(f"Error registering routes with honeypot_pages_bp blueprint: {e}")
    
    try:
        app.register_blueprint(honeypot_pages_bp)
        logger.info("Registered honeypot_pages_bp blueprint")
    except Exception as e:
        logger.error(f"Error registering honeypot_pages_bp blueprint: {e}")
    
###############################################################
###############################################################
###############################################################

    from honeypot.backend.middleware.csrf_protection import generate_csrf_token
    
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf_token()}
   

    @app.before_request
    def setup_geoip_readers():
        """Make GeoIP readers available in the request context"""
        g.asn_reader = asn_reader
        g.country_reader = country_reader
    
    @app.route('/api/health')
    def health_check():
        """Basic health check endpoint"""
        try:
            db = get_db()
            db_status = "OK" if db else "Not Connected"
        except Exception:
            db_status = "Error"
        
        return {
            'status': 'running',
            'server_time': datetime.utcnow().isoformat(),
            'database': db_status
        }
    
    return app

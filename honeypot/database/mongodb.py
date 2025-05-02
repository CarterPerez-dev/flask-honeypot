from pymongo import MongoClient
import os
from flask import g, current_app
import logging
import traceback
import threading

logger = logging.getLogger(__name__)


_mongo_client = None
_mongo_client_lock = threading.Lock()

def get_mongo_client():
    """
    Get or create MongoDB client singleton
    
    Returns:
        MongoClient: MongoDB client object
    """
    global _mongo_client
    

    if _mongo_client is not None:
        try:

            _mongo_client.admin.command('ping')
            return _mongo_client
        except Exception as e:
            logger.warning(f"Existing MongoDB client invalid, will create new one: {e}")

    

    with _mongo_client_lock:
        if _mongo_client is not None:
            try:
                _mongo_client.admin.command('ping')
                return _mongo_client
            except:              
                pass
        
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/honeypot')
        try:
            client = MongoClient(
                mongo_uri, 
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
                maxPoolSize=50,
                minPoolSize=5,
                maxIdleTimeMS=60000,
                waitQueueTimeoutMS=10000
            )
            
            client.admin.command('ping')
            logger.info(f"Created new MongoDB client connection: {mongo_uri}")
            

            _mongo_client = client
            return client
        except Exception as e:
            logger.error(f"Failed to create MongoDB client: {e}")
            logger.error(traceback.format_exc())
            return None

def get_db():
    """
    Get MongoDB database connection
    
    Returns:
        pymongo.database.Database: MongoDB database object or None if connection fails
    """

    if 'db' not in g:
        client = get_mongo_client()
        if client is None:
            logger.error("Failed to get MongoDB client")
            return None
        
        try:

            mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/honeypot')
            db_name = mongo_uri.split('/')[-1].split('?')[0]  
            

            g.db = client[db_name]
            
            logger.debug(f"Connected to MongoDB database: {db_name}")
            return g.db
        except Exception as e:
            logger.error(f"Error getting MongoDB database: {e}")
            logger.error(traceback.format_exc())
            return None
    
    return g.db

def close_db(e=None):
    """
    Clean up request-specific resources.
    """
    g.pop('db', None)

def cleanup_db_connections():
    """
    Cleanup MongoDB connections on application shutdown
    """
    global _mongo_client
    if _mongo_client is not None:
        try:
            _mongo_client.close()
            logger.info("Closed MongoDB client on application shutdown")
        except Exception as e:
            logger.error(f"Error closing MongoDB client: {e}")
        finally:
            _mongo_client = None

def initialize_collections(db):
    """
    Initialize MongoDB collections with proper indexes
    
    Args:
        db: MongoDB database instance
    """
    if db is None:
        logger.error("Cannot initialize collections: Database connection is None")
        return
        
    try:

        if "honeypot_interactions" not in db.list_collection_names():
            try:
                db.create_collection("honeypot_interactions")
                logger.info("Created honeypot_interactions collection")
            except Exception as e:
                logger.error(f"Error creating honeypot_interactions collection: {e}")
        

        collections_and_indexes = {
            "honeypot_interactions": [
                "timestamp",
                "ip_address",
                "page_type",
                "interaction_type"
            ],
            "scanAttempts": [
                "timestamp",
                "clientId",
                "ip",
                [("ip", 1), ("timestamp", -1)]
            ],
            "watchList": [
                {"key": "clientId", "unique": True},
                "ip",
                "severity"
            ],
            "securityBlocklist": [
                "clientId",
                "ip",
                "blockUntil"
            ],
            "admin_login_attempts": [
                "ip",
                "lastAttempt"
            ]
        }
        

        for collection_name, indexes in collections_and_indexes.items():
            try:          
                if collection_name not in db.list_collection_names():
                    try:
                        db.create_collection(collection_name)
                        logger.info(f"Created collection: {collection_name}")
                    except Exception as e:
                        logger.error(f"Error creating collection {collection_name}: {e}")
                        continue 
                
                collection = db[collection_name]
                for index in indexes:
                    try:
                        if isinstance(index, dict):
                            key = index.pop("key")
                            collection.create_index(key, **index)
                            logger.info(f"Created index on {collection_name}.{key} with options")
                        elif isinstance(index, list):
                            collection.create_index(index)
                            logger.info(f"Created compound index on {collection_name}")
                        else:
                            collection.create_index(index)
                            logger.info(f"Created index on {collection_name}.{index}")
                    except Exception as e:
                        logger.error(f"Error creating index on {collection_name}.{index}: {e}")
            except Exception as e:
                logger.error(f"Error processing collection {collection_name}: {e}")
        
        logger.info("MongoDB collections initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing collections: {e}")
        logger.error(traceback.format_exc())

def init_app(app):
    """
    Initialize MongoDB with Flask application
    
    Args:
        app (Flask): Flask application
    """

    app.teardown_appcontext(close_db)
    app.teardown_appcontext(lambda e: None)  
    

    app.before_first_request(lambda: app.atexit(cleanup_db_connections))
    

    if not hasattr(app, 'extensions'):
        app.extensions = {}
    

    with app.app_context():
        try:
            db = get_db()
            if db:
                app.extensions['mongodb'] = {'db': db}
                

                initialize_collections(db)
                logger.info("MongoDB initialization complete")
            else:
                app.extensions['mongodb'] = {'db': None}
                logger.warning("MongoDB connection failed during initialization")
        except Exception as e:
            app.extensions['mongodb'] = {'db': None}
            logger.error(f"Exception during MongoDB initialization: {e}")
            logger.error(traceback.format_exc())




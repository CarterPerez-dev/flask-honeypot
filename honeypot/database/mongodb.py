from pymongo import MongoClient
import os
from flask import g, current_app
import logging
import traceback

logger = logging.getLogger(__name__)

def get_db():
    """
    Get MongoDB database connection
    
    Returns:
        pymongo.database.Database: MongoDB database object or None if connection fails
    """
    if 'db' not in g:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/honeypot')
        
        try:
            # Create client and connect to database
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            db_name = mongo_uri.split('/')[-1]
            g.db = client[db_name]
            g.mongo_client = client
            
            # Test connection with timeout
            client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {mongo_uri}")
            
            return g.db
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.error(traceback.format_exc())
            # Don't store the failed connection in g
            if 'mongo_client' in g:
                del g['mongo_client']
            if 'db' in g:
                del g['db']
            return None
    
    return g.db

def close_db(e=None):
    """Close database connection if it exists"""
    mongo_client = g.pop('mongo_client', None)
    
    if mongo_client is not None:
        try:
            mongo_client.close()
            logger.info("Closed MongoDB connection")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")

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
        # Create honeypot_interactions collection with indexes
        if "honeypot_interactions" not in db.list_collection_names():
            try:
                db.create_collection("honeypot_interactions")
                logger.info("Created honeypot_interactions collection")
            except Exception as e:
                logger.error(f"Error creating honeypot_interactions collection: {e}")
        
        # Define collections and their indexes
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
        
        # Create indexes with error handling for each collection
        for collection_name, indexes in collections_and_indexes.items():
            try:
                # Create collection if it doesn't exist
                if collection_name not in db.list_collection_names():
                    try:
                        db.create_collection(collection_name)
                        logger.info(f"Created collection: {collection_name}")
                    except Exception as e:
                        logger.error(f"Error creating collection {collection_name}: {e}")
                        continue  # Skip to next collection if we can't create this one
                
                # Create indexes for this collection
                collection = db[collection_name]
                for index in indexes:
                    try:
                        if isinstance(index, dict):
                            # Index with options
                            key = index.pop("key")
                            collection.create_index(key, **index)
                            logger.info(f"Created index on {collection_name}.{key} with options")
                        elif isinstance(index, list):
                            # Compound index
                            collection.create_index(index)
                            logger.info(f"Created compound index on {collection_name}")
                        else:
                            # Simple index
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
    # Register connection cleanup function
    app.teardown_appcontext(close_db)
    
    # Initialize app.extensions dictionary if it doesn't exist
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    
    # Set up MongoDB in app context
    with app.app_context():
        try:
            db = get_db()
            if db:
                app.extensions['mongodb'] = {'db': db}
                
                # Initialize collections with the established connection
                initialize_collections(db)
                logger.info("MongoDB initialization complete")
            else:
                app.extensions['mongodb'] = {'db': None}
                logger.warning("MongoDB connection failed during initialization")
        except Exception as e:
            app.extensions['mongodb'] = {'db': None}
            logger.error(f"Exception during MongoDB initialization: {e}")
            logger.error(traceback.format_exc())

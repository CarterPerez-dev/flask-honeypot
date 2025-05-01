from pymongo import MongoClient
import os
from flask import g, current_app
import logging

logger = logging.getLogger(__name__)

def get_db():
    """
    Get MongoDB database connection
    
    Returns:
        pymongo.database.Database: MongoDB database object
    """
    if 'db' not in g:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/honeypot')
        
        try:
            # Create client and connect to database
            client = MongoClient(mongo_uri)
            db_name = mongo_uri.split('/')[-1]
            g.db = client[db_name]
            g.mongo_client = client
            
            # Test connection
            client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {mongo_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    return g.db

def close_db(e=None):
    """Close database connection if it exists"""
    mongo_client = g.pop('mongo_client', None)
    
    if mongo_client is not None:
        mongo_client.close()
        logger.info("Closed MongoDB connection")

def initialize_collections(db):
    """
    Initialize MongoDB collections with proper indexes
    
    Args:
        db: MongoDB database instance
    """
    # Create honeypot_interactions collection with indexes
    if "honeypot_interactions" not in db.list_collection_names():
        db.create_collection("honeypot_interactions")
    db.honeypot_interactions.create_index("timestamp")
    db.honeypot_interactions.create_index("ip_address")
    db.honeypot_interactions.create_index("page_type")
    db.honeypot_interactions.create_index("interaction_type")
    
    # Create scanAttempts collection with indexes
    if "scanAttempts" not in db.list_collection_names():
        db.create_collection("scanAttempts")
    db.scanAttempts.create_index("timestamp")
    db.scanAttempts.create_index("clientId")
    db.scanAttempts.create_index("ip")
    db.scanAttempts.create_index([("ip", 1), ("timestamp", -1)])
    
    # Create watchList collection with indexes
    if "watchList" not in db.list_collection_names():
        db.create_collection("watchList")
    db.watchList.create_index("clientId", unique=True)
    db.watchList.create_index("ip")
    db.watchList.create_index("severity")
    
    # Create securityBlocklist collection with indexes
    if "securityBlocklist" not in db.list_collection_names():
        db.create_collection("securityBlocklist")
    db.securityBlocklist.create_index("clientId")
    db.securityBlocklist.create_index("ip")
    db.securityBlocklist.create_index("blockUntil")
    
    # Create admin_login_attempts collection with indexes
    if "admin_login_attempts" not in db.list_collection_names():
        db.create_collection("admin_login_attempts")
    db.admin_login_attempts.create_index("ip")
    db.admin_login_attempts.create_index("lastAttempt")



def init_app(app):
    """
    Initialize MongoDB with Flask application
    
    Args:
        app (Flask): Flask application
    """
    app.teardown_appcontext(close_db)

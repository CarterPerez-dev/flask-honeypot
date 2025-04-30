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

def init_app(app):
    """
    Initialize MongoDB with Flask application
    
    Args:
        app (Flask): Flask application
    """
    app.teardown_appcontext(close_db)

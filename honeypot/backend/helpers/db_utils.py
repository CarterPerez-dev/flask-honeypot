import functools
import logging
from honeypot.database.mongodb import get_db

logger = logging.getLogger(__name__)

def with_db_recovery(f):
    """
    Decorator to handle MongoDB connection recovery
    
    Usage:
        @with_db_recovery
        def some_function():
            db = get_db()
            return db.collection.find()
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if "MongoClient" in str(e) and "close" in str(e):
                logger.warning(f"MongoDB connection issue, attempting recovery: {str(e)}")
                try:
                    return f(*args, **kwargs)
                except Exception as recover_e:
                    logger.error(f"MongoDB recovery failed: {str(recover_e)}")
                    raise recover_e
            else:
                raise e
    
    return wrapper

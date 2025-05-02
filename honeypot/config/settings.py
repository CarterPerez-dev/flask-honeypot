# honeypot/config/settings.py
import os
from dotenv import load_dotenv
import secrets


load_dotenv()


def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_hex(32)  


class Config:
    """Base configuration for honeypot package"""
    # Core settings
    DEBUG = False
    TESTING = False
    
    # Redis settings for sessions
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # MongoDB settings
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/honeypot')
    
    # GeoIP settings
    GEOIP_DB_DIRECTORY = os.environ.get('GEOIP_DB_DIRECTORY', None)  
    MAXMIND_LICENSE_KEY = os.environ.get('MAXMIND_LICENSE_KEY', '')
    GEOIP_AUTO_UPDATE = os.environ.get('GEOIP_AUTO_UPDATE', 'true').lower() == 'true'
    
    # Proxy cache settings
    PROXY_CACHE_DIRECTORY = os.environ.get('PROXY_CACHE_DIRECTORY', None) 
    PROXY_CACHE_UPDATE_INTERVAL = int(os.environ.get('PROXY_CACHE_UPDATE_INTERVAL', 24))  
    
    # Honeypot settings
    HONEYPOT_RATE_LIMIT = int(os.environ.get('HONEYPOT_RATE_LIMIT', 15))
    HONEYPOT_RATE_PERIOD = int(os.environ.get('HONEYPOT_RATE_PERIOD', 60))
    HONEYPOT_TEMPLATES_PATH = os.environ.get('HONEYPOT_TEMPLATES_PATH', None)
    
    # Data directory (used for cache, databases, etc.)
    @property
    def DATA_DIRECTORY(self):
        data_dir = os.environ.get('HONEYPOT_DATA_DIRECTORY')
        if not data_dir:
            # Create a default data directory in the package
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
        return data_dir
    
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', None)
  
    @property
    def SECRET_KEY(self):
        """Get secret key from environment or generate a secure one"""
        key = os.environ.get('SECRET_KEY')
        if not key:
            key = generate_secret_key()
            import logging
            logging.warning(
                "No SECRET_KEY environment variable found. Using a generated key. "
                "This is fine for development but will cause sessions to invalidate "
                "when the application restarts. Set a persistent SECRET_KEY in production."
            )
        return key  

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    

class ProductionConfig(Config):
    """Production configuration"""
    def __init__(self):
        if not self.SECRET_KEY or self.SECRET_KEY == 'dev_secure_key_change_me':
            import warnings
            warnings.warn("SECRET_KEY not set or using default value in production!")
    

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/honeypot_test'
    REDIS_DB = 1  


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """
    Return configuration class based on environment
    
    Args:
        config_name (str, optional): Configuration name to load
        
    Returns:
        object: Configuration object
    """
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])()

# honeypot/config/settings.py
import os
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()

class Config:
    """Base configuration for honeypot package"""
    # Core settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secure_key_change_me')
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
    GEOIP_DB_DIRECTORY = os.environ.get('GEOIP_DB_DIRECTORY', None)  # Will default to package dir if None
    MAXMIND_LICENSE_KEY = os.environ.get('MAXMIND_LICENSE_KEY', '')
    GEOIP_AUTO_UPDATE = os.environ.get('GEOIP_AUTO_UPDATE', 'true').lower() == 'true'
    
    # Proxy cache settings
    PROXY_CACHE_DIRECTORY = os.environ.get('PROXY_CACHE_DIRECTORY', None)  # Will default to package dir if None
    PROXY_CACHE_UPDATE_INTERVAL = int(os.environ.get('PROXY_CACHE_UPDATE_INTERVAL', 24))  # hours
    
    # Honeypot settings
    HONEYPOT_RATE_LIMIT = int(os.environ.get('HONEYPOT_RATE_LIMIT', 5))
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
    
    # Admin dashboard settings
    ADMIN_URL_PREFIX = os.environ.get('ADMIN_URL_PREFIX', '/honey') # Using a generic url path for admin pages are easily foudn with dirbuster/ hidden path scanning tools
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', None)  # Should be bcrypt hash
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', None)
    

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    

class ProductionConfig(Config):
    """Production configuration"""
    # Ensure these settings are properly set in production
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

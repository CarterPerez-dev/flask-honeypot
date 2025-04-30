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
    GEOIP_DB_DIRECTORY = os.environ.get('GEOIP_DB_DIRECTORY', './geoip_db')
    MAXMIND_LICENSE_KEY = os.environ.get('MAXMIND_LICENSE_KEY', '')
    
    # Honeypot settings
    HONEYPOT_RATE_LIMIT = int(os.environ.get('HONEYPOT_RATE_LIMIT', 5))
    HONEYPOT_RATE_PERIOD = int(os.environ.get('HONEYPOT_RATE_PERIOD', 99))
    HONEYPOT_TEMPLATES_PATH = os.environ.get('HONEYPOT_TEMPLATES_PATH', None)
       
    # Admin dashboard settings
    ADMIN_URL_PREFIX = os.environ.get('ADMIN_URL_PREFIX', '/admin')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', None)  # Should be bcrypt hash
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    LOG_FILE = os.environ.get('LOG_FILE', None)
    

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    

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

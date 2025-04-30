from flask import Flask
from flask_cors import CORS
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import redis
from honeypot import create_honeypot_app
from honeypot.config.settings import get_config

def create_app(config=None):
    """
    Create and configure the Flask application for honeypot functionality
    
    Args:
        config (dict, optional): Configuration dictionary to override defaults
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__, 
                template_folder='templates')
    
    # Apply default configuration
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_secure_key_change_me'),
        SESSION_TYPE='redis',
        SESSION_PERMANENT=True,
        SESSION_USE_SIGNER=True,
        SESSION_KEY_PREFIX='honeypot_session:',
        SESSION_REDIS=redis.StrictRedis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=0,
            password=os.environ.get('REDIS_PASSWORD', None)
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        JSON_SORT_KEYS=False,
        PROPAGATE_EXCEPTIONS=True,
        PRESERVE_CONTEXT_ON_EXCEPTION=False
    )
    
    # Apply custom configuration if provided
    if config:
        app.config.update(config)
    
    # Setup CORS
    CORS(app, supports_credentials=True)
    
    # Initialize extensions
    Session(app)
    
    # Fix proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    
    # Register blueprints
    from honeypot.backend.routes.honeypot import honeypot_bp
    from honeypot.backend.routes.honeypot_pages import honeypot_pages_bp

    
    app.register_blueprint(honeypot_bp, url_prefix='/honeypot')
    app.register_blueprint(honeypot_pages_bp)

    
    # Add context processor for CSRF token
    from honeypot.backend.middleware.csrf_protection import generate_csrf_token
    
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf_token()}
    
    # Basic health check endpoint
    @app.route('/health')
    def health_check():
        return 'Honeypot is running'
    
    return app

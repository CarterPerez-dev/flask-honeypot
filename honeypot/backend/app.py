# honeypot/backend/app.py
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import redis
from honeypot.config.settings import get_config
from honeypot.database.mongodb import init_app as init_db

def create_app(config=None):
    """
    Create and configure the Flask application for honeypot functionality
    
    Args:
        config (dict, optional): Configuration dictionary to override defaults
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Get configuration
    app_config = get_config()
    
    # Apply default configuration
    app.config.update(
        SECRET_KEY=app_config.SECRET_KEY,
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
        SESSION_COOKIE_SECURE=not app_config.DEBUG,
        JSON_SORT_KEYS=False,
        PROPAGATE_EXCEPTIONS=True,
        PRESERVE_CONTEXT_ON_EXCEPTION=False,
        HONEYPOT_RATE_LIMIT=app_config.HONEYPOT_RATE_LIMIT,
        HONEYPOT_RATE_PERIOD=app_config.HONEYPOT_RATE_PERIOD
    )
    
    # Apply custom configuration if provided
    if config:
        app.config.update(config)
    

    CORS(app, supports_credentials=True)
    

    Session(app)
    init_db(app)
    

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    
    # Register blueprints
    from honeypot.backend.routes.honeypot import honeypot_bp
    from honeypot.backend.routes.honeypot_pages import honeypot_pages_bp
    from honeypot.backend.routes.honeypot_routes import register_routes_with_blueprint
    
    app.register_blueprint(honeypot_bp, url_prefix='/honeypot')
    app.register_blueprint(honeypot_pages_bp)
    

    register_routes_with_blueprint(
        blueprint=honeypot_pages_bp,
        handler_function=honeypot_bp.view_functions['honeypot_handler']
    )
    
    # Context processor for CSRF token
    from honeypot.backend.middleware.csrf_protection import generate_csrf_token
    
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf_token()}
    
    # Basic health check endpoint
    @app.route('/health')
    def health_check():
        return 'Honeypot is running'
    
    return app

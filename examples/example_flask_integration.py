"""
example_flask_integration.py - Example of integrating Honeypot Framework with an existing Flask app
"""
from flask import Flask, render_template, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound
from honeypot import create_honeypot_app
import os

# Create your main application
main_app = Flask(__name__)

# Configure your main application
main_app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'your-main-app-secret-key'),
    DEBUG=os.environ.get('DEBUG', 'False') == 'True'
)

# Regular routes for your main application
@main_app.route('/')
def index():
    return render_template('index.html', title="My Secure Application")

@main_app.route('/api/data')
def get_data():
    return jsonify({"message": "This is legitimate data from your main application"})

# Create the honeypot application
honeypot_config = {
    "SECRET_KEY": os.environ.get('HONEYPOT_SECRET_KEY', os.environ.get('SECRET_KEY')),
    "MONGO_URI": os.environ.get('MONGO_URI', 'mongodb://localhost:27017/honeypot'),
    "REDIS_HOST": os.environ.get('REDIS_HOST', 'localhost'),
    "REDIS_PORT": int(os.environ.get('REDIS_PORT', 6379)),
    "REDIS_PASSWORD": os.environ.get('REDIS_PASSWORD', None),
    "HONEYPOT_ADMIN_PASSWORD": os.environ.get('HONEYPOT_ADMIN_PASSWORD', 'change-me-in-production')
}

honeypot_app = create_honeypot_app(honeypot_config)

# Option 1: Mount the honeypot at a specific URL prefix using DispatcherMiddleware
application = DispatcherMiddleware(main_app, {
    '/security': honeypot_app,  # Map the honeypot app to /security/* URLs
})

# Option 2: If you want to selectively include specific honeypot routes in your main app
# instead of using DispatcherMiddleware, you can register blueprints:
#
# from honeypot.backend.routes.honeypot_pages import honeypot_pages_bp
# from honeypot.backend.routes.honeypot import honeypot_bp
# 
# # Register only the honeypot routes you want
# main_app.register_blueprint(honeypot_pages_bp, url_prefix='/honeypot')
# main_app.register_blueprint(honeypot_bp, url_prefix='/api/honeypot')

# If you're using gunicorn, use the application object:
# $ gunicorn 'example_flask_integration:application'

# For direct Flask execution, we need a proper app object:
if __name__ == "__main__":
    # For development, we can create a simple WSGI app that wraps the DispatcherMiddleware
    class ProxyApp:
        def __init__(self, app):
            self.app = app
            
        def __call__(self, environ, start_response):
            return self.app(environ, start_response)
    
    # Create a proxy WSGI app we can run with Flask's CLI
    proxy_app = ProxyApp(application)
    
    # To access flask cli commands
    proxy_app.debug = main_app.debug
    proxy_app.name = main_app.name
    proxy_app.config = main_app.config
    
    # Additional setup for Blueprints (if using Option 2)
    # proxy_app.blueprints = main_app.blueprints
    
    # Run the integrated application
    proxy_app.run(host='0.0.0.0', port=5000, debug=True)

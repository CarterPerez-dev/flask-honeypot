# examples/with_existing_app.py
from flask import Flask
from honeypot import create_honeypot_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Create your main application
main_app = Flask(__name__)

@main_app.route('/')
def home():
    return 'Main application home page'

# Create the honeypot app
honeypot_app = create_honeypot_app()

# Combine the applications
application = DispatcherMiddleware(main_app, {
    '/security': honeypot_app
})

if __name__ == "__main__":
    run_simple('localhost', 5000, application, use_reloader=True)

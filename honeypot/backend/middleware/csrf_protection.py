# honeypot/backend/middleware/csrf_protection.py
import secrets
from flask import request, session, jsonify, abort
from functools import wraps

def generate_csrf_token():
    """Generate a secure CSRF token and store it in the session"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def csrf_protect(): 
    """
    CSRF protection middleware. Checks unsafe methods.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.headers.get('X-CSRF-TOKEN')
                session_token = session.get('csrf_token')
                if not token or not session_token or token != session_token:
                    print(f"CSRF Failure: Path={request.path} Header={token} Session={session_token}")
                    return jsonify({"error": "CSRF token validation failed"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# honeypot/backend/middleware/csrf_protection.py
import secrets
from flask import request, session, jsonify, abort, current_app
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def generate_csrf_token():
    """Generate a secure CSRF token and store it in the session"""
    if 'csrf_token' not in session:
        token = secrets.token_hex(32)
        session['csrf_token'] = token
        # Force session save
        session.modified = True
        logger.debug(f"Generated new CSRF token: {token[:5]}...")
    return session['csrf_token']

def csrf_protect(): 
    """CSRF protection middleware with improved session handling"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # For /login endpoint, make session handling more lenient
            if request.path.endswith('/login'):
                # For login requests, if we have a token header but no session token,
                # accept it and set the session token to match the header
                token = request.headers.get('X-CSRF-TOKEN')
                if token and request.method == 'POST':
                    session['csrf_token'] = token
                    session.modified = True
                    logger.debug(f"Accepting header token for login: {token[:5]}...")
                    return f(*args, **kwargs)
            
            # Normal CSRF validation for other endpoints
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.headers.get('X-CSRF-TOKEN')
                session_token = session.get('csrf_token')
                
                logger.debug(f"CSRF Check - Path: {request.path}")
                logger.debug(f"Header token: {token[:5]}... if token else 'None'")
                logger.debug(f"Session token: {session_token[:5]}... if session_token else 'None'")
                
                if not token or not session_token or token != session_token:
                    logger.warning(f"CSRF Failure: Path={request.path} Header={token} Session={session_token}")
                    return jsonify({"error": "CSRF token validation failed"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

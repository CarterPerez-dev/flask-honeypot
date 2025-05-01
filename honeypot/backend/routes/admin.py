# honeypot/backend/routes/admin.py
import os
import secrets
import time
import math
from datetime import datetime, timedelta
from flask import Blueprint, request, session, jsonify, current_app
from honeypot.backend.middleware.csrf_protection import generate_csrf_token, csrf_protect
from functools import wraps

from dotenv import load_dotenv

load_dotenv()

# Create blueprint
angela_bp = Blueprint('angela', __name__)

# Get admin password from environment variable
ADMIN_PASS = os.environ.get('HONEYPOT_ADMIN_PASSWORD', 'admin_key')

# MongoDB connection helper
def get_db():
    return current_app.extensions.get('mongodb', {}).get('db')

@angela_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """Generate and return a CSRF token"""
    token = generate_csrf_token()
    # Force content type to be JSON and ensure no caching
    response = jsonify({"csrf_token": token})
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@angela_bp.route('/login', methods=['POST'])
def admin_login():
    """Handle admin login authentication with explicit session management"""
    data = request.json or {}
    raw_admin_key = data.get('adminKey', '')
    
    # Get client identifier for rate limiting
    client_ip = request.remote_addr
    
    # Get database connection
    db = get_db()
    
    # Debug session state - convert to dict for logging
    session_dict = {key: session.get(key) for key in list(session.keys())}
    current_app.logger.info(f"Session before login: {session_dict}")
    
    # Sanitize inputs - simple sanitization
    sanitized_key = raw_admin_key.strip() if raw_admin_key else ""
    
    # Get CSRF token from header
    csrf_token = request.headers.get('X-CSRF-TOKEN')
    if csrf_token:
        session['csrf_token'] = csrf_token
        session.modified = True
    
    # Check if credentials are valid
    if sanitized_key and sanitized_key == ADMIN_PASS:
        # Set session values
        session['honeypot_admin_logged_in'] = True
        session['admin_last_active'] = datetime.utcnow().isoformat()
        session['admin_ip'] = client_ip
        
        # Force session save
        session.modified = True
        
        # Log successful login for debugging
        current_app.logger.info(f"Login successful for IP: {client_ip}")
        current_app.logger.info(f"Session after login: {dict(session)}")
        
        # Log to database if available
        if db:
            db.admin_login_attempts.delete_many({"ip": client_ip})
            db.auditLogs.insert_one({
                "timestamp": datetime.utcnow(),
                "ip": client_ip,
                "success": True,
                "adminLogin": True
            })
        
        return jsonify({
            "message": "Authorization successful",
            "session_id": request.cookies.get('session', 'unknown')
        }), 200
    else:
        # Handle failed login
        if db:
            failed_attempts = db.admin_login_attempts.find_one({"ip": client_ip})
            
            if failed_attempts:
                attempts = failed_attempts.get("attempts", 0) + 1
                
                if attempts >= 5:
                    block_minutes = min(1440, 5 * (2 ** (attempts - 5)))
                    block_until = datetime.utcnow() + timedelta(minutes=block_minutes)
                    
                    db.admin_login_attempts.update_one(
                        {"_id": failed_attempts["_id"]},
                        {"$set": {
                            "attempts": attempts,
                            "lastAttempt": datetime.utcnow(),
                            "blockUntil": block_until
                        }}
                    )
                    
                    db.auditLogs.insert_one({
                        "timestamp": datetime.utcnow(),
                        "ip": client_ip,
                        "success": False,
                        "reason": "Blocked due to too many attempts",
                        "adminLogin": True
                    })
                    
                    return jsonify({
                        "error": f"Too many failed login attempts. Try again in {block_minutes} minutes."
                    }), 429
                else:
                    db.admin_login_attempts.update_one(
                        {"_id": failed_attempts["_id"]},
                        {"$set": {
                            "attempts": attempts,
                            "lastAttempt": datetime.utcnow()
                        }}
                    )
            else:
                db.admin_login_attempts.insert_one({
                    "ip": client_ip,
                    "attempts": 1,
                    "lastAttempt": datetime.utcnow()
                })
            
            db.auditLogs.insert_one({
                "timestamp": datetime.utcnow(),
                "ip": client_ip,
                "success": False,
                "reason": "Invalid admin credentials",
                "adminLogin": True
            })
        
        return jsonify({"error": "Invalid admin credentials"}), 403

@angela_bp.route('/honey/angela', methods=['GET'])
def check_auth_status():
    """
    Checks if the current session belongs to a logged-in and active admin.
    Accessible via GET request.
    """
    # Log session contents for debugging
    session_dict = {key: session.get(key) for key in list(session.keys())}
    current_app.logger.info(f"Auth check - Session: {session_dict}")
    current_app.logger.info(f"Auth check - Cookies: {request.cookies}")

    is_authenticated = session.get('honeypot_admin_logged_in', False)
    
    if is_authenticated:
        # Update last active time
        session['admin_last_active'] = datetime.utcnow().isoformat()
        session.modified = True
        
        return jsonify({
            "isAuthenticated": True
         }), 200
    else:
        return jsonify({
            "isAuthenticated": False,
            "message": "Not authenticated or session expired"
        }), 401

@angela_bp.route('/logout', methods=['POST'])
def admin_logout():
    """Handle admin logout"""
    session.pop('honeypot_admin_logged_in', None)
    session.pop('admin_last_active', None)
    session.pop('admin_ip', None)
    
    return jsonify({"message": "Logged out successfully"}), 200

def require_admin():
    """
    Middleware to check if user is authenticated as admin
    
    Returns:
        bool: True if properly authenticated
    """
    is_authenticated = session.get('honeypot_admin_logged_in', False)
    
    if not is_authenticated:
        return False
    
    # Check last activity time
    last_active = session.get('admin_last_active')
    if last_active:
        try:
            last_active_time = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
            inactivity_limit = timedelta(hours=1) # Edit this number if you want to stay logged in longer or shorter
            
            if (datetime.utcnow() - last_active_time) > inactivity_limit:
                session.pop('honeypot_admin_logged_in', None)
                return False
        except:
            session.pop('honeypot_admin_logged_in', None)
            return False
    
    # Update last active time
    session['admin_last_active'] = datetime.utcnow().isoformat()
    
    return True

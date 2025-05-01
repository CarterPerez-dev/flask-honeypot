# honeypot/backend/routes/admin.py
import os
import secrets
import time
import math
from datetime import datetime, timedelta
from flask import Blueprint, request, session, jsonify, current_app
from honeypot.backend.helpers.unhackable import sanitize_admin_key, sanitize_role
from honeypot.backend.middleware.csrf_protection import generate_csrf_token

from dotenv import load_dotenv

load_dotenv()

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/honeypot/admin')

# Get admin password from environment variable
ADMIN_PASS = os.environ.get('HONEYPOT_ADMIN_PASSWORD', 'admin_key')

# MongoDB connection helper
def get_db():
    return current_app.extensions.get('mongodb', {}).get('db')

@admin_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """Generate and return a CSRF token"""
    token = generate_csrf_token()
    return jsonify({"csrf_token": token})

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Handle admin login authentication"""
    data = request.json or {}
    raw_admin_key = data.get('adminKey', '')
    
    # Get client identifier for rate limiting
    client_ip = request.remote_addr
    
    # Get database connection
    db = get_db()
    
    # Check if this IP is currently blocked for login attempts
    now = datetime.utcnow()
    ip_block = None
    
    if db:
        ip_block = db.admin_login_attempts.find_one({
            "ip": client_ip,
            "blockUntil": {"$gt": now}
        })
    
    if ip_block:
        # Calculate time remaining in the block
        block_time = ip_block["blockUntil"] - now
        minutes_remaining = math.ceil(block_time.total_seconds() / 60)
        
        # Log the blocked attempt if db is available
        if db:
            db.auditLogs.insert_one({
                "timestamp": now,
                "ip": client_ip,
                "success": False,
                "reason": "IP blocked",
                "adminLogin": True
            })
        
        return jsonify({
            "error": f"Too many failed login attempts. Try again in {minutes_remaining} minutes."
        }), 429
    
    # Get sanitized inputs
    sanitized_key, key_valid, key_errors = sanitize_admin_key(raw_admin_key)
    
    # Create validation context
    validation_context = {
        "validation_time": time.time(),
        "key_errors": key_errors,
        "ip_address": client_ip,
        "request_id": secrets.token_hex(8),
        "total_error_count": len(key_errors)
    }
    
    # Check admin password
    if sanitized_key and sanitized_key == ADMIN_PASS:
        # Successful login, clear any failed attempts if db is available
        if db:
            db.admin_login_attempts.delete_many({"ip": client_ip})
            
            # Log successful login
            db.auditLogs.insert_one({
                "timestamp": now,
                "ip": client_ip,
                "success": True,
                "adminLogin": True
            })
        
        # Set session
        session['honeypot_admin_logged_in'] = True
        session['admin_last_active'] = now.isoformat()
        session['admin_ip'] = client_ip
        
        return jsonify({"message": "Authorization successful"}), 200
    else:
        # Failed login attempt
        if db:
            # Get previous failed attempts
            failed_attempts = db.admin_login_attempts.find_one({"ip": client_ip})
            
            if failed_attempts:
                # Increment attempts
                attempts = failed_attempts.get("attempts", 0) + 1
                
                # Check if we should block now
                if attempts >= 5:
                    # Block for progressively longer times based on number of attempts
                    block_minutes = min(1440, 5 * (2 ** (attempts - 5)))  # Exponential backoff, cap at 1 day
                    block_until = now + timedelta(minutes=block_minutes)
                    
                    db.admin_login_attempts.update_one(
                        {"_id": failed_attempts["_id"]},
                        {"$set": {
                            "attempts": attempts,
                            "lastAttempt": now,
                            "blockUntil": block_until,
                            "validation_errors": validation_context.get("key_errors", [])
                        }}
                    )
                    
                    # Log the blocked attempt
                    db.auditLogs.insert_one({
                        "timestamp": now,
                        "ip": client_ip,
                        "success": False,
                        "reason": "Blocked due to too many attempts",
                        "adminLogin": True,
                        "validation_context": validation_context
                    })
                    
                    return jsonify({
                        "error": f"Too many failed login attempts. Try again in {block_minutes} minutes."
                    }), 429
                else:
                    # Update attempts
                    db.admin_login_attempts.update_one(
                        {"_id": failed_attempts["_id"]},
                        {"$set": {
                            "attempts": attempts,
                            "lastAttempt": now,
                            "validation_errors": validation_context.get("key_errors", [])
                        }}
                    )
            else:
                # First failed attempt
                db.admin_login_attempts.insert_one({
                    "ip": client_ip,
                    "attempts": 1,
                    "lastAttempt": now,
                    "validation_errors": validation_context.get("key_errors", [])
                })
            
            # Log the failed attempt
            db.auditLogs.insert_one({
                "timestamp": now,
                "ip": client_ip,
                "success": False,
                "reason": "Invalid admin password",
                "adminLogin": True,
                "validation_context": validation_context
            })
        
        # Don't leak info about the validation errors to client
        return jsonify({"error": "Invalid admin password"}), 403

@admin_bp.route('/logout', methods=['POST'])
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
    
    # Check for session expiration
    last_active = session.get('admin_last_active')
    if last_active:
        try:
            last_active_time = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
            inactivity_limit = timedelta(hours=1)
            
            if (datetime.utcnow() - last_active_time) > inactivity_limit:
                # Session expired
                session.pop('honeypot_admin_logged_in', None)
                return False
        except:
            # Error parsing time, invalidate session
            session.pop('honeypot_admin_logged_in', None)
            return False
    
    # Update last active timestamp
    session['admin_last_active'] = datetime.utcnow().isoformat()
    
    return True

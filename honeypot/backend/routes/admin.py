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
angela_bp = Blueprint('angela', __name__, url_prefix=ls'/honeypot/angela')


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
@csrf_protect() 
def admin_login():
    """Handle admin login authentication"""
    data = request.json or {}
    raw_admin_key = data.get('adminKey', '')
    raw_role = data.get('role', 'basic')  
    

    client_ip = request.remote_addr
    

    db = get_db()
    

    now = datetime.utcnow()
    ip_block = None
    
    if db:
        ip_block = db.admin_login_attempts.find_one({
            "ip": client_ip,
            "blockUntil": {"$gt": now}
        })
    
    if ip_block:
        block_time = ip_block["blockUntil"] - now
        minutes_remaining = math.ceil(block_time.total_seconds() / 60)
        
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
     

    validation_context = {
        "validation_time": time.time(),
        "key_errors": key_errors,
        "role_errors": role_errors,
        "ip_address": client_ip,
        "request_id": secrets.token_hex(8),
        "total_error_count": len(key_errors) + len(role_errors)
    }
    

    if sanitized_key and key_valid and sanitized_key == ADMIN_PASS:
        if db:
            db.admin_login_attempts.delete_many({"ip": client_ip})
            
            db.auditLogs.insert_one({
                "timestamp": now,
                "ip": client_ip,
                "success": True,
                "adminLogin": True,
                "role": sanitized_role
            })
        

        session['honeypot_admin_logged_in'] = True
        session['admin_last_active'] = now.isoformat()
        session['admin_ip'] = client_ip
        session['admin_role'] = sanitized_role
        
        return jsonify({"message": "Authorization successful", "role": sanitized_role}), 200
    else:

        if db:
            failed_attempts = db.admin_login_attempts.find_one({"ip": client_ip})
            
            if failed_attempts:
                attempts = failed_attempts.get("attempts", 0) + 1
                
                if attempts >= 5:
                    block_minutes = min(1440, 5 * (2 ** (attempts - 5))) 
                    block_until = now + timedelta(minutes=block_minutes)
                    
                    db.admin_login_attempts.update_one(
                        {"_id": failed_attempts["_id"]},
                        {"$set": {
                            "attempts": attempts,
                            "lastAttempt": now,
                            "blockUntil": block_until,
                            "validation_errors": validation_context.get("key_errors", []) + validation_context.get("role_errors", [])
                        }}
                    )
                    
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
                    db.admin_login_attempts.update_one(
                        {"_id": failed_attempts["_id"]},
                        {"$set": {
                            "attempts": attempts,
                            "lastAttempt": now,
                            "validation_errors": validation_context.get("key_errors", []) + validation_context.get("role_errors", [])
                        }}
                    )
            else:
                db.admin_login_attempts.insert_one({
                    "ip": client_ip,
                    "attempts": 1,
                    "lastAttempt": now,
                    "validation_errors": validation_context.get("key_errors", []) + validation_context.get("role_errors", [])
                })
            
            db.auditLogs.insert_one({
                "timestamp": now,
                "ip": client_ip,
                "success": False,
                "reason": "Invalid admin credentials",
                "adminLogin": True,
                "validation_context": validation_context
            })
        
        return jsonify({"error": "Invalid admin credentials"}), 403


@admin_bp.route('/honey/angela', methods=['GET'])
@csrf_protect() 
def check_auth_status():
    """
    Checks if the current session belongs to a logged-in and active admin.
    Accessible via GET request.
    """

    is_currently_authenticated = require_admin() 

    if is_currently_authenticated:
        user_role = session.get('admin_role', 'basic') 
        return jsonify({
            "isAuthenticated": True,
            "role": user_role
         }), 200
    else:
        return jsonify({
            "isAuthenticated": False
        }), 401

@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    """Handle admin logout"""
    session.pop('honeypot_admin_logged_in', None)
    session.pop('admin_last_active', None)
    session.pop('admin_ip', None)
    session.pop('admin_role', None)
    
    return jsonify({"message": "Logged out successfully"}), 200

def require_admin(minimum_role='basic'):
    """
    Middleware to check if user is authenticated as admin
    
    Args:
        minimum_role (str): Minimum required role
        
    Returns:
        bool: True if properly authenticated
    """
    is_authenticated = session.get('honeypot_admin_logged_in', False)
    
    if not is_authenticated:
        return False
    

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
    
    user_role = session.get('admin_role', 'basic')
    role_hierarchy = {
        'basic': 0,
        'supervisor': 1,
        'superadmin': 2
    }
    
    required_level = role_hierarchy.get(minimum_role, 0)
    user_level = role_hierarchy.get(user_role, 0)
    
    if user_level < required_level:
        return False
    

    session['admin_last_active'] = datetime.utcnow().isoformat()
    
    return True

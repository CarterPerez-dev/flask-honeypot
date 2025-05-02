# honeypot/backend/routes/admin.py
import os
import secrets
import time
import math
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, session, jsonify, current_app, make_response
from honeypot.backend.middleware.csrf_protection import generate_csrf_token, csrf_protect
from functools import wraps
import logging
import traceback
from honeypot.database.mongodb import get_db
from honeypot.backend.helpers.db_utils import with_db_recovery
from honeypot.backend.helpers.unhackable import (
    sanitize_admin_key, 
    validate_admin_credentials, 
    constant_time_compare
)


from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)

# Create blueprint, random to ensure no interference with honeypot routes
angela_bp = Blueprint('angela', __name__)


ADMIN_PASS = os.environ.get('HONEYPOT_ADMIN_PASSWORD')

@angela_bp.route('/login', methods=['POST'])
@with_db_recovery
def admin_login():
    """Handle admin login authentication with explicit session management"""
    try:
        data = request.json or {}
        raw_admin_key = data.get('adminKey', '')


        client_ip = request.remote_addr


        db = get_db()


        session_dict = {key: session.get(key) for key in list(session.keys())}
        current_app.logger.info(f"Session before login: {session_dict}")


        sanitized_key, is_valid, validation_errors = sanitize_admin_key(raw_admin_key)
        
        if validation_errors:
            current_app.logger.warning(f"Admin key validation errors: {validation_errors}")
        

        csrf_token = request.headers.get('X-CSRF-TOKEN')
        if csrf_token:
            session['csrf_token'] = csrf_token
            session.modified = True


        if sanitized_key and constant_time_compare(sanitized_key, ADMIN_PASS):
            session['honeypot_admin_logged_in'] = True
            session['admin_last_active'] = datetime.utcnow().isoformat()
            session['admin_ip'] = client_ip

            session.modified = True


            current_app.logger.info(f"Login successful for IP: {client_ip}")
            current_app.logger.info(f"Session after login: {dict(session)}")


            if db is not None:
                try:
                    db.admin_login_attempts.delete_many({"ip": client_ip})
                    db.auditLogs.insert_one({
                        "timestamp": datetime.utcnow(),
                        "ip": client_ip,
                        "success": True,
                        "adminLogin": True
                    })
                except Exception as e:
                    logger.error(f"Error writing to database during login: {e}")

            return jsonify({
                "message": "Authorization successful",
                "session_id": request.cookies.get('session', 'unknown')
            }), 200
        else:
            if db is not None:
                try:
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


                    audit_entry = {
                        "timestamp": datetime.utcnow(),
                        "ip": client_ip,
                        "success": False,
                        "reason": "Invalid admin credentials",
                        "adminLogin": True
                    }
                    

                    if validation_errors:
                        audit_entry["validation_errors"] = validation_errors
                        
                    db.auditLogs.insert_one(audit_entry)
                except Exception as e:
                    logger.error(f"Error updating failed login attempts: {e}")
            else: 
                logger.warning(f"DB connection unavailable, cannot log failed login attempt for IP: {client_ip}")

            return jsonify({"error": "Invalid admin credentials"}), 403
    except Exception as e:
        logger.error(f"Error during login: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Login process failed due to server error"}), 500

@angela_bp.route('/honey/angela', methods=['GET'])
def check_auth_status():
    """
    Checks if the current session belongs to a logged-in and active admin.
    Accessible via GET request.
    """
    try:
        session_dict = {key: session.get(key) for key in list(session.keys())}
        current_app.logger.info(f"Auth check - Session: {session_dict}")
        current_app.logger.info(f"Auth check - Cookies: {request.cookies}")

        is_authenticated = session.get('honeypot_admin_logged_in', False)

        if is_authenticated:
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
    except Exception as e:
        logger.error(f"Error checking authentication status: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "isAuthenticated": False,
            "message": "Error checking authentication status"
        }), 500

@angela_bp.route('/logout', methods=['POST'])
def admin_logout():
    """Handle admin logout"""
    try:
        session.pop('honeypot_admin_logged_in', None)
        session.pop('admin_last_active', None)
        session.pop('admin_ip', None)
        session.pop('csrf_token', None)
        session.modified = True 

        return jsonify({"message": "Logged out successfully"}), 200
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({"error": "Logout process failed"}), 500

def require_admin():
    """
    Decorator function or simple check if user is authenticated as admin.
    This version is a simple check, not a decorator.
    Returns:
        bool: True if properly authenticated
    """
    try:
        is_authenticated = session.get('honeypot_admin_logged_in', False)

        if not is_authenticated:
            logger.debug("require_admin check failed: not authenticated.")
            return False


        last_active_str = session.get('admin_last_active')
        if last_active_str:
            try:
                if 'Z' in last_active_str:
                    last_active_time = datetime.fromisoformat(last_active_str.replace('Z', '+00:00'))
                elif '+' in last_active_str or '-' in last_active_str[10:]: 
                     last_active_time = datetime.fromisoformat(last_active_str)
                else: 
                     last_active_time = datetime.fromisoformat(last_active_str).replace(tzinfo=timezone.utc)


                now_utc = datetime.now(timezone.utc)
                inactivity_limit = timedelta(hours=1) # Edit this number if you want to stay logged in longer or shorter

                if (now_utc - last_active_time) > inactivity_limit:
                    logger.info(f"Admin session timed out due to inactivity. Last active: {last_active_str}")
                    session.pop('honeypot_admin_logged_in', None)
                    session.pop('admin_last_active', None)
                    session.pop('admin_ip', None)
                    session.modified = True
                    return False
            except Exception as e:
                logger.error(f"Error parsing last_active time '{last_active_str}': {e}")
                session.pop('honeypot_admin_logged_in', None)
                session.modified = True
                return False
        else:
            logger.warning("Admin session missing 'admin_last_active'. Invalidating session.")
            session.pop('honeypot_admin_logged_in', None)
            session.modified = True
            return False


        session['admin_last_active'] = datetime.now(timezone.utc).isoformat()
        session.modified = True
        logger.debug("require_admin check passed.")
        return True
    except Exception as e:
        logger.error(f"Error in require_admin check: {e}")
        return False

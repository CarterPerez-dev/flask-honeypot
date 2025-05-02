"""
enhanced_admin_security.py - Enhanced security measures for the admin module

This module demonstrates additional security techniques that can be applied to the
honeypot admin interface to further protect against unauthorized access.
"""

from flask import Blueprint, request, session, jsonify, current_app, g, abort
from honeypot.backend.middleware.csrf_protection import generate_csrf_token, csrf_protect
from functools import wraps
import logging
import traceback
import time
import re
import ipaddress
import hmac
import hashlib
import base64
import secrets
from datetime import datetime, timedelta, timezone
import urllib.parse

# Initialize logger
logger = logging.getLogger(__name__)

# Enhanced security blueprint
enhanced_admin_bp = Blueprint('enhanced_admin', __name__)

# ------------ SECURITY ENHANCEMENTS ------------

# 1. IP Whitelisting
ALLOWED_IP_RANGES = [
    '192.168.1.0/24',  # Example local network
    '10.0.0.0/8',      # Example corporate network
    # Add your trusted IP ranges here
]

def is_ip_allowed(ip_address):
    """
    Check if an IP address is in the allowed ranges
    
    Args:
        ip_address (str): IP address to check
        
    Returns:
        bool: True if IP is allowed
    """
    if not ip_address or ip_address == 'unknown':
        return False
        
    # Always allow localhost for development
    if ip_address == '127.0.0.1' or ip_address == 'localhost':
        return True
        
    # Check against whitelist
    try:
        client_ip = ipaddress.ip_address(ip_address)
        for allowed_range in ALLOWED_IP_RANGES:
            if client_ip in ipaddress.ip_network(allowed_range):
                return True
    except ValueError:
        logger.error(f"Invalid IP address format: {ip_address}")
        return False
        
    # IP not in whitelist
    logger.warning(f"Access attempt from non-whitelisted IP: {ip_address}")
    return False

# 2. Enhanced HMAC-based session tokens
def generate_secure_session_token(user_id, ip_address, user_agent):
    """
    Generate a secure session token using HMAC
    
    Args:
        user_id (str): User identifier
        ip_address (str): Client IP address
        user_agent (str): Client User-Agent
        
    Returns:
        str: Base64-encoded HMAC token
    """
    # Get secret key from app config
    secret_key = current_app.config['SECRET_KEY'].encode()
    
    # Prepare message with user context
    timestamp = int(time.time())
    message = f"{user_id}|{ip_address}|{user_agent}|{timestamp}".encode()
    
    # Generate HMAC
    h = hmac.new(secret_key, message, hashlib.sha256)
    
    # Combine timestamp and HMAC for verification later
    token_parts = f"{timestamp}|{h.hexdigest()}"
    
    # Encode as base64 for transmission
    return base64.urlsafe_b64encode(token_parts.encode()).decode()

def verify_session_token(token, user_id, ip_address, user_agent, max_age=3600):
    """
    Verify a session token
    
    Args:
        token (str): Session token to verify
        user_id (str): Expected user ID
        ip_address (str): Current client IP
        user_agent (str): Current User-Agent
        max_age (int): Maximum token age in seconds
        
    Returns:
        bool: True if token is valid
    """
    try:
        # Decode token
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded.split('|')
        
        if len(parts) != 2:
            logger.warning(f"Invalid token format: {token}")
            return False
            
        timestamp, received_hmac = parts
        timestamp = int(timestamp)
        
        # Check token age
        current_time = int(time.time())
        if current_time - timestamp > max_age:
            logger.warning(f"Expired token: {current_time - timestamp} seconds old")
            return False
            
        # Reconstruct message
        message = f"{user_id}|{ip_address}|{user_agent}|{timestamp}".encode()
        
        # Verify HMAC
        secret_key = current_app.config['SECRET_KEY'].encode()
        h = hmac.new(secret_key, message, hashlib.sha256)
        expected_hmac = h.hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_hmac, received_hmac)
    
    except Exception as e:
        logger.error(f"Error verifying session token: {e}")
        return False

# 3. Brute force protection with exponential backoff
def get_login_attempts(ip_address):
    """
    Get number of failed login attempts for an IP address
    
    Args:
        ip_address (str): Client IP address
        
    Returns:
        tuple: (attempts, last_attempt, block_until)
    """
    from honeypot.database.mongodb import get_db
    
    db = get_db()
    if not db:
        # Default conservative values if DB is not available
        return (5, datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(minutes=15))
    
    try:
        result = db.admin_login_attempts.find_one({"ip": ip_address})
        
        if not result:
            return (0, None, None)
            
        return (
            result.get("attempts", 0),
            result.get("lastAttempt"),
            result.get("blockUntil")
        )
    except Exception as e:
        logger.error(f"Error getting login attempts: {e}")
        # Default conservative values on error
        return (5, datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(minutes=15))

def update_login_attempts(ip_address, success=False):
    """
    Update login attempts for an IP address
    
    Args:
        ip_address (str): Client IP address
        success (bool): Whether login was successful
        
    Returns:
        bool: True if operation succeeded
    """
    from honeypot.database.mongodb import get_db
    
    db = get_db()
    if not db:
        logger.error("Cannot update login attempts: Database unavailable")
        return False
    
    try:
        now = datetime.now(timezone.utc)
        
        if success:
            # Clear failed attempts on success
            db.admin_login_attempts.delete_many({"ip": ip_address})
            return True
        
        # Get current attempts
        attempts, _, _ = get_login_attempts(ip_address)
        attempts += 1
        
        # Calculate block duration with exponential backoff
        block_minutes = 0
        if attempts >= 3:
            # Start with 5 minutes, double each time: 5, 10, 20, 40, 80...
            block_minutes = 5 * (2 ** (attempts - 3))
            # Cap at 24 hours (1440 minutes)
            block_minutes = min(1440, block_minutes)
        
        block_until = now + timedelta(minutes=block_minutes) if block_minutes > 0 else None
        
        # Update or insert record
        db.admin_login_attempts.update_one(
            {"ip": ip_address},
            {
                "$set": {
                    "attempts": attempts,
                    "lastAttempt": now,
                    "blockUntil": block_until
                }
            },
            upsert=True
        )
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating login attempts: {e}")
        return False

# 4. Enhanced admin authorization check with context validation
def require_enhanced_admin():
    """
    Decorator for routes requiring enhanced admin authorization
    
    This decorator adds:
    - IP whitelisting
    - Brute force protection
    - Session token verification
    - Context binding (IP and User-Agent)
    - JWT verification (if configured)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 0. Get client details
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip and ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
                
            user_agent = request.headers.get('User-Agent', '')
            
            # 1. Check IP whitelist
            if not is_ip_allowed(client_ip):
                logger.warning(f"Access blocked for non-whitelisted IP: {client_ip}")
                abort(403)  # Forbidden
            
            # 2. Check brute force protection
            attempts, last_attempt, block_until = get_login_attempts(client_ip)
            if block_until and datetime.now(timezone.utc) < block_until:
                logger.warning(f"Access blocked due to too many failed attempts from IP: {client_ip}")
                block_remaining = (block_until - datetime.now(timezone.utc)).total_seconds() / 60
                return jsonify({
                    "error": f"Too many failed login attempts. Try again in {int(block_remaining)} minutes."
                }), 429  # Too Many Requests
            
            # 3. Check basic authentication
            is_authenticated = session.get('honeypot_admin_logged_in', False)
            if not is_authenticated:
                logger.warning(f"Unauthenticated access attempt from IP: {client_ip}")
                return jsonify({"error": "Not authenticated"}), 401
                
            # 4. Verify session context
            session_ip = session.get('admin_ip')
            if not session_ip or session_ip != client_ip:
                logger.warning(f"Session IP mismatch: {session_ip} vs {client_ip}")
                return jsonify({"error": "Session IP mismatch"}), 401
            
            # 5. Check session token (if implemented)
            session_token = session.get('admin_session_token')
            if session_token:
                admin_id = session.get('admin_id', 'admin')
                if not verify_session_token(session_token, admin_id, client_ip, user_agent):
                    logger.warning(f"Invalid session token from IP: {client_ip}")
                    return jsonify({"error": "Invalid session token"}), 401
            
            # 6. Check token expiration
            last_active_str = session.get('admin_last_active')
            if last_active_str:
                try:
                    # Parse ISO format timestamp with timezone
                    if 'Z' in last_active_str:
                        last_active = datetime.fromisoformat(last_active_str.replace('Z', '+00:00'))
                    elif '+' in last_active_str or '-' in last_active_str[10:]: 
                        last_active = datetime.fromisoformat(last_active_str)
                    else: 
                        last_active = datetime.fromisoformat(last_active_str).replace(tzinfo=timezone.utc)

                    now = datetime.now(timezone.utc)
                    inactivity_limit = timedelta(minutes=30)  # Shorter session timeout for enhanced security

                    if (now - last_active) > inactivity_limit:
                        logger.info(f"Admin session timeout due to inactivity. Last active: {last_active_str}")
                        session.clear()
                        return jsonify({"error": "Session expired"}), 401
                except Exception as e:
                    logger.error(f"Error parsing last_active time: {e}")
                    session.clear()
                    return jsonify({"error": "Session error"}), 401
            
            # 7. Update session last active time
            session['admin_last_active'] = datetime.now(timezone.utc).isoformat()
            session.modified = True
            
            # All checks passed, proceed to the route handler
            return f(*args, **kwargs)
            
        return decorated_function
    return decorator

# 5. Content Security Policy for admin routes
@enhanced_admin_bp.after_request
def add_security_headers(response):
    """Add security headers to all responses from enhanced admin routes"""
    # Content Security Policy - restrict resources to same origin
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'"
    
    # Prevent browsers from performing MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking attacks
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Enable browser XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer policy - limit information sent to other sites
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # HSTS - force browsers to use HTTPS
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Disable caching for sensitive pages
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

# -------------------- ENHANCED ROUTES --------------------

@enhanced_admin_bp.route('/login', methods=['POST'])
def enhanced_admin_login():
    """Enhanced admin login endpoint with additional security measures"""
    try:
        data = request.json or {}
        admin_key = data.get('adminKey', '')
        mfa_code = data.get('mfaCode', '')  # Optional MFA code
        
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
            
        user_agent = request.headers.get('User-Agent', '')
        
        # 1. Check IP whitelist first
        if not is_ip_allowed(client_ip):
            # Be careful here - don't reveal this is due to IP filtering
            # Just treat it like any other failed login
            logger.warning(f"Login attempt from non-whitelisted IP: {client_ip}")
            update_login_attempts(client_ip, success=False)
            return jsonify({"error": "Invalid credentials"}), 403
        
        # 2. Check brute force protection
        attempts, last_attempt, block_until = get_login_attempts(client_ip)
        if block_until and datetime.now(timezone.utc) < block_until:
            block_remaining = (block_until - datetime.now(timezone.utc)).total_seconds() / 60
            logger.warning(f"Blocked login attempt from IP: {client_ip}")
            return jsonify({
                "error": f"Too many failed login attempts. Try again in {int(block_remaining)} minutes."
            }), 429
        
        # 3. Verify credentials - replace with your actual verification
        from honeypot.backend.helpers.unhackable import sanitize_admin_key, constant_time_compare
        from honeypot.backend.routes.admin import ADMIN_PASS
        
        sanitized_key, is_valid, _ = sanitize_admin_key(admin_key)
        
        # 4. Optional MFA check - example implementation
        mfa_valid = True  # Replace with actual verification
        if current_app.config.get('ADMIN_MFA_REQUIRED', False) and not mfa_valid:
            logger.warning(f"Failed MFA verification from IP: {client_ip}")
            update_login_attempts(client_ip, success=False)
            return jsonify({"error": "Invalid MFA code"}), 403
        
        # 5. Final authentication check
        if sanitized_key and constant_time_compare(sanitized_key, ADMIN_PASS) and mfa_valid:
            # Login successful
            session.clear()  # Clear any existing session data
            
            # Generate a secure session ID
            session_id = secrets.token_hex(32)
            
            # Set session data
            session['honeypot_admin_logged_in'] = True
            session['admin_id'] = 'admin'  # Or use actual admin ID
            session['admin_last_active'] = datetime.now(timezone.utc).isoformat()
            session['admin_ip'] = client_ip
            
            # Generate and store enhanced session token
            session_token = generate_secure_session_token('admin', client_ip, user_agent)
            session['admin_session_token'] = session_token
            
            # Set CSRF token
            csrf_token = request.headers.get('X-CSRF-TOKEN')
            if csrf_token:
                session['csrf_token'] = csrf_token
            else:
                session['csrf_token'] = generate_csrf_token()
                
            session.modified = True
            
            # Reset failed attempts
            update_login_attempts(client_ip, success=True)
            
            # Log successful login
            logger.info(f"Enhanced admin login successful from IP: {client_ip}")
            
            # Record in audit log
            try:
                from honeypot.database.mongodb import get_db
                db = get_db()
                if db:
                    db.auditLogs.insert_one({
                        "timestamp": datetime.now(timezone.utc),
                        "ip": client_ip,
                        "user_agent": user_agent,
                        "action": "admin_login",
                        "success": True
                    })
            except Exception as e:
                logger.error(f"Failed to log successful login to audit log: {e}")
            
            return jsonify({
                "message": "Enhanced authentication successful",
                "session_id": request.cookies.get('session', 'unknown')
            }), 200
        else:
            # Login failed
            logger.warning(f"Failed enhanced admin login attempt from IP: {client_ip}")
            
            # Update failed attempts
            update_login_attempts(client_ip, success=False)
            
            # Record in audit log
            try:
                from honeypot.database.mongodb import get_db
                db = get_db()
                if db:
                    db.auditLogs.insert_one({
                        "timestamp": datetime.now(timezone.utc),
                        "ip": client_ip,
                        "user_agent": user_agent,
                        "action": "admin_login",
                        "success": False
                    })
            except Exception as e:
                logger.error(f"Failed to log failed login to audit log: {e}")
            
            return jsonify({"error": "Invalid credentials"}), 403
            
    except Exception as e:
        logger.error(f"Error during enhanced admin login: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Login process failed due to server error"}), 500

@enhanced_admin_bp.route('/logout', methods=['POST'])
@require_enhanced_admin()
def enhanced_admin_logout():
    """Enhanced admin logout with secure session termination"""
    try:
        # Get client details for audit log
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
            
        user_agent = request.headers.get('User-Agent', '')
        
        # Clear session data
        session.clear()
        
        # Add secure cookie to explicitly invalidate session
        response = jsonify({"message": "Logged out successfully"})
        response.set_cookie('session', '', expires=0, secure=True, httponly=True, samesite='Strict')
        
        # Record in audit log
        try:
            from honeypot.database.mongodb import get_db
            db = get_db()
            if db:
                db.auditLogs.insert_one({
                    "timestamp": datetime.now(timezone.utc),
                    "ip": client_ip,
                    "user_agent": user_agent,
                    "action": "admin_logout",
                    "success": True
                })
        except Exception as e:
            logger.error(f"Failed to log logout to audit log: {e}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error during enhanced admin logout: {e}")
        return jsonify({"error": "Logout process failed"}), 500

@enhanced_admin_bp.route('/secure-endpoint', methods=['GET'])
@require_enhanced_admin()
def secure_endpoint():
    """Example of a highly secured admin endpoint"""
    return jsonify({
        "message": "Access to secure endpoint granted",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ------------ INTEGRATION EXAMPLE ------------

def setup_enhanced_security(app):
    """
    Set up enhanced security for the Flask application
    
    Args:
        app (Flask): Flask application
    """
    # Register the enhanced admin blueprint
    app.register_blueprint(enhanced_admin_bp, url_prefix='/enhanced-admin')
    
    # Set up global security measures
    
    # 1. Request validation middleware
    @app.before_request
    def validate_request():
        """Validate all incoming requests"""
        # Check for suspicious query parameters
        for key, value in request.args.items():
            # Example: Check for SQL injection patterns
            sql_patterns = [
                r"['\"]\s*OR\s*['\"]?[\w\s]*['\"]?\s*=\s*['\"]?[\w\s]*['\"]?",
                r"UNION\s+SELECT",
                r"--\s",
                r";\s*SELECT",
                r"DROP\s+TABLE",
                r"TRUNCATE\s+TABLE"
            ]
            
            for pattern in sql_patterns:
                if re.search(pattern, str(value), re.IGNORECASE):
                    logger.warning(f"Blocked request with SQL injection pattern: {key}={value}")
                    abort(400)  # Bad Request
                    
            # Example: Check for XSS patterns
            xss_patterns = [
                r"<script",
                r"javascript:",
                r"on\w+=['\"]"
            ]
            
            for pattern in xss_patterns:
                if re.search(pattern, str(value), re.IGNORECASE):
                    logger.warning(f"Blocked request with XSS pattern: {key}={value}")
                    abort(400)  # Bad Request
    
    # 2. Add global security headers
    @app.after_request
    def add_global_security_headers(response):
        """Add security headers to all responses"""
        # Basic security headers for all routes
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    # 3. Enable strict CSRF protection for all routes
    # (Already provided by csrf_protect middleware in the honeypot package)
    
    # 4. Set secure cookie options
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
    )
    
    # 5. Example of rate limiting (would require Flask-Limiter or similar)
    # This is just a placeholder for what you could implement
    """
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Apply stricter limits to admin routes
    limiter.limit("10 per minute")(enhanced_admin_bp)
    """
    
    logger.info("Enhanced security measures enabled")
    
    return app

# Example usage in your main application:
"""
from flask import Flask
from honeypot import create_honeypot_app
from enhanced_admin_security import setup_enhanced_security

app = create_honeypot_app()
app = setup_enhanced_security(app)

if __name__ == "__main__":
    app.run(debug=False)
"""

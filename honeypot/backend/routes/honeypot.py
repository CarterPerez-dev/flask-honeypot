# honeypot/backend/routes/honeypot.py

import os
import logging
import ipaddress
import socket
import traceback
import time
import re
import hashlib
import json
from datetime import datetime, timedelta

from flask import (
    Blueprint, request, jsonify, g, make_response, session, current_app,
    render_template # Assuming you might use templates for fake responses
)
from bson.objectid import ObjectId
from pymongo import UpdateOne
import user_agents
import geoip2.database

# --- Package Specific Imports ---
# Use get_db to access the database within the request context
from honeypot.database.mongodb import get_db
# Import helper for admin checks if needed within honeypot routes directly
# from honeypot.backend.auth import require_cracked_admin # Adjust path if needed
# Import proxy detector (assuming it's initialized elsewhere or here)
from .proxy_detector import proxy_detector # Relative import, assuming this is correct
# --- import unhackable --
from .unhackable import (
    validate_admin_credentials, sanitize_admin_key, sanitize_role, secure_admin_login,
    InputValidationError
)

# --- Configure Logging ---
logger = logging.getLogger(__name__)

# --- Create Blueprint ---
honeypot_bp = Blueprint('honeypot', __name__)

# --- Global Variables / Lazy Loading for GeoIP ---
asn_reader = None
country_reader = None

def _load_geoip_readers_if_needed():
    """Load GeoIP readers using paths from app config, only if not already loaded."""
    global asn_reader, country_reader
    if asn_reader is None or country_reader is None:
        geoip_dir = current_app.config.get('GEOIP_DB_DIRECTORY', '/app/geoip_db') # Get path from config
        ASN_DB_PATH = os.path.join(geoip_dir, 'GeoLite2-ASN.mmdb')
        COUNTRY_DB_PATH = os.path.join(geoip_dir, 'GeoLite2-Country.mmdb')
        logger.info(f"Attempting to load GeoIP DBs from: {geoip_dir}")
        try:
            if os.path.exists(ASN_DB_PATH):
                asn_reader = geoip2.database.Reader(ASN_DB_PATH)
                logger.info("GeoLite2-ASN database loaded.")
            else:
                logger.warning(f"ASN database not found at {ASN_DB_PATH}")

            if os.path.exists(COUNTRY_DB_PATH):
                country_reader = geoip2.database.Reader(COUNTRY_DB_PATH)
                logger.info("GeoLite2-Country database loaded.")
            else:
                logger.warning(f"Country database not found at {COUNTRY_DB_PATH}")

        except Exception as e:
            logger.error(f"Error loading GeoIP databases: {str(e)}", exc_info=True)
            # Keep readers as None if loading fails

# --- Constants ---
DEFAULT_SCAN_PATHS = { # Keep or load from config/DB
    "/admin", "/admin/login", "/wp-admin", "/wp-login.php",
    "/administrator", "/login", "/administrator/index.php"
}
# Load common paths potentially (needs app context or pass db)
COMMON_SCAN_PATHS = DEFAULT_SCAN_PATHS.copy()

# --- Helper Functions (Adapted for Package Context) ---

def get_real_ip():
    """Get the client's real IP address, considering proxies."""
    # Use ProxyFix middleware's result if available
    if hasattr(request, 'environ') and 'REMOTE_ADDR' in request.environ:
        ip = request.environ['REMOTE_ADDR']
    else:
        # Fallback, might not be accurate behind multiple proxies without ProxyFix properly set
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
    return ip or "unknown_ip"

def get_client_identifier():
    """Generate a comprehensive client identifier using multiple factors."""
    factors = []
    ip = get_real_ip()
    factors.append(ip)
    user_agent = request.headers.get('User-Agent', '')
    factors.append(user_agent[:100] or "unknown_agent")
    accept = request.headers.get('Accept', '')
    accept_lang = request.headers.get('Accept-Language', '')
    accept_encoding = request.headers.get('Accept-Encoding', '')
    factors.append((accept + accept_lang + accept_encoding)[:50])
    connection = request.headers.get('Connection', '')
    factors.append(connection)

    # Simplified header list for brevity, keep your original list
    additional_headers = ['X-Requested-With', 'DNT', 'Referer', 'Origin']
    for header in additional_headers:
        value = request.headers.get(header, '')
        if value:
            factors.append(f"{header}:{value[:20]}")

    # Session data fingerprint
    if session:
        try:
            session_data = json.dumps(dict(session))
            factors.append(hashlib.md5(session_data.encode()).hexdigest()[:12])
        except Exception: # Handle potential non-serializable session data
            pass

    identifier = "|".join(filter(None, factors)) # Ensure no None values
    hashed_id = hashlib.sha256(identifier.encode()).hexdigest()
    return hashed_id


def extract_asn_from_ip(ip):
    """Get ASN, org, and country for an IP using MaxMind GeoLite2."""
    _load_geoip_readers_if_needed() # Lazy load
    asn_info = {"asn": "Unknown", "org": "Unknown", "country": "Unknown"}

    if not ip or ip in ("unknown_ip", "127.0.0.1"):
        return asn_info

    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
            asn_info.update({"asn": "Private", "org": "Private Network"})
            return asn_info
    except ValueError:
        asn_info.update({"asn": "Invalid", "org": "Invalid IP"})
        return asn_info

    try:
        if asn_reader:
            try:
                response = asn_reader.asn(ip)
                asn_info["asn"] = f"AS{response.autonomous_system_number}"
                asn_info["org"] = response.autonomous_system_organization
            except geoip2.errors.AddressNotFoundError:
                logger.debug(f"IP {ip} not found in ASN database.")
            except Exception as asn_e:
                 logger.warning(f"ASN lookup error for {ip}: {asn_e}")

        if country_reader:
            try:
                response = country_reader.country(ip)
                asn_info["country"] = response.country.name or "Unknown"
            except geoip2.errors.AddressNotFoundError:
                logger.debug(f"IP {ip} not found in Country database.")
            except Exception as country_e:
                 logger.warning(f"Country lookup error for {ip}: {country_e}")

    except Exception as e:
        logger.error(f"General error extracting ASN for IP {ip}: {str(e)}", exc_info=True)
        asn_info.update({"asn": "Error", "org": "Error"})

    return asn_info


def detect_tor_or_proxy(ip):
    """Check if IP is Tor exit node or known proxy using ProxyDetector."""
    if not ip or ip in ("unknown_ip", "127.0.0.1"):
        return False
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
            return False
    except ValueError:
        return False

    # Assuming proxy_detector is initialized and available
    # It might need initialization in create_app and stored in app.extensions
    # Or re-initialize it here if it's simple and stateless (less ideal)
    # Example: Accessing from app extensions
    pd = current_app.extensions.get('proxy_detector')
    if pd:
         return pd.is_tor_or_proxy(ip)
    else:
         logger.warning("ProxyDetector not initialized or found in app extensions.")
         # Fallback: Re-initialize here (make sure PROXY_CACHE_PATH is in config)
         try:
            cache_dir = current_app.config.get('PROXY_CACHE_PATH')
            if cache_dir:
                temp_detector = proxy_detector.ProxyDetector(cache_dir=cache_dir) # Re-import ProxyDetector if needed
                return temp_detector.is_tor_or_proxy(ip)
            else:
                 logger.error("PROXY_CACHE_PATH not configured.")
                 return False
         except Exception as e:
             logger.error(f"Failed to fallback initialize ProxyDetector: {e}")
             return False


def detect_bot_patterns(user_agent, request_info):
    """Analyze request patterns to determine if it's likely a bot."""
    # (Keep your original bot_strings list and logic)
    bot_indicators = []
    ua_lower = user_agent.lower() if user_agent else ""
    bot_strings = ['bot', 'crawl', 'spider', 'scan', 'wget', 'curl', 'python-requests', 'nmap', 'nikto'] # Add your full list
    for bot_string in bot_strings:
        if bot_string in ua_lower:
            bot_indicators.append(f"UA contains '{bot_string}'")
    if not user_agent or len(user_agent) < 10:
        bot_indicators.append("Short or missing user agent")
    # Add more pattern checks if needed
    return bot_indicators if bot_indicators else None


def log_scan_attempt(path, method, params=None, data=None):
    """Log comprehensive details about the scan attempt to the database."""
    try:
        db = get_db() # Get DB connection for this request
        client_id = get_client_identifier()
        ip = get_real_ip()
        user_agent = request.headers.get('User-Agent', '')

        # --- Add all your detailed logging logic here ---
        hostname = None
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except socket.herror:
             hostname = "Resolution failed"
        except Exception as e:
            hostname = f"Lookup error: {type(e).__name__}"


        is_port_scan = any(term in path.lower() for term in ['port', 'scan', 'nmap', 'masscan'])
        ua_lower = user_agent.lower()
        scanner_signs = ['nmap', 'nikto', 'sqlmap', 'acunetix', 'nessus', 'zap', 'burp']
        is_scanner = any(sign in ua_lower for sign in scanner_signs)
        suspicious_params_flag = False # Renamed to avoid conflict

        # Simplified check for suspicious params, keep your original list
        if params and request.args:
            param_checks = ['sleep', 'benchmark', 'exec', 'eval', 'union', 'select', 'script']
            for param, value in request.args.items():
                 # Basic check, enhance with regex for complex patterns
                 value_lower = str(value).lower()
                 if any(check in value_lower for check in param_checks):
                     suspicious_params_flag = True
                     break

        ua_info = {}
        try:
            if user_agent:
                parsed_ua = user_agents.parse(user_agent)
                ua_info = { # Keep your detailed ua_info structure
                    "browser_family": parsed_ua.browser.family,
                    "os_family": parsed_ua.os.family,
                    "is_bot": parsed_ua.is_bot
                }
        except Exception as e:
            ua_info = {"parse_error": str(e)}

        asn_info = extract_asn_from_ip(ip)
        bot_indicators = detect_bot_patterns(user_agent, {"path": path, "method": method})
        is_tor_or_proxy = detect_tor_or_proxy(ip)
        headers = {key: value for key, value in request.headers.items()}

        # Build the scan log document
        scan_log = {
            "clientId": client_id,
            "ip": ip,
            "path": path,
            "method": method,
            "timestamp": datetime.utcnow(),
            "user_agent": user_agent,
            "ua_info": ua_info,
            "asn_info": asn_info,
            "headers": headers,
            "query_params": dict(request.args) if request.args else None,
            "form_data": dict(request.form) if request.form else None,
            "json_data": request.get_json(silent=True),
            "cookies": dict(request.cookies),
            "is_tor_or_proxy": is_tor_or_proxy,
            "bot_indicators": bot_indicators,
            "hostname": hostname,
            "is_port_scan": is_port_scan,
            "is_scanner": is_scanner,
            "suspicious_params": suspicious_params_flag,
            "notes": []
        }

        # Add notes (example)
        if "X-Forwarded-For" in headers and ip != request.remote_addr:
             scan_log["notes"].append("Possible proxy/spoofing detected (XFF present)")

        # Suspicious query param keywords check (simplified)
        if request.args:
            suspicious_keywords = ['eval', 'exec', 'select', 'union', 'sleep', 'script', '../']
            combined_args = "".join(request.args.values()).lower()
            if any(keyword in combined_args for keyword in suspicious_keywords):
                 scan_log["notes"].append("Suspicious keywords found in query parameters")

        # Insert into database
        db.scanAttempts.insert_one(scan_log)

        # Update watchlist
        severity = 1
        if bot_indicators: severity += 1
        if is_tor_or_proxy: severity += 1
        if scan_log["notes"]: severity += len(scan_log["notes"])
        if is_port_scan: severity += 2
        if is_scanner: severity += 3
        if suspicious_params_flag: severity += 2

        db.watchList.update_one(
            {"clientId": client_id},
            {
                "$set": {
                    "lastSeen": datetime.utcnow(),
                    "lastPath": path,
                    "ip": ip,
                    "lastUserAgent": user_agent[:200] # Store recent UA
                },
                "$inc": {"count": 1, "severityScore": severity}, # Use a clearer field name
                "$push": {
                    "recentPaths": {
                        "$each": [{"path": path, "timestamp": datetime.utcnow()}],
                        "$slice": -10 # Keep last 10 paths
                    }
                }
            },
            upsert=True
        )

        return client_id

    except Exception as e:
        logger.error(f"Error logging scan attempt: {str(e)}", exc_info=True)
        return None


def is_rate_limited(client_id):
    """Check if the client has exceeded the honeypot rate limit."""
    db = get_db()
    # Get limits from config
    limit = current_app.config.get('HONEYPOT_RATE_LIMIT', 5)
    period = current_app.config.get('HONEYPOT_RATE_PERIOD', 60)

    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=period)

    count = db.scanAttempts.count_documents({
        "clientId": client_id,
        "timestamp": {"$gte": cutoff}
    })
    logger.debug(f"Rate limit check for {client_id}: count={count}, limit={limit}")
    return count >= limit


def get_threat_score(client_id):
    """Calculate a threat score for this client based on past behavior."""
    db = get_db()
    client = db.watchList.find_one({"clientId": client_id})
    if not client:
        return 0

    score = 0
    count = client.get("count", 0)
    severity = client.get("severityScore", 0) # Use updated field name

    # Weighted score
    score += min(count * 2, 30)        # More attempts increase score, capped
    score += min(severity * 3, 50)     # Severity has higher weight, capped

    # Recency bonus (more points for recent activity)
    last_seen = client.get("lastSeen")
    if last_seen and (datetime.utcnow() - last_seen) < timedelta(hours=1):
         score += 10
    elif last_seen and (datetime.utcnow() - last_seen) < timedelta(hours=24):
         score += 5

    # Check recent path diversity (scanning different things?)
    recent_paths = client.get("recentPaths", [])
    unique_recent_paths = len(set(p["path"] for p in recent_paths))
    if unique_recent_paths > 5: # If scanning many different paths recently
        score += 10

    # Check if previously blocked
    block_record = db.securityBlocklist.find_one({"clientId": client_id})
    if block_record:
        score += 15 # Add points if they were blocked before

    return min(score, 100) # Cap at 100

def handle_high_threat(client_id, threat_score, ip):
    """Take action based on threat score."""
    db = get_db()
    block_reason = None
    block_duration_days = 0

    if threat_score >= 85: # Stricter threshold for longer block
        block_reason = f"High threat score ({threat_score}), persistent scanning activity."
        block_duration_days = 7
    elif threat_score >= 60: # Medium threshold
        block_reason = f"Medium threat score ({threat_score}), suspicious scanning activity."
        block_duration_days = 1

    if block_reason and block_duration_days > 0:
        block_until = datetime.utcnow() + timedelta(days=block_duration_days)
        db.securityBlocklist.update_one(
            {"clientId": client_id}, # Can also block by IP: {"ip": ip}
            {
                "$set": {
                    "blockUntil": block_until,
                    "reason": block_reason,
                    "threatScore": threat_score,
                    "ip": ip, # Record IP at time of blocking
                    "updatedAt": datetime.utcnow()
                },
                "$setOnInsert": {"createdAt": datetime.utcnow()}
            },
            upsert=True
        )
        logger.warning(f"Blocking client {client_id} (IP: {ip}) until {block_until}. Reason: {block_reason}")
        # Add notification logic here if needed (e.g., send email, log to SIEM)


def render_fake_response(path, method):
    """Generate a fake response based on the path."""
    # This is a simplified example. You'd want more sophisticated templates.
    path_lower = path.lower()
    if 'login' in path_lower or 'admin' in path_lower:
        # Could render a fake login template
        # return render_template('fake_login.html')
        return "<html><head><title>Login</title></head><body><form method='post'><input type='text' name='username'><input type='password' name='password'><input type='submit' value='Login'></form></body></html>", 200
    elif 'wp-admin' in path_lower or 'wp-login' in path_lower:
        # Fake WordPress login
         return "<html><head><title>WordPress Login</title></head><body>Fake WP Login Page</body></html>", 200
    elif '.php' in path_lower:
        return "<?php // Access denied ?>", 403 # Fake PHP denial
    else:
        # Default fake 404 or generic page
        return "<html><head><title>Not Found</title></head><body><h1>Not Found</h1><p>The requested URL was not found on this server.</p></body></html>", 404


# --- Main Honeypot Handler ---
# This function will be dynamically registered for many routes
# by the register_routes_with_blueprint function in create_app.
def honeypot_handler():
    """Centralized handler for all honeypot scan routes."""
    path = request.path
    method = request.method
    start_time = time.time()
    client_id = None
    threat_score = 0

    try:
        # Log the attempt first
        client_id = log_scan_attempt(
            path,
            method,
            params=(request.method == 'GET'),
            data=(request.method == 'POST')
        )

        if client_id:
            # Check rate limiting *after* logging the attempt
            if is_rate_limited(client_id):
                logger.warning(f"Rate limit exceeded for client {client_id} accessing {path}")
                # Calculate threat score only if rate limited or potentially malicious
                threat_score = get_threat_score(client_id)

                # Handle high threat clients
                if threat_score >= 60: # Use the threshold defined in handle_high_threat
                    handle_high_threat(client_id, threat_score, get_real_ip())
                    # If blocked, maybe return a different response
                    resp_content = "<html><body><h1>Access Denied</h1></body></html>"
                    status_code = 403 # Forbidden
                    resp = make_response(resp_content, status_code)
                    resp.headers['Server'] = 'nginx/1.18.0 (Ubuntu)' # Vary server headers
                    resp.headers['Content-Type'] = 'text/html'
                    # Optionally add a rate limit header
                    # resp.headers['Retry-After'] = '3600' # Try again in 1 hour
                    return resp

                # If just rate limited but not blocked, return a 429
                resp_content = "<html><body><h1>Too Many Requests</h1></body></html>"
                status_code = 429
                resp = make_response(resp_content, status_code)
                resp.headers['Server'] = 'Apache/2.4.41 (Ubuntu)'
                resp.headers['Content-Type'] = 'text/html'
                resp.headers['Retry-After'] = '60' # Try again in 60 seconds
                return resp

        # If not rate limited or blocked, return a standard fake response
        response_content, status_code = render_fake_response(path, method)
        resp = make_response(response_content, status_code)
        # Vary headers slightly based on path/response type
        if 'wp-' in path:
             resp.headers['Server'] = 'Apache'
             resp.headers['X-Powered-By'] = 'PHP/7.4.3'
        elif 'admin' in path:
             resp.headers['Server'] = 'nginx/1.20.1'
        else:
            resp.headers['Server'] = 'Apache/2.4.41 (Ubuntu)' # Default

        resp.headers['Content-Type'] = 'text/html' # Assume HTML for most fake responses

        return resp

    except Exception as e:
         logger.error(f"Unhandled error in honeypot_handler for path {path}: {e}", exc_info=True)
         # Generic server error response
         return make_response("Internal Server Error", 500)

    finally:
        duration = time.time() - start_time
        logger.info(f"Honeypot request: {method} {path} from {get_real_ip()} -> Status: {resp.status_code if 'resp' in locals() else 'Error'} | ClientID: {client_id} | Score: {threat_score} | Duration: {duration:.4f}s")


# --- Analytics & Interaction Routes (Defined on honeypot_bp) ---

# IMPORTANT: Add authentication/authorization checks (e.g., require_cracked_admin)
# to all these administrative endpoints. You'll need to import your auth check function.
# Example decorator (adjust import path as needed):
# from honeypot.backend.auth import require_admin_auth
# @honeypot_bp.before_request
# def check_admin_auth():
#     # Apply auth check to all routes in this blueprint unless explicitly excluded
#     if request.endpoint and 'static' not in request.endpoint: # Example: skip static files
#          if not require_admin_auth(): # Replace with your actual auth check function
#               return jsonify({"error": "Unauthorized"}), 401

# --- Simple Analytics Endpoint ---
@honeypot_bp.route('/analytics', methods=['GET'])
# @require_admin_auth # Apply your auth decorator
def honeypot_analytics():
    """Return basic analytics about scan attempts."""
    # Add your actual admin authentication check here!
    # if not is_admin_authenticated(): return jsonify(...), 403

    db = get_db()
    try:
        total_attempts = db.scanAttempts.count_documents({})
        unique_ips = len(db.scanAttempts.distinct("ip"))
        unique_clients = len(db.scanAttempts.distinct("clientId"))

        pipeline_paths = [{"$group": {"_id": "$path", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
        top_paths = list(db.scanAttempts.aggregate(pipeline_paths))

        pipeline_ips = [{"$group": {"_id": "$ip", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
        top_ips = list(db.scanAttempts.aggregate(pipeline_ips))

        # Get recent activity (ensure ObjectId and datetime are serialized)
        recent_activity_raw = list(db.scanAttempts.find().sort("timestamp", -1).limit(20))
        recent_activity = []
        for activity in recent_activity_raw:
             activity["_id"] = str(activity["_id"])
             # Safely format timestamp
             ts = activity.get("timestamp")
             activity["timestamp"] = ts.isoformat() if isinstance(ts, datetime) else str(ts)
             # Remove potentially large fields for summary view
             activity.pop("headers", None)
             activity.pop("ua_info", None)
             recent_activity.append(activity)


        # Add watchlist summary
        watchlist_summary = list(db.watchList.find().sort("severityScore", -1).limit(10))
        for item in watchlist_summary:
             item["_id"] = str(item["_id"])
             item["lastSeen"] = item["lastSeen"].isoformat() if isinstance(item.get("lastSeen"), datetime) else str(item.get("lastSeen"))
             item.pop("recentPaths", None) # Don't include full path list in summary


        return jsonify({
            "scan_attempts_stats": {
                "total_attempts": total_attempts,
                "unique_ips": unique_ips,
                "unique_clients": unique_clients,
                "top_paths": top_paths,
                "top_ips": top_ips,
                "recent_activity": recent_activity
            },
            "watchlist_summary": watchlist_summary
        }), 200
    except Exception as e:
        logger.error(f"Error in honeypot analytics: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve analytics data"}), 500


# --- Interaction Logging Endpoint (Called by honeypot_pages.py potentially) ---
# Keep log_honeypot_interaction and related routes here if they are part of the core honeypot API
# Otherwise, they might belong in honeypot_pages.py if they are tightly coupled to those pages.

def log_honeypot_interaction(category, action, details=None):
    """Log interactions with specific honeypot pages/elements."""
    # This function might be called from honeypot_pages routes
    db = get_db()
    ip = get_real_ip()
    log_entry = {
        "category": category, # e.g., 'wordpress', 'cpanel', 'custom_page'
        "action": action,     # e.g., 'page_view', 'login_attempt', 'button_click', 'form_submit'
        "timestamp": datetime.utcnow(),
        "ip_address": ip, # Use a consistent field name
        "user_agent": request.headers.get('User-Agent', 'Unknown'),
        "path": request.path,
        "method": request.method,
        "details": details or {} # Store structured details
    }

    # Enhance with GeoIP and other context if needed
    log_entry["geo_info"] = extract_asn_from_ip(ip)
    log_entry["client_id"] = get_client_identifier() # Link interaction to scanner profile

    result = db.honeypotInteractions.insert_one(log_entry) # Use a dedicated collection
    interaction_id = str(result.inserted_id)
    logger.info(f"Honeypot interaction logged: ID={interaction_id}, Category={category}, Action={action}, IP={ip}")
    return interaction_id


@honeypot_bp.route('/log-interaction', methods=['POST'])
# @require_some_form_of_auth_or_rate_limit # Prevent abuse of this logging endpoint
def log_client_side_interaction():
    """Endpoint for logging client-side interactions via AJAX/fetch."""
    # Add rate limiting or basic validation if needed
    if not request.is_json:
        return jsonify({"status": "error", "message": "Expected JSON data"}), 400

    data = request.get_json()
    category = data.get('category', 'unknown_page')
    action = data.get('action', 'client_event')
    details = data.get('details', {})

    # Perform some validation on input data
    if not isinstance(details, dict):
        details = {"raw_details": str(details)} # Ensure details is a dict
    if len(category) > 50 or len(action) > 50:
         return jsonify({"status": "error", "message": "Invalid category or action length"}), 400

    try:
        interaction_id = log_honeypot_interaction(category, action, details)
        return jsonify({"status": "success", "interaction_id": interaction_id})
    except Exception as e:
        logger.error(f"Error logging client-side interaction: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


# --- Detailed Stats and Interaction Viewing ---
# Add the rest of your analytics routes here, adapting them similarly:
# - Use get_db()
# - Use current_app.config if needed
# - Add authentication checks
# - Ensure proper JSON serialization (ObjectIds, datetimes)
# - Use relative imports

# Example: /interactions route
@honeypot_bp.route('/interactions', methods=['GET'])
# @require_admin_auth
def view_honeypot_interactions():
    # Add auth check
    db = get_db()
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit
        filter_query = {} # Add filtering logic based on request.args

        # Example filters:
        category = request.args.get('category')
        action = request.args.get('action')
        ip = request.args.get('ip')

        if category: filter_query['category'] = category
        if action: filter_query['action'] = action
        if ip: filter_query['ip_address'] = {"$regex": ip, "$options": "i"}

        interactions_raw = list(db.honeypotInteractions.find(filter_query)
                              .sort("timestamp", -1)
                              .skip(skip)
                              .limit(limit))
        total_count = db.honeypotInteractions.count_documents(filter_query)

        interactions = []
        for item in interactions_raw:
            item["_id"] = str(item["_id"])
            ts = item.get("timestamp")
            item["timestamp"] = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            interactions.append(item)

        return jsonify({
            "interactions": interactions,
            "total": total_count,
            "page": page,
            "limit": limit
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving honeypot interactions: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve interactions"}), 500

# Add routes like /interactions/<id>, /detailed-stats, /combined-analytics etc.
# Remember to adapt them for the package structure (get_db, config, auth).
# Add helper functions like get_interaction_explanation, get_risk_level etc. at the end or in a separate utils file.

# --- Helper Functions for Explanations (Keep these) ---
def get_interaction_type_explanation(interaction_type):
    # ... (your existing explanation logic)
    explanations = {
        "page_view": "Visitor viewed the page.",
        "login_attempt": "Visitor attempted login.",
        # Add more
    }
    return explanations.get(interaction_type, f"Unknown type: {interaction_type}")

def get_page_type_explanation(page_type):
    # ... (your existing explanation logic)
    explanations = {
        "wordpress": "Fake WordPress admin page.",
        "admin_panels": "Generic fake admin panel.",
         # Add more
    

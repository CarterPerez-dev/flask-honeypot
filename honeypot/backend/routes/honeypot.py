# honeypot/backend/routes/honeypot.py
from flask import Blueprint, request, render_template, jsonify, make_response, current_app, g
from bson.objectid import ObjectId
from datetime import datetime, timedelta, timezone
import time
import re
import hashlib
import json
import logging
import ipaddress
import user_agents
import socket
from pymongo import UpdateOne
import traceback

# Import helpers
from honeypot.backend.helpers.proxy_detector import get_proxy_detector, ProxyCache
from honeypot.database.models import HoneypotInteraction, ScanAttempt, WatchlistEntry, BlocklistEntry
from honeypot.backend.routes.admin import require_admin  
from honeypot.database.mongodb import get_db, get_mongo_client
from honeypot.backend.helpers.db_utils import with_db_recovery

# Create logger
logger = logging.getLogger(__name__)

# Create honeypot blueprint
honeypot_bp = Blueprint('honeypot', __name__)

# Constants
DEFAULT_SCAN_PATHS = {
    "/admin",
    "/admin/login",
    "/wp-admin",
    "/wp-login.php",
    "/administrator",
    "/login",
    "/administrator/index.php"
}

# Load common scan paths from database
COMMON_SCAN_PATHS = set()

@with_db_recovery
def load_common_scan_paths():
    """Load the most common scan paths from the database"""
    global COMMON_SCAN_PATHS
    
    # Start with the default paths
    COMMON_SCAN_PATHS = DEFAULT_SCAN_PATHS.copy()
    
    try:
        # Check if we're in an application context
        from flask import has_app_context
        if not has_app_context():
            logger.info("Not in application context, using default scan paths only")
            return
            
        # Get database connection directly
        db = get_db()
        
        if db:
            # Get top 500 scanned paths from database
            pipeline = [
                {"$group": {"_id": "$path", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 500}
            ]
            results = list(db.scanAttempts.aggregate(pipeline))
            
            # Add database paths to our set (which already contains the defaults)
            for result in results:
                COMMON_SCAN_PATHS.add(result["_id"])
            
            logger.info(f"Loaded {len(COMMON_SCAN_PATHS)} common scan paths from database")
    except Exception as e:
        logger.error(f"Error loading common scan paths: {str(e)}")
        


def get_client_identifier():
    """
    Generate a comprehensive client identifier using multiple factors.
    This creates a more reliable identifier even if the client is trying to hide.
    
    Returns:
        str: SHA-256 hash of the client identifier
    """
    factors = []
    
    # Basic identifiers
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip and ',' in ip:  # Handle proxy chains
        ip = ip.split(',')[0].strip()
    factors.append(ip or "unknown_ip")
    
    # Browser fingerprinting
    user_agent = request.headers.get('User-Agent', '')
    factors.append(user_agent[:100] or "unknown_agent")
    
    # Accept headers can be used for fingerprinting
    accept = request.headers.get('Accept', '')
    accept_lang = request.headers.get('Accept-Language', '')
    accept_encoding = request.headers.get('Accept-Encoding', '')
    factors.append((accept + accept_lang + accept_encoding)[:50])
    
    # Connection-specific headers
    connection = request.headers.get('Connection', '')
    factors.append(connection)
    
    # Additional headers for fingerprinting
    additional_headers = [
        'X-Requested-With', 'DNT', 'Referer', 'Origin',
        'Sec-Fetch-Dest', 'Sec-Fetch-Mode', 'Sec-Fetch-Site',
        'Cache-Control', 'If-None-Match', 'If-Modified-Since',
    ]
    
    for header in additional_headers:
        value = request.headers.get(header, '')
        if value:
            factors.append(f"{header}:{value[:20]}")
    
    # If we have a session, add a fingerprint of session data
    from flask import session
    if session:
        try:
            session_data = json.dumps(dict(session))
            factors.append(hashlib.md5(session_data.encode()).hexdigest()[:12])
        except:
            pass
    
    # Build and hash the combined identifier
    identifier = "|".join(factors)
    hashed_id = hashlib.sha256(identifier.encode()).hexdigest()
    
    return hashed_id


def extract_asn_from_ip(ip):
    """
    Get ASN, organization, and country information for an IP address
    using MaxMind GeoLite2 databases
    
    Args:
        ip (str): IP address to lookup
        
    Returns:
        dict: ASN and geolocation information for the IP
    """
    try:
        # Skip private, local, or invalid IPs
        if not ip or ip == "unknown_ip" or ip == "127.0.0.1":
            return {"asn": "Unknown", "org": "Unknown", "country": "Unknown"}
        
        # Make sure we're working with a valid IP
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
                return {"asn": "Private", "org": "Private Network", "country": "Unknown"}
        except ValueError:
            return {"asn": "Invalid", "org": "Invalid IP", "country": "Unknown"}
        
        # Get ASN information
        asn_info = {"asn": "Unknown", "org": "Unknown", "country": "Unknown"}
        
        # Try to get ASN and organization
        asn_reader = getattr(g, 'asn_reader', None) or current_app.config.get('ASN_READER')
        if asn_reader:
            try:
                response = asn_reader.asn(ip)
                asn_info["asn"] = f"AS{response.autonomous_system_number}"
                asn_info["org"] = response.autonomous_system_organization
            except Exception:
                # IP not found in ASN database or other error
                pass
        
        # Try to get country
        country_reader = getattr(g, 'country_reader', None) or current_app.config.get('COUNTRY_READER')
        if country_reader:
            try:
                response = country_reader.country(ip)
                asn_info["country"] = response.country.name or "Unknown"
            except Exception:
                # IP not found in Country database or other error
                pass
        
        return asn_info
    
    except Exception as e:
        logger.error(f"Error extracting ASN for IP {ip}: {str(e)}")
        return {"asn": "Error", "org": "Error", "country": "Unknown"}


def detect_tor_or_proxy(ip):
    """
    Check if the IP is likely a Tor exit node or a known proxy service.
    
    Args:
        ip (str): IP address to check
        
    Returns:
        bool: True if IP is detected as Tor/proxy
    """
    if not ip or ip == "unknown_ip":
        return False
    
    # Basic IP validation
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
            return False
    except ValueError:
        return False
    
    # Get proxy detector
    proxy_detector = get_proxy_detector(current_app.config.get('PROXY_CACHE'))
    
    # Check against detector
    return proxy_detector.is_tor_or_proxy(ip)


def detect_bot_patterns(user_agent, request_info):
    """
    Analyze request patterns to determine if it's likely a bot.
    
    Args:
        user_agent (str): User-Agent header
        request_info (dict): Additional request information
        
    Returns:
        list: List of bot indicators, or None if no indicators
    """
    bot_indicators = []
    
    ua_lower = user_agent.lower()
    
    # Check for common bot strings in user agent
    bot_strings = [
        # Common crawlers and bots
        'bot', 'crawl', 'spider', 'scan', 'scrape',
        # Web automation tools
        'wget', 'curl', 'httr', 'httpie', 'requests', 'axios',
        # Programming language HTTP clients
        'python-requests', 'python-urllib', 'go-http', 'java-http-client', 'okhttp',
        'aiohttp', 'httpclient', 'urllib', 'apache-httpclient',
        # Security scanners and testing tools
        'nmap', 'nikto', 'burp', 'zap', 'acunetix', 'qualys', 'nessus', 'sqlmap',
        'masscan', 'dirbuster', 'gobuster', 'dirb', 'wfuzz', 'hydra',
    ]
    
    for bot_string in bot_strings:
        if bot_string in ua_lower:
            bot_indicators.append(f"UA contains '{bot_string}'")
    
    # Empty or very short user agents are suspicious
    if len(user_agent) < 10:
        bot_indicators.append("Short user agent")
    
    # Check for automated request patterns
    path = request_info.get('path', '')
    if path and any(path.endswith(ext) for ext in ['.php', '.aspx', '.jsp']):
        # Scanning for specific file types
        bot_indicators.append(f"Scanning for {path.split('.')[-1]} files")
    
    return bot_indicators if bot_indicators else None


@with_db_recovery
def log_scan_attempt(path, method, params=None, data=None):
    """
    Log comprehensive details about the scan attempt to the database.
    
    Args:
        path (str): Request path
        method (str): HTTP method
        params (bool): Whether to log query parameters
        data (bool): Whether to log form/JSON data
        
    Returns:
        str: Client ID for the scan attempt
    """
    try:
        # Get client identifier
        client_id = get_client_identifier()
        
        # Get client IP
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        
        # Get user agent
        user_agent = request.headers.get('User-Agent', '')
        
        # Perform reverse DNS lookup
        hostname = None
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = None
        
        # Check for port scanning attempts
        is_port_scan = any(scan_term in path.lower() for scan_term in [
            'port', 'scan', 'nmap', 'masscan', 'shodan', 'censys'
        ])
        
        # Check for common vulnerability scanners in user agent
        ua_lower = user_agent.lower() if user_agent else ""
        scanner_signs = ['nmap', 'nikto', 'sqlmap', 'acunetix', 'nessus', 
                        'zap', 'burp', 'whatweb', 'qualys', 'openvas']
        is_scanner = any(sign in ua_lower for sign in scanner_signs)
        
        # Check for suspicious request parameters
        suspicious_params = False
        if params and request.args:
            param_checks = ['sleep', 'benchmark', 'exec', 'eval', 'union', 
                         'select', 'update', 'delete', 'insert', 'script']
            for param, value in request.args.items():
                if any(check in str(value).lower() for check in param_checks):
                    suspicious_params = True
                    break
        
        # Parse the user agent string for more details
        ua_info = {}
        try:
            if user_agent:
                parsed_ua = user_agents.parse(user_agent)
                ua_info = {
                    "browser": {
                        "family": parsed_ua.browser.family,
                        "version": parsed_ua.browser.version_string
                    },
                    "os": {
                        "family": parsed_ua.os.family,
                        "version": parsed_ua.os.version_string
                    },
                    "device": {
                        "family": parsed_ua.device.family,
                        "brand": parsed_ua.device.brand,
                        "model": parsed_ua.device.model
                    },
                    "is_mobile": parsed_ua.is_mobile,
                    "is_tablet": parsed_ua.is_tablet,
                    "is_pc": parsed_ua.is_pc,
                    "is_bot": parsed_ua.is_bot
                }
        except Exception as e:
            ua_info = {"parse_error": str(e)}
        
        # Get ASN info
        asn_info = extract_asn_from_ip(ip)
        
        # Detect if it's a likely bot
        bot_indicators = detect_bot_patterns(user_agent, {
            "path": path,
            "method": method
        })
        
        # Check if using Tor or proxy
        is_tor_or_proxy = detect_tor_or_proxy(ip)
        
        # Extract all headers for analysis
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
            "query_params": dict(request.args) if params else None,
            "form_data": dict(request.form) if data else None,
            "json_data": request.get_json(silent=True) if data else None,
            "cookies": {key: value for key, value in request.cookies.items()},
            "is_tor_or_proxy": is_tor_or_proxy,
            "bot_indicators": bot_indicators,
            "hostname": hostname,
            "is_port_scan": is_port_scan,
            "is_scanner": is_scanner,
            "suspicious_params": suspicious_params,
            "notes": []
        }
        
        # Additional security checks
        if "X-Forwarded-For" in headers and ip != request.remote_addr:
            scan_log["notes"].append("Possible IP spoofing attempt")
        
        # Check for suspicious query parameters
        if params:
            suspicious_params = [
                # SQL injection
                'eval', 'exec', 'select', 'union', 'sleep', 'benchmark', 
                'from', 'where', 'having', 'group by', 'order by', 'insert', 
                # Command injection
                'cmd', 'command', 'system', 'shell', 'bash', 'powershell', 
                '|', '&', ';', '`', '$', '>', '<', 'ping', 'nc', 'ncat', 
                # File inclusion/traversal
                'file', 'path', 'include', 'require', 'load', '../', '..\\', 
                # XSS-related
                'script', 'alert', 'onerror', 'onload', 'iframe', 'javascript', 
                # NoSQL injection
                '$where', '$gt', '$lt', '$ne', '$exists', '$regex',
            ]
            
            for param, value in request.args.items():
                if any(sus in str(value).lower() for sus in suspicious_params):
                    scan_log["notes"].append(f"Suspicious parameter: {param}")
        
        # Get database connection
        db = get_db()
        
        if db is not None:
            try:
                # Insert into database
                db.scanAttempts.insert_one(scan_log)
                
                # Update watchlist with this client
                severity = 1  # Base severity level
                
                # Increase severity based on certain factors
                if bot_indicators:
                    severity += 1
                if is_tor_or_proxy:
                    severity += 1
                if scan_log["notes"]:
                    severity += len(scan_log["notes"])
                if is_port_scan:
                    severity += 2
                if is_scanner:
                    severity += 3
                if suspicious_params:
                    severity += 2
                
                # Update the watchlist
                db.watchList.update_one(
                    {"clientId": client_id},
                    {
                        "$set": {
                            "lastSeen": datetime.utcnow(),
                            "lastPath": path,
                            "ip": ip
                        },
                        "$inc": {"count": 1, "severity": severity}
                    },
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error saving scan attempt to database: {str(e)}")
        else:
            logger.warning("MongoDB connection not available, scan attempt not saved")
        
        # Return the client ID for potential further actions
        return client_id
    
    except Exception as e:
        logger.error(f"Error logging scan attempt: {str(e)}")
        logger.error(traceback.format_exc())
        return None


@with_db_recovery
def is_rate_limited(client_id):
    """
    Check if the client has exceeded the honeypot rate limit.
    
    Args:
        client_id (str): Client identifier
        
    Returns:
        bool: True if rate limited
    """
    # Get rate limit settings from app config
    rate_limit = current_app.config.get('HONEYPOT_RATE_LIMIT', 5)
    rate_period = current_app.config.get('HONEYPOT_RATE_PERIOD', 60)
    
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=rate_period)
    
    # Get database connection
    db = get_db()
    
    if db is None:
        logger.warning("MongoDB connection not available, rate limit check failed")
        return False
    
    try:
        # Count recent requests from this client to honeypot endpoints
        count = db.scanAttempts.count_documents({
            "clientId": client_id,
            "timestamp": {"$gte": cutoff}
        })
        
        return count >= rate_limit
    except Exception as e:
        logger.error(f"Error checking rate limit: {str(e)}")
        return False


@with_db_recovery
def get_threat_score(client_id):
    """
    Calculate a threat score for this client based on past behavior.
    Higher score = more suspicious.
    
    Args:
        client_id (str): Client identifier
        
    Returns:
        int: Threat score (0-100)
    """
    # Get database connection
    db = get_db()
    
    if db is None:
        logger.warning("MongoDB connection not available, threat score check failed")
        return 0
    
    try:
        # Get client history
        client = db.watchList.find_one({"clientId": client_id})
        if not client:
            return 0
        
        # Base score
        score = 0
        
        # Number of scan attempts
        count = client.get("count", 0)
        if count > 1:
            score += min(count * 5, 30)  
        
        # Severity from past scans
        severity = client.get("severity", 0)
        score += min(severity * 2, 50)  
        
        # Recent activity (within last hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_count = db.scanAttempts.count_documents({
            "clientId": client_id,
            "timestamp": {"$gte": cutoff}
        })
        score += min(recent_count * 2, 20)  
        
        return min(score, 100)  
    except Exception as e:
        logger.error(f"Error calculating threat score: {str(e)}")
        return 0


@with_db_recovery
def handle_high_threat(client_id, threat_score):
    """
    Take action based on threat score.
    
    Args:
        client_id (str): Client identifier
        threat_score (int): Threat score (0-100)
    """
    # Get database connection
    db = get_db()
    
    if db is None:
        logger.warning("MongoDB connection not available, high threat handling failed")
        return
    
    try:
        if threat_score >= 80:
            # Very high threat - add to blocklist for 7 days
            db.securityBlocklist.update_one(
                {"clientId": client_id},
                {
                    "$set": {
                        "blockUntil": datetime.utcnow() + timedelta(days=7),
                        "reason": "Excessive scanning activity",
                        "threatScore": threat_score,
                        "updatedAt": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.warning(f"Added client {client_id} to blocklist (threat score: {threat_score})")
            
        elif threat_score >= 50:
            # Medium-high threat - temporary block for 24 hours
            db.securityBlocklist.update_one(
                {"clientId": client_id},
                {
                    "$set": {
                        "blockUntil": datetime.utcnow() + timedelta(hours=24),
                        "reason": "Suspicious scanning activity",
                        "threatScore": threat_score,
                        "updatedAt": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"Added client {client_id} to temporary blocklist (threat score: {threat_score})")
    except Exception as e:
        logger.error(f"Error handling high threat: {str(e)}")


@with_db_recovery
def log_honeypot_interaction(page_type, interaction_type, additional_data=None):
    """
    Log honeypot interaction to the database
    
    Args:
        page_type (str): Type of honeypot page
        interaction_type (str): Type of interaction
        additional_data (dict, optional): Additional data
        
    Returns:
        str: Interaction ID
    """
    try:
        # Get client details
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        
        user_agent = request.headers.get('User-Agent', '')
        referer = request.headers.get('Referer', '')
        
        # Create interaction fingerprint
        interaction_id = hashlib.sha256(f"{ip}|{user_agent}|{time.time()}".encode()).hexdigest()
        
        # Build log entry
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.utcnow(),
            "ip_address": ip,
            "user_agent": user_agent,
            "referer": referer,
            "page_type": page_type,
            "interaction_type": interaction_type,
            "http_method": request.method,
            "path": request.path,
            "query_string": dict(request.args),
            "headers": {k: v for k, v in request.headers.items()},
            "cookies": {k: v for k, v in request.cookies.items()},
        }
        
        # Add form data if applicable
        if request.form:
            log_entry["form_data"] = dict(request.form)
        
        # Add JSON data if applicable
        if request.is_json:
            log_entry["json_data"] = request.get_json(silent=True)
        
        # Add additional custom data
        if additional_data:
            log_entry["additional_data"] = additional_data
        
        # Get ASN info
        log_entry["geoInfo"] = extract_asn_from_ip(ip)
        
        # Check for Tor/proxy
        log_entry["is_tor_or_proxy"] = detect_tor_or_proxy(ip)
        
        # Get database connection
        db = get_db()
        
        if db is not None:
            try:
                # Store in database
                db.honeypot_interactions.insert_one(log_entry)
            except Exception as e:
                logger.error(f"Error saving interaction to database: {str(e)}")
        else:
            logger.warning("MongoDB connection not available, interaction not saved")
        
        return interaction_id
    except Exception as e:
        logger.error(f"Error logging honeypot interaction: {str(e)}")
        return None


def render_fake_response(path, method):
    """
    Render a fake but convincing response for honeypot
    
    Args:
        path (str): Request path
        method (str): HTTP method
        
    Returns:
        str: HTML content for the response
    """
    # Default to a generic login page
    template = 'honeypot/generic-login.html'
    
    # Map paths to appropriate templates
    path_lower = path.lower()
    
    # WordPress admin pages
    if any(x in path_lower for x in ['wp-admin', 'wp-login', 'wordpress']):
        template = 'honeypot/wp-dashboard.html'
    
    # Admin panels
    elif any(x in path_lower for x in ['admin', 'administrator', 'panel', 'dashboard']):
        template = 'honeypot/admin-dashboard.html'
    
    # phpMyAdmin
    elif any(x in path_lower for x in ['phpmyadmin', 'pma', 'mysql', 'database']):
        template = 'honeypot/phpmyadmin-dashboard.html'
    
    # cPanel
    elif any(x in path_lower for x in ['cpanel', 'cPanel', 'hosting']):
        template = 'honeypot/cpanel-dashboard.html'
    
    try:
        return render_template(template)
    except Exception as e:
        logger.error(f"Error rendering template {template}: {str(e)}")
        # Fallback to simple text response
        return "<html><body><h1>Login</h1><form><input name='username'><input name='password' type='password'><button>Login</button></form></body></html>"


@honeypot_bp.route('/log-interaction', methods=['POST'])
@with_db_recovery
def log_client_side_interaction():
    """
    Endpoint for logging client-side interactions via AJAX
    
    Returns:
        dict: Status response
    """
    if not require_admin():  
        return jsonify({"error": "Not authorized"}), 401

    if not request.is_json:
        return jsonify({"status": "error", "message": "Expected JSON data"}), 400
    
    data = request.get_json()
    page_type = data.get('page_type', 'unknown')
    interaction_type = data.get('interaction_type', 'unknown')
    additional_data = data.get('additional_data', {})
    
    interaction_id = log_honeypot_interaction(page_type, interaction_type, additional_data)
    
    return jsonify({"status": "success", "interaction_id": interaction_id})


@honeypot_bp.route('/handler', methods=['GET', 'POST'])
@with_db_recovery
def honeypot_handler():
    """
    Main handler for all honeypot routes.
    Logs the attempt and returns appropriate fake response.
    
    Returns:
        Response: Fake response
    """ 
    
    path = request.path
    method = request.method
    
    client_id = log_scan_attempt(
        path, 
        method, 
        params=(request.method == 'GET'), 
        data=(request.method == 'POST')
    )
    
    if client_id and is_rate_limited(client_id):
        threat_score = get_threat_score(client_id)
        
        if threat_score >= 50:
            handle_high_threat(client_id, threat_score)
            
            if threat_score >= 90:
                resp = make_response("403 Forbidden", 403)
                resp.headers['Server'] = 'Apache/2.4.41 (Ubuntu)'
                return resp
    
    resp = make_response(render_fake_response(path, method))
    
    resp.headers['Server'] = 'Apache/2.4.41 (Ubuntu)'
    resp.headers['X-Powered-By'] = 'PHP/7.4.3'
    
    return resp


@honeypot_bp.route('/analytics', methods=['GET'])
@with_db_recovery
def honeypot_analytics():
    """
    Return analytics about honeypot activity
    
    Returns:
        dict: Honeypot analytics
    """
    
    if not require_admin():  
        return jsonify({"error": "Not authorized"}), 401    
    
    try:
        # Get database connection
        db = get_db()
        
        if db is None:
            return jsonify({"error": "Database connection not available"}), 500
        
        total_attempts = db.scanAttempts.count_documents({})
        unique_ips = len(db.scanAttempts.distinct("ip"))
        unique_clients = len(db.scanAttempts.distinct("clientId"))
        
        # Get top paths
        top_paths_pipeline = [
            {"$group": {"_id": "$path", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_paths = list(db.scanAttempts.aggregate(top_paths_pipeline))
        
        # Get top IPs
        top_ips_pipeline = [
            {"$group": {"_id": "$ip", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_ips = list(db.scanAttempts.aggregate(top_ips_pipeline))
        
        # Get recent activity
        recent_activity = list(db.scanAttempts.find()
                                .sort("timestamp", -1)
                                .limit(20))
        
        # Format for JSON response
        for activity in recent_activity:
            activity["_id"] = str(activity["_id"])
            activity["timestamp"] = activity["timestamp"].isoformat()
        
        return jsonify({
            "total_attempts": total_attempts,
            "unique_ips": unique_ips,
            "unique_clients": unique_clients,
            "top_paths": top_paths,
            "top_ips": top_ips,
            "recent_activity": recent_activity
        }), 200
    except Exception as e:
        logger.error(f"Error in honeypot analytics: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve analytics",
            "details": str(e)
        }), 500


@honeypot_bp.route('/detailed-stats', methods=['GET'])
@with_db_recovery
def honeypot_detailed_stats():
    """
    Return detailed statistics about honeypot interactions, keeping original field names
    and adding total_interactions, credential_attempts, and time_series.
    
    Returns:
        dict: Detailed honeypot statistics
    """
    if not require_admin():  
        return jsonify({"error": "Not authorized"}), 401    
    
    try:
        # Get database connection
        db = get_db()
        
        if db is None:
            logger.error("Database connection not available for detailed stats")
            return jsonify({"error": "Database connection not available"}), 500
        
        # --- Define Time Frames (More Precise) ---
        now = datetime.now(timezone.utc) # Use timezone-aware UTC now
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # Calculate week start (assuming Monday is 0, Sunday is 6)
        week_start = today_start - timedelta(days=now.weekday()) 
        # Calculate month start
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # For time_series chart
        thirty_days_ago = now - timedelta(days=30)


        stats = {
            "threats_detected": 0,
            "unique_page_types": 0,
            "unique_interaction_types": 0,
            "today_interactions": 0,
            "week_interactions": 0,
            "month_interactions": 0,
            "page_type_stats": [],
            "interaction_stats": [],
            "top_interactors": [],
            "payload_downloads": [],
            "geographic_stats": [],
            "timestamp": now.isoformat(),         
            "total_interactions": 0,
            "credential_attempts": [],
            "time_series": [] 
        }
        



        try:
            stats["total_interactions"] = db.honeypot_interactions.count_documents({})
        except Exception as e:
            logger.error(f"Error counting total interactions: {str(e)}")


        try:
            threat_conditions = {
                 "$or": [

                    {"is_tor_or_proxy": True},


                    {"interaction_type": "user_database_download_attempted"},
                    {"interaction_type": "bitcoin_mining_started"},
                    {"interaction_type": "bitcoin_withdrawal_attempted"},
                    {"interaction_type": "encryption_started"},
                    {"interaction_type": "bsod_triggered"},
                    {"interaction_type": "password_view_attempted"},
                    {"interaction_type": "password_decrypt_attempted"},
                    {"interaction_type": "api_keys_viewed"},
                    {"interaction_type": "api_key_copied"},
                    {"interaction_type": "terminal_glitch_opened"},
                    {"interaction_type": "vanishing_button_clicked"},
                    {"interaction_type": "sql_injection_attempt"},
                    {"interaction_type": "account_lockout"},
                    {"interaction_type": "login_attempt"},

                 ]
             }

            stats["threats_detected"] = db.honeypot_interactions.count_documents(threat_conditions)
        except Exception as e:
            logger.error(f"Error counting threats: {str(e)}")
        

        try:
            page_types = list(db.honeypot_interactions.aggregate([
                {"$match": {"page_type": {"$ne": None, "$ne": ""}}},
                {"$group": {"_id": "$page_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 1000} 
            ]))
            stats["page_type_stats"] = page_types
            stats["unique_page_types"] = db.honeypot_interactions.distinct("page_type", {"page_type": {"$ne": None, "$ne": ""}}) 
            stats["unique_page_types"] = len(stats["unique_page_types"])
        except Exception as e:
            logger.error(f"Error getting page types: {str(e)}")
        

        try:
            interaction_types = list(db.honeypot_interactions.aggregate([
                {"$match": {"interaction_type": {"$ne": None, "$ne": ""}}},
                {"$group": {"_id": "$interaction_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 1000} 
            ]))
            stats["interaction_stats"] = interaction_types
            stats["unique_interaction_types"] = db.honeypot_interactions.distinct("interaction_type", {"interaction_type": {"$ne": None, "$ne": ""}}) 
            stats["unique_interaction_types"] = len(stats["unique_interaction_types"])
        except Exception as e:
            logger.error(f"Error getting interaction types: {str(e)}")
        

        try:
            stats["today_interactions"] = db.honeypot_interactions.count_documents({
                "timestamp": {"$gte": today_start}
            })
        except Exception as e:
            logger.error(f"Error counting today's interactions: {str(e)}")
        
        try:
            stats["week_interactions"] = db.honeypot_interactions.count_documents({
                "timestamp": {"$gte": week_start}
            })
        except Exception as e:
            logger.error(f"Error counting week's interactions: {str(e)}")
        
        try:
            stats["month_interactions"] = db.honeypot_interactions.count_documents({
                "timestamp": {"$gte": month_start}
            })
        except Exception as e:
            logger.error(f"Error counting month's interactions: {str(e)}")
        

        try:
            stats["top_interactors"] = list(db.honeypot_interactions.aggregate([
                {"$match": {"ip_address": {"$ne": None, "$ne": ""}}},
                {"$group": {"_id": "$ip_address", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
        except Exception as e:
            logger.error(f"Error getting top interactors: {str(e)}")
        

        try:
            stats["payload_downloads"] = list(db.honeypot_interactions.aggregate([
                {"$match": {"interaction_type": "download_attempt"}},
                {"$group": {"_id": "$additional_data.filename", "count": {"$sum": 1}}}, 
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]))
            if not stats["payload_downloads"] or stats["payload_downloads"][0].get("_id") is None:
                 stats["payload_downloads"] = list(db.honeypot_interactions.aggregate([
                    {"$match": {"interaction_type": "download_attempt"}},
                    {"$group": {"_id": "$page_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 5}
                 ]))

        except Exception as e:
            logger.error(f"Error getting payload downloads: {str(e)}")
        
        try:
            stats["geographic_stats"] = list(db.honeypot_interactions.aggregate([
                {"$match": {"geoInfo.country": {"$exists": True, "$ne": None, "$ne": "", "$ne": "Unknown", "$ne": "Private"}}},
                {"$group": {"_id": "$geoInfo.country", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
        except Exception as e:
            logger.error(f"Error getting geographic stats: {str(e)}")


        try:
            credential_attempts_list = list(db.honeypot_interactions.find(
                {"interaction_type": "login_attempt"}
            ).sort("timestamp", -1).limit(10)) 
            

            formatted_attempts = []
            for attempt in credential_attempts_list:
                attempt['_id'] = str(attempt['_id']) 
                if isinstance(attempt.get('timestamp'), datetime):
                    attempt['timestamp'] = attempt['timestamp'].isoformat()
                formatted_attempts.append(attempt) 
            stats["credential_attempts"] = formatted_attempts
        except Exception as e:
            logger.error(f"Error getting credential attempts: {str(e)}")


        try:
            time_series_agg = list(db.honeypot_interactions.aggregate([
                {"$match": {"timestamp": {"$gte": thirty_days_ago}}},
                {"$group": {
                    "_id": { 
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp", "timezone": "UTC"}
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}},
                {"$project": { 
                    "_id": 0,
                    "date": "$_id",
                    "count": "$count"
                }}
            ]))
            stats["time_series"] = time_series_agg
        except Exception as e:
            logger.error(f"Error getting time series data: {str(e)}")


        logger.info(f"Returning detailed stats with original names + additions.")
        return jsonify(stats), 200
    
    except Exception as e:
        logger.error(f"Critical error in /detailed-stats endpoint: {str(e)}")
        logger.error(traceback.format_exc()) 
        return jsonify({
            "error": "Failed to retrieve detailed honeypot statistics",
            "details": str(e)
        }), 500


@honeypot_bp.route('/interactions', methods=['GET'])
@with_db_recovery
def view_honeypot_interactions():
    """
    Get honeypot interactions with filtering and pagination
    
    Returns:
        dict: Honeypot interactions
    """
    if not require_admin():  
        return jsonify({"error": "Not authorized"}), 401
    
    try:
        db = get_db()
        
        if db is None:
            return jsonify({"error": "Database connection not available"}), 500
        

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit
        

        filter_query = {}
        
        page_type = request.args.get('page_type')
        if page_type:
            filter_query['page_type'] = page_type
        
        interaction_type = request.args.get('interaction_type')
        if interaction_type:
            filter_query['interaction_type'] = interaction_type
        

        interactions = list(db.honeypot_interactions.find(filter_query)
                            .sort("timestamp", -1)
                            .skip(skip)
                            .limit(limit))
        

        for interaction in interactions:
            interaction['_id'] = str(interaction['_id'])
            if isinstance(interaction.get('timestamp'), datetime):
                interaction['timestamp'] = interaction['timestamp'].isoformat()
        

        total_count = db.honeypot_interactions.count_documents(filter_query)
        
        return jsonify({
            "interactions": interactions,
            "total": total_count,
            "page": page,
            "limit": limit
        }), 200
    except Exception as e:
        logger.error(f"Error getting honeypot interactions: {str(e)}")
        return jsonify({
            "error": f"Failed to retrieve honeypot interactions: {str(e)}",
        }), 500


@honeypot_bp.route('/interactions/<interaction_id>', methods=['GET'])
@with_db_recovery
def get_honeypot_interaction(interaction_id):
    """
    Get detailed information about a specific honeypot interaction
    
    Args:
        interaction_id (str): Interaction ID
        
    Returns:
        dict: Honeypot interaction details
    """
    if not require_admin():  
        return jsonify({"error": "Not authorized"}), 401
    
    try:
        db = get_db()
        
        if db is None:
            return jsonify({"error": "Database connection not available"}), 500
        

        interaction = db.honeypot_interactions.find_one({"_id": ObjectId(interaction_id)})
        
        if not interaction:
            return jsonify({"error": "Interaction not found"}), 404
        

        interaction["_id"] = str(interaction["_id"])
        

        if isinstance(interaction.get("timestamp"), datetime):
            interaction["timestamp"] = interaction["timestamp"].isoformat()
        
        # Add human-readable explanations to the data
        interaction["explanations"] = {
            "summary": "This is a record of when someone interacted with your honeypot system.",
            "interaction_type": get_interaction_type_explanation(interaction.get("interaction_type", "")),
            "page_type": get_page_type_explanation(interaction.get("page_type", "")),
            "suspicious_factors": get_suspicious_factors(interaction),
            "technical_details": "The data shows exactly what the visitor sent to your server, including their browser details, IP address, and what they were trying to access."
        }
        
        return jsonify(interaction), 200
    except Exception as e:
        logger.error(f"Error getting honeypot interaction: {str(e)}")
        return jsonify({
            "error": f"Failed to retrieve interaction details: {str(e)}"
        }), 500


# Helper functions for human-readable explanations
def get_interaction_type_explanation(interaction_type):
    """
    Return a human-readable explanation of the interaction type
    
    Args:
        interaction_type (str): Interaction type
        
    Returns:
        str: Human-readable explanation
    """
    explanations = {
        "page_view": "Someone visited this page directly, possibly trying to access restricted admin areas.",
        "download_attempt": "Someone tried to download a file from your honeypot, which could indicate they were tricked by the fake system.",
        "form_submission": "Someone submitted login credentials or other data to your honeypot form.",
        "button_click": "Someone clicked on an interactive element in your honeypot.",
        "menu_click": "Someone clicked on a menu item in your honeypot interface.",
        "login_attempt": "Someone attempted to log in to your honeypot system.",
        "api_call": "Someone made an API call to your honeypot system.",
        "file_upload": "Someone attempted to upload a file to your honeypot system.",
        "search_query": "Someone submitted a search query to your honeypot system.",
    }
    
    return explanations.get(interaction_type, f"Unknown interaction type: {interaction_type}")


def get_page_type_explanation(page_type):
    """
    Return a human-readable explanation of the page type
    
    Args:
        page_type (str): Page type
        
    Returns:
        str: Human-readable explanation
    """
    explanations = {
        "wordpress": "A fake WordPress admin page that attracts attackers looking for vulnerable WordPress sites.",
        "admin_panel": "A fake admin login page designed to attract unauthorized access attempts.",
        "admin_panels": "A fake admin login page designed to attract unauthorized access attempts.",
        "phpmyadmin": "A fake database administration tool page that attracts attackers looking for database access.",
        "cpanel": "A fake hosting control panel that attracts attackers looking for website hosting access.",
        "webmail": "A fake webmail interface that attracts attackers looking for email access.",
        "forum": "A fake forum administration page that attracts attackers.",
        "e_commerce": "A fake e-commerce administration page that attracts attackers.",
        "cms": "A fake content management system page that attracts attackers.",
        "file_sharing": "A fake file sharing interface that attracts attackers.",
        "database_endpoints": "A fake database endpoint that attracts attackers.",
        "remote_access": "A fake remote access interface that attracts attackers.",
        "iot_devices": "A fake IoT device interface that attracts attackers.",
        "devops_tools": "A fake DevOps tool interface that attracts attackers.",
        "web_frameworks": "A fake web framework administration interface that attracts attackers.",
        "logs_and_debug": "A fake logs or debug interface that attracts attackers.",
        "backdoors_and_shells": "A fake backdoor or shell interface that attracts attackers.",
        "injection_attempts": "A page designed to detect injection attempts.",
        "mobile_endpoints": "A fake mobile API endpoint that attracts attackers.",
        "cloud_services": "A fake cloud service interface that attracts attackers.",
        "monitoring_tools": "A fake monitoring tool interface that attracts attackers.",
    }
    
    return explanations.get(page_type, f"Unknown page type: {page_type}")


def get_suspicious_factors(interaction):
    """
    Analyze the interaction for suspicious factors
    
    Args:
        interaction (dict): Interaction data
        
    Returns:
        list: List of suspicious factors
    """
    factors = []
    
    # Check for Tor/proxy usage
    if interaction.get("is_tor_or_proxy"):
        factors.append("This visitor appears to be using Tor or a proxy service, which might indicate they're trying to hide their identity.")
    
    # Check for known bot patterns
    if interaction.get("bot_indicators") and len(interaction.get("bot_indicators", [])) > 0:
        factors.append("This visitor shows signs of being an automated tool or bot rather than a real person.")
    
    # Check for scanner signatures
    if interaction.get("is_scanner"):
        factors.append("This visitor appears to be using a vulnerability scanner tool, which is commonly used by attackers.")
    
    # Check for port scanning
    if interaction.get("is_port_scan"):
        factors.append("This visitor seems to be scanning your server for open ports, which is often a first step in an attack.")
    
    # Check for suspicious query parameters
    if interaction.get("suspicious_params"):
        factors.append("This visitor is using suspicious parameters that might indicate an attempt to exploit vulnerabilities.")
    
    return factors if factors else ["No obviously suspicious behavior detected."]


@honeypot_bp.route('/html-interactions', methods=['GET'])
@with_db_recovery
def get_html_interactions():
    """
    Get honeypot HTML page interactions with filtering and pagination
    
    Returns:
        dict: HTML interactions
    """
    if not require_admin():  
        return jsonify({"error": "Not authorized"}), 401
    
    try:
        # Get database connection
        db = get_db()
        
        if db is None:
            return jsonify({"error": "Database connection not available"}), 500
        
        # Get pagination params
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit
        
        # Get filter params
        page_type = request.args.get('page_type')
        interaction_type = request.args.get('interaction_type')
        ip_filter = request.args.get('ip')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search_term = request.args.get('search')
        
        # Build query
        query = {}
        
        # Apply filters
        if page_type and page_type != 'all':
            query['page_type'] = page_type
        
        if interaction_type and interaction_type != 'all':
            query['interaction_type'] = interaction_type
        
        if ip_filter:
            query['ip_address'] = {"$regex": ip_filter, "$options": "i"}
        
        # Date range filter
        if date_from or date_to:
            query['timestamp'] = {}
            if date_from:
                try:
                    from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    query['timestamp']["$gte"] = from_date
                except:
                    pass
            
            if date_to:
                try:
                    to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    query['timestamp']["$lte"] = to_date
                except:
                    pass
        
        # Full text search across multiple fields
        if search_term:
            search_regex = {"$regex": search_term, "$options": "i"}
            query["$or"] = [
                {"page_type": search_regex},
                {"interaction_type": search_regex},
                {"ip_address": search_regex},
                {"additional_data.username": search_regex},
                {"additional_data.message": search_regex},
                {"additional_data.input": search_regex},
                {"additional_data.form_data": search_regex}
            ]
        
        # Get total count for pagination
        total_count = db.honeypot_interactions.count_documents(query)
        
        # Get interactions with pagination
        interactions = list(db.honeypot_interactions.find(query)
                            .sort("timestamp", -1)
                            .skip(skip)
                            .limit(limit))
        
        # Format for JSON
        for interaction in interactions:
            interaction['_id'] = str(interaction['_id'])
            if isinstance(interaction.get('timestamp'), datetime):
                interaction['timestamp'] = interaction['timestamp'].isoformat()
        
        # Get unique page types and interaction types for filters
        page_types = db.honeypot_interactions.distinct("page_type")
        interaction_types = db.honeypot_interactions.distinct("interaction_type")
        
        return jsonify({
            "interactions": interactions,
            "total": total_count,
            "page": page,
            "limit": limit,
            "page_types": page_types,
            "interaction_types": interaction_types
        }), 200
    except Exception as e:
        logger.error(f"Error getting HTML interactions: {str(e)}")
        return jsonify({
            "error": f"Failed to retrieve HTML interactions: {str(e)}"
        }), 500
        
        
@honeypot_bp.route('/combined-analytics', methods=['GET'])
@with_db_recovery
def combined_honeypot_analytics():
    """Return combined analytics from both honeypot collections"""

    if not require_admin():  
        return jsonify({"error": "Not authorized"}), 401
    
    try:
        # Get database connection directly
        db = get_db()
        
        if db is None:
            logger.error("Database connection not available")
            return jsonify({"error": "Database connection not available"}), 500
        
        # Initialize with empty values
        stats = {
            "total_attempts": 0,
            "unique_ips": 0,
            "unique_clients": 0,
            "today_interactions": 0,
            "week_interactions": 0,
            "threats_detected": 0,
            "top_paths": [],
            "top_ips": [],
            "recent_activity": []
        }
        
        try:
            # Statistics from both collections
            scan_attempts_count = db.scanAttempts.count_documents({})
            interactions_count = db.honeypot_interactions.count_documents({})
            stats["total_attempts"] = scan_attempts_count + interactions_count
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}")
            return jsonify({"error": "Failed to count documents", "details": str(e)}), 500
        
        try:
            # Combine unique IPs from both collections
            scan_ips = set(db.scanAttempts.distinct("ip") or [])
            interaction_ips = set(db.honeypot_interactions.distinct("ip_address") or [])
            stats["unique_ips"] = len(scan_ips.union(interaction_ips))
        except Exception as e:
            logger.error(f"Error getting unique IPs: {str(e)}")
        
        try:
            # Combine unique clients
            scan_clients = set(db.scanAttempts.distinct("clientId") or [])
            interaction_clients = set(db.honeypot_interactions.distinct("interaction_id") or [])
            stats["unique_clients"] = len(scan_clients.union(interaction_clients))
        except Exception as e:
            logger.error(f"Error getting unique clients: {str(e)}")
        
        # Get top paths from both collections
        paths_data = []
        
        try:
            # Get paths from scanAttempts
            if scan_attempts_count > 0:
                scan_paths_pipeline = [
                    {"$group": {"_id": "$path", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]
                scan_paths = list(db.scanAttempts.aggregate(scan_paths_pipeline))
                paths_data.extend(scan_paths)
        except Exception as e:
            logger.error(f"Error getting scan paths: {str(e)}")
        
        try:
            # Get paths from honeypot_interactions
            if interactions_count > 0:
                interaction_paths_pipeline = [
                    {"$group": {"_id": "$path", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]
                interaction_paths = list(db.honeypot_interactions.aggregate(interaction_paths_pipeline))
                paths_data.extend(interaction_paths)
        except Exception as e:
            logger.error(f"Error getting interaction paths: {str(e)}")
        
        # Combine and sort paths
        path_counts = {}
        for item in paths_data:
            path = item["_id"]
            count = item["count"]
            if path in path_counts:
                path_counts[path] += count
            else:
                path_counts[path] = count
        
        stats["top_paths"] = [{"_id": k, "count": v} for k, v in path_counts.items()]
        stats["top_paths"].sort(key=lambda x: x["count"], reverse=True)
        stats["top_paths"] = stats["top_paths"][:10]
        
        # Similar approach for IPs
        ips_data = []
        
        try:
            # Get IPs from scanAttempts
            if scan_attempts_count > 0:
                scan_ips_pipeline = [
                    {"$group": {"_id": "$ip", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]
                scan_ips_list = list(db.scanAttempts.aggregate(scan_ips_pipeline))
                ips_data.extend(scan_ips_list)
        except Exception as e:
            logger.error(f"Error getting scan IPs: {str(e)}")
        
        try:
            # Get IPs from honeypot_interactions
            if interactions_count > 0:
                interaction_ips_pipeline = [
                    {"$group": {"_id": "$ip_address", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]
                interaction_ips_list = list(db.honeypot_interactions.aggregate(interaction_ips_pipeline))
                ips_data.extend(interaction_ips_list)
        except Exception as e:
            logger.error(f"Error getting interaction IPs: {str(e)}")
        
        # Combine and sort IPs
        ip_counts = {}
        for item in ips_data:
            ip = item["_id"]
            count = item["count"]
            if ip in ip_counts:
                ip_counts[ip] += count
            else:
                ip_counts[ip] = count
        
        stats["top_ips"] = [{"_id": k, "count": v} for k, v in ip_counts.items()]
        stats["top_ips"].sort(key=lambda x: x["count"], reverse=True)
        stats["top_ips"] = stats["top_ips"][:10]
        
        # Get recent activity (combine both collections)
        recent_activities = []
        
        try:
            recent_scan_attempts = list(db.scanAttempts.find().sort("timestamp", -1).limit(10))
            # Format scan attempts
            for item in recent_scan_attempts:
                item["_id"] = str(item["_id"])
                if isinstance(item.get("timestamp"), datetime):
                    item["timestamp"] = item["timestamp"].isoformat()
                # Normalize data structure
                item["ip"] = item.get("ip")
                item["path"] = item.get("path", "")
                item["type"] = item.get("type", "page_view")
                recent_activities.extend([item])
        except Exception as e:
            logger.error(f"Error getting recent scan attempts: {str(e)}")
        
        try:
            recent_interactions = list(db.honeypot_interactions.find().sort("timestamp", -1).limit(10))
            # Format interactions
            for item in recent_interactions:
                item["_id"] = str(item["_id"])
                if isinstance(item.get("timestamp"), datetime):
                    item["timestamp"] = item["timestamp"].isoformat()
                # Normalize data structure
                item["ip"] = item.get("ip_address")
                item["path"] = item.get("path", "")
                item["type"] = item.get("interaction_type", "page_view")
                recent_activities.extend([item])
        except Exception as e:
            logger.error(f"Error getting recent interactions: {str(e)}")
        
        # Combine, sort by timestamp, and limit to 20
        recent_activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        stats["recent_activity"] = recent_activities[:20]
        
        # Count detected threats
        try:
            threats_detected = 0
            threats_detected += db.scanAttempts.count_documents({
                "$or": [
                    {"is_scanner": True},
                    {"is_port_scan": True},
                    {"suspicious_params": True},
                    {"bot_indicators": {"$exists": True, "$ne": []}}
                ]
            })
            threats_detected += db.honeypot_interactions.count_documents({
                "$or": [
                    {"is_scanner": True},
                    {"is_port_scan": True},
                    {"suspicious_params": True}
                ]
            })
            stats["threats_detected"] = threats_detected
        except Exception as e:
            logger.error(f"Error counting threats: {str(e)}")
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error in combined honeypot analytics: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve analytics",
            "details": str(e)
        }), 500

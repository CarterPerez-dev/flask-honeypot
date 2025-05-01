# honeypot/backend/helpers/proxy_detector.py
import requests
import threading
import time
import logging
from datetime import datetime, timedelta
import ipaddress
import os
import json  # Add missing import

logger = logging.getLogger(__name__)


class ProxyCache:
    """Simple file-based cache for proxy lists."""
    def __init__(self, cache_dir='proxy_cache', cache_expiry_hours=6):
        self.cache_dir = cache_dir
        self.cache_expiry = timedelta(hours=cache_expiry_hours)
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"ProxyCache initialized with directory: {self.cache_dir}")

    def _get_cache_path(self, key):
        # Basic sanitization of key for filename
        safe_key = "".join(c for c in key if c.isalnum() or c in ('_', '-')).rstrip()
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def load_cache(self, key):
        """Loads data from cache if not expired."""
        path = self._get_cache_path(key)
        if not os.path.exists(path):
            logger.debug(f"Cache miss (file not found): {key}")
            return None
        try:
            # Check file modification time
            mtime = os.path.getmtime(path)
            if (datetime.utcnow() - datetime.utcfromtimestamp(mtime)) > self.cache_expiry:
                logger.info(f"Cache expired: {key}")
                # Optionally delete expired file: os.remove(path)
                return None

            with open(path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Cache hit: {key}")
                return data
        except Exception as e:
            logger.error(f"Error loading cache for {key} from {path}: {e}")
            return None

    def save_cache(self, key, data):
        """Saves data to cache."""
        path = self._get_cache_path(key)
        try:
            with open(path, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Cache saved: {key}")
        except Exception as e:
            logger.error(f"Error saving cache for {key} to {path}: {e}")


class ProxyDetector:
    """Detects Tor exit nodes and proxy servers based on IP address"""
    
    def __init__(self, cache=None):
        """
        Initialize the proxy detector
        
        Args:
            cache (ProxyCache, optional): Proxy cache instance. Defaults to None.
        """
        self.cache = cache or ProxyCache()
        self.tor_exit_nodes = set()
        self.known_proxies = set()
        self.last_update = datetime.utcnow() - timedelta(days=1)  
        self.update_lock = threading.Lock()
        
        # Load cached data if available
        self._load_cached_data()
        
        # Start background updater thread
        self._start_updater()
    
    def _load_cached_data(self):
        """Load cached proxy and Tor node data"""
        try:
            # Load Tor exit nodes
            tor_data = self.cache.load_cache('tor_nodes')
            if tor_data and 'nodes' in tor_data:
                self.tor_exit_nodes = set(tor_data['nodes'])
                if 'timestamp' in tor_data:
                    try:
                        self.last_update = datetime.fromisoformat(tor_data['timestamp'])
                    except:
                        self.last_update = datetime.utcnow() - timedelta(days=1)
            
            # Load known proxies
            proxy_data = self.cache.load_cache('proxies')
            if proxy_data and 'proxies' in proxy_data:
                self.known_proxies = set(proxy_data['proxies'])
            
            logger.info(f"Loaded {len(self.tor_exit_nodes)} Tor nodes and {len(self.known_proxies)} proxies from cache")
        except Exception as e:
            logger.error(f"Error loading cached proxy data: {str(e)}")
    
    def _update_lists(self):
        """Update Tor exit node and proxy lists"""
        with self.update_lock:
            now = datetime.utcnow()
            # Only update if it's been more than 6 hours
            if (now - self.last_update) < timedelta(hours=6):
                return
            
            try:
                # Update Tor exit node list from Tor Project
                tor_response = requests.get("https://check.torproject.org/exit-addresses", timeout=10)
                if tor_response.status_code == 200:
                    new_nodes = set()
                    for line in tor_response.text.split("\n"):
                        if line.startswith("ExitAddress "):
                            parts = line.split()
                            if len(parts) >= 2:
                                new_nodes.add(parts[1])
                    
                    # Only update if we got a reasonable number of nodes
                    if len(new_nodes) > 50:
                        self.tor_exit_nodes = new_nodes
                        logger.info(f"Updated Tor exit node list, found {len(new_nodes)} nodes")
                        
                        # Save to cache
                        self.cache.save_cache('tor_nodes', {
                            'nodes': list(new_nodes),
                            'timestamp': now.isoformat()
                        })
                
                # Also try dan.me.uk as an alternative source
                try:
                    dan_response = requests.get("https://www.dan.me.uk/torlist/", timeout=10)
                    if dan_response.status_code == 200:
                        for line in dan_response.text.split("\n"):
                            ip = line.strip()
                            if ip and self._is_valid_ip(ip):
                                self.tor_exit_nodes.add(ip)
                except Exception as e:
                    logger.warning(f"Error getting Tor list from dan.me.uk: {str(e)}")
                
                # Public proxy lists
                proxy_lists = [
                    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt",
                    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
                ]
                
                new_proxies = set()
                for url in proxy_lists:
                    try:
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            for line in response.text.split("\n"):
                                if ":" in line:
                                    ip = line.split(":")[0].strip()
                                    if ip and self._is_valid_ip(ip):
                                        new_proxies.add(ip)
                    except Exception as e:
                        logger.warning(f"Error getting proxy list from {url}: {str(e)}")
                
                if new_proxies:
                    self.known_proxies = new_proxies
                    logger.info(f"Updated proxy list, found {len(new_proxies)} proxies")
                    
                    # Save to cache
                    self.cache.save_cache('proxies', {
                        'proxies': list(new_proxies),
                        'timestamp': now.isoformat()
                    })
                
                # Update timestamp
                self.last_update = now
                
            except Exception as e:
                logger.error(f"Error updating proxy lists: {str(e)}")
    
    def _start_updater(self):
        """Start the background updater thread"""
        def updater_thread():
            while True:
                try:
                    self._update_lists()
                    # Sleep for 2 hours
                    time.sleep(7200)
                except Exception as e:
                    logger.error(f"Error in updater thread: {str(e)}")
                    time.sleep(300)  # Sleep for 5 minutes on error
        
        thread = threading.Thread(target=updater_thread, daemon=True)
        thread.start()
    
    def is_tor_exit_node(self, ip):
        """
        Check if the given IP is a Tor exit node
        
        Args:
            ip (str): IP address to check
            
        Returns:
            bool: True if IP is a Tor exit node
        """
        # Trigger an update if needed
        if (datetime.utcnow() - self.last_update) > timedelta(hours=12):
            self._update_lists()
        
        return ip in self.tor_exit_nodes
    
    def is_known_proxy(self, ip):
        """
        Check if the given IP is a known proxy
        
        Args:
            ip (str): IP address to check
            
        Returns:
            bool: True if IP is a known proxy
        """
        return ip in self.known_proxies
    
    def is_tor_or_proxy(self, ip):
        """
        Check if the given IP is either a Tor exit node or a known proxy
        
        Args:
            ip (str): IP address to check
            
        Returns:
            bool: True if IP is a Tor exit node or known proxy
        """
        return self.is_tor_exit_node(ip) or self.is_known_proxy(ip)
    
    def _is_valid_ip(self, ip):
        """
        Check if a string is a valid IP address
        
        Args:
            ip (str): String to check
            
        Returns:
            bool: True if string is a valid IP address
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


# Create a global instance for convenience
proxy_detector = None

def get_proxy_detector(cache=None):
    """
    Get or create the global proxy detector instance
    
    Args:
        cache (ProxyCache, optional): Proxy cache instance. Defaults to None.
    
    Returns:
        ProxyDetector: Global proxy detector instance
    """
    global proxy_detector
    if proxy_detector is None:
        proxy_detector = ProxyDetector(cache)
    return proxy_detector

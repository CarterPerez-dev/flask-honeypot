"""Backend module for Honeypot Framework"""

# Expose key components at module level
from honeypot.backend.app import create_app
from honeypot.backend.middleware.csrf_protection import csrf_protect, generate_csrf_token

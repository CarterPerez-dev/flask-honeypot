"""
Honeypot Framework - A comprehensive honeypot system for detecting and analyzing unauthorized access attempts
"""

from honeypot.backend.app import create_app
from honeypot.config.settings import get_config

__version__ = '0.1.0'

# Expose key functions at package level
create_honeypot_app = create_app

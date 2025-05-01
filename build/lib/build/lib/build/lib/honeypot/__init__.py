"""
Honeypot Framework - A comprehensive honeypot system for detecting and analyzing unauthorized access attempts
"""


from honeypot.backend.app import create_app
from honeypot.config.settings import get_config


try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown" 



create_honeypot_app = create_app


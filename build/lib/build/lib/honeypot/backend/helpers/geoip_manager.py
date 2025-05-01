# honeypot/backend/helpers/geoip_manager.py
import os
import logging
import requests
import shutil
import tarfile
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class GeoIPManager:
    """Manages GeoIP database files and updates"""
    
    def __init__(self, db_directory=None, license_key=None):
        """
        Initialize the GeoIP Manager
        
        Args:
            db_directory (str, optional): Path to database directory. Defaults to None.
            license_key (str, optional): MaxMind license key. Defaults to None.
        """
        self.license_key = license_key
        
        if not db_directory:
            # Default to a directory within the package
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_directory = os.path.join(base_dir, '..', '..', 'data', 'geoip_db')
        else:
            self.db_directory = db_directory
            
        # Create directory if it doesn't exist
        os.makedirs(self.db_directory, exist_ok=True)
        
        # Define paths for databases
        self.asn_db_path = os.path.join(self.db_directory, 'GeoLite2-ASN.mmdb')
        self.country_db_path = os.path.join(self.db_directory, 'GeoLite2-Country.mmdb')
        
        logger.info(f"GeoIP manager initialized in {self.db_directory}")
    
    def check_databases(self):
        """
        Check if databases exist and are up-to-date
        
        Returns:
            dict: Status of each database
        """
        status = {
            'asn': {
                'exists': os.path.exists(self.asn_db_path),
                'needs_update': False
            },
            'country': {
                'exists': os.path.exists(self.country_db_path),
                'needs_update': False
            }
        }
        
        # Check if files need update (older than 30 days)
        for db_type in status:
            if status[db_type]['exists']:
                db_path = self.asn_db_path if db_type == 'asn' else self.country_db_path
                file_mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
                max_age = timedelta(days=30)
                
                status[db_type]['needs_update'] = (datetime.now() - file_mtime) > max_age
                status[db_type]['age_days'] = (datetime.now() - file_mtime).days
        
        return status
    
    def download_database(self, db_type):
        """
        Download a specific GeoIP database
        
        Args:
            db_type (str): Type of database ('asn' or 'country')
            
        Returns:
            bool: True if download was successful
        """
        if not self.license_key:
            logger.error("Cannot download GeoIP database: No license key provided")
            return False
            
        edition_id = f"GeoLite2-{db_type.upper()}" if db_type.lower() == 'asn' else f"GeoLite2-{db_type.capitalize()}"
        target_path = self.asn_db_path if db_type.lower() == 'asn' else self.country_db_path
        
        # Create a temporary file
        temp_dir = os.path.join(self.db_directory, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        tar_filename = f"{edition_id}.tar.gz"
        tar_path = os.path.join(temp_dir, tar_filename)
        
        try:
            # Download the file
            url = f"https://download.maxmind.com/app/geoip_download?edition_id={edition_id}&license_key={self.license_key}&suffix=tar.gz"
            logger.info(f"Downloading {edition_id} database...")
            
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(tar_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
                
            # Extract the database file
            logger.info(f"Extracting {edition_id} database...")
            with tarfile.open(tar_path, "r:gz") as tar:
                # Find the .mmdb file
                mmdb_file = None
                for member in tar.getmembers():
                    if member.name.endswith('.mmdb'):
                        mmdb_file = member
                        break
                
                if not mmdb_file:
                    logger.error(f"Could not find .mmdb file in {tar_filename}")
                    return False
                
                # Extract the file
                tar.extract(mmdb_file, path=temp_dir)
                
                # Move to the final location
                extracted_path = os.path.join(temp_dir, mmdb_file.name)
                shutil.move(extracted_path, target_path)
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            logger.info(f"Successfully downloaded and installed {edition_id} database")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {edition_id} database: {str(e)}")
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False
    
    def update_databases(self, force=False):
        """
        Check and update all databases if needed
        
        Args:
            force (bool): Force update even if not needed
            
        Returns:
            dict: Status of each database
        """
        status = self.check_databases()
        
        for db_type in ['asn', 'country']:
            if force or not status[db_type]['exists'] or status[db_type]['needs_update']:
                success = self.download_database(db_type)
                status[db_type]['updated'] = success
            else:
                logger.info(f"{db_type.upper()} database is up-to-date")
                status[db_type]['updated'] = False
        
        return status
    
    def get_database_info(self):
        """
        Get information about installed databases
        
        Returns:
            dict: Database information
        """
        db_info = {
            'asn': {
                'exists': os.path.exists(self.asn_db_path),
                'path': self.asn_db_path,
            },
            'country': {
                'exists': os.path.exists(self.country_db_path),
                'path': self.country_db_path,
            }
        }
        
        # Add file size and modification time
        for db_type in db_info:
            if db_info[db_type]['exists']:
                db_path = self.asn_db_path if db_type == 'asn' else self.country_db_path
                stats = os.stat(db_path)
                db_info[db_type]['size_mb'] = round(stats.st_size / (1024 * 1024), 2)
                db_info[db_type]['modified'] = datetime.fromtimestamp(stats.st_mtime).isoformat()
                
                # Create MD5 hash of the file for verification
                md5_hash = hashlib.md5()
                with open(db_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                db_info[db_type]['md5'] = md5_hash.hexdigest()
        
        return db_info

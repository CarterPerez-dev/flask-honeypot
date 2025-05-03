# honeypot/utils/generate_config.py

import secrets
import string
import os

def generate_password(length=16):
    """Generate a secure random password (letters and digits only)"""
    # Remove special characters from the alphabet
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_env_file(output_path='.env'):
    """Generate a secure .env file with random credentials"""
    # Check if file already exists
    if os.path.exists(output_path):
        overwrite = input(f"{output_path} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Generate secure values
    env_content = f"""# Honeypot Framework Configuration
# IMPORTANT: Keep this file secret and don't commit to version control!

# Core settings
SECRET_KEY="{secrets.token_hex(32)}"
DEBUG=False

# MongoDB credentials
MONGO_USER="honeypot_user"
MONGO_PASSWORD="{generate_password(20)}"

# Redis password
REDIS_PASSWORD="{generate_password(20)}"

# Admin dashboard password
HONEYPOT_ADMIN_PASSWORD="{generate_password(16)}"

# Other settings
HONEYPOT_RATE_LIMIT=15
HONEYPOT_RATE_PERIOD=60

HONEYPOT_DATA_DIRECTORY=/app/data

# Flask environment ('development' or 'production')
FLASK_ENV=production
"""

    with open(output_path, 'w') as f:
        f.write(env_content)
    
    print(f"Secure configuration generated at {output_path}")
    print("IMPORTANT: Keep this file secure and don't commit it to version control!")

if __name__ == "__main__":
    generate_env_file()

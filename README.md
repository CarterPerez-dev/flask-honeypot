# 🍯 Flask-Honeypot Framework

```
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥
🟥 ██╗  ██╗ ██████╗ ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ████████╗ 🟥
🟧 ██║  ██║██╔═══██╗████╗  ██║██╔════╝╚██╗ ██╔╝██╔══██╗██╔═══██╗╚══██╔══╝ 🟧
🟨 ███████║██║   ██║██╔██╗ ██║█████╗   ╚████╔╝ ██████╔╝██║   ██║   ██║    🟨
🟩 ██╔══██║██║   ██║██║╚██╗██║██╔══╝    ╚██╔╝  ██╔═══╝ ██║   ██║   ██║    🟩
🟦 ██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║   ██║     ╚██████╔╝   ██║    🟦
🟪 ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝    ╚═╝    🟪
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥
 ```

<p align="center">
  <strong>A comprehensive honeypot system for detecting, trapping, and analyzing unauthorized access attempts</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-technical-overview">Technical Overview</a> •
  <a href="#-honeypot-traps">Honeypot Traps</a> •
  <a href="#-admin-dashboard">Admin Dashboard</a> •
  <a href="#-integration">Integration</a> •
  <a href="#-docker-deployment">Docker Deployment</a> •
  <a href="#-security-considerations">Security</a> •
  <a href="#-license">License</a>
</p>


## Project Screenshots

### Click to view screenshots:

[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220546.png" width="100" alt="Screenshot 1">](#screenshot-1)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220613.png" width="100" alt="Screenshot 2">](#screenshot-2)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220712.png" width="100" alt="Screenshot 3">](#screenshot-3)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220719.png" width="100" alt="Screenshot 4">](#screenshot-4)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220750.png" width="100" alt="Screenshot 5">](#screenshot-5)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220821.png" width="100" alt="Screenshot 6">](#screenshot-6)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220840.png" width="100" alt="Screenshot 7">](#screenshot-7)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220859.png" width="100" alt="Screenshot 8">](#screenshot-8)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220911.png" width="100" alt="Screenshot 9">](#screenshot-9)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220933.png" width="100" alt="Screenshot 10">](#screenshot-10)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220946.png" width="100" alt="Screenshot 11">](#screenshot-11)
[<img src="https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20221012.png" width="100" alt="Screenshot 12">](#screenshot-12)







## 🔍 Features

Flask-Honeypot is a security monitoring tool designed to detect and analyze unauthorized access attempts by creating convincing decoys that attract and trap potential attackers.

- **Multiple honeypot trap types** - 20+ pre-built decoys including admin panels, WordPress, phpMyAdmin, file managers, and more
- **Interactive deceptive elements** - Clickable buttons, forms, fake file downloads, and simulated errors to keep attackers engaged
- **Rich attacker profiling** - Collect IPs, user agents, GeoIP data, ASN info, and behavioral patterns
- **Real-time Tor/proxy detection** - Identify attackers attempting to hide their true location
- **Advanced security analytics** - Visual dashboards showing attack patterns, geographic distribution, and threat levels
- **Auto-blocking capabilities** - Rate limiting and IP blocking with configurable thresholds
- **Detailed interaction logging** - Every click, form submission, and interaction attempt is recorded
- **Containerized deployment** - Quick setup with Docker and docker-compose
- **Scalable architecture** - MongoDB for storage and Redis for session management
- **MaxMind GeoIP integration** - Optional geographic and ASN tracking

## 🚀 Quick Start
--
## The fastest way to deploy (Docker):
---
### Option 1: Docker Deployment (Recommended for Production)

```bash
### Clone the repository
```bash
git clone https://github.com/CarterPerez-dev/honeypot-framework.git
cd honeypot-framework
```
### Set executable permissions for setup_honeypot.sh 
```bash
chmod +x setup_honeypot.sh
```
### Run the setup script
```bash
./setup_honeypot.sh
```

### This script will:
- Check dependencies (Python, Docker, Docker Compose)
- Create a Python virtual environment
- Install Flask-Honeypot
- Generate a secure configuration in `.env`
- Prompt for optional MaxMind license key


### Start the honeypot
```bash
docker-compose up --build -d
```

### That's it! Your honeypot is now running. Access the admin dashboard at:
```bash
http://your-server/honey/login
```
### If you set up https
```bash
https://your-server/honey/login
```

#### Use the admin password from your `.env` file (generated by the setup script, you can always change it).

## 📦 Installation
---
### Option 2: Python Package Installation

### If you want to integrate the honeypot into an existing Flask application:

```bash
pip install flask-honeypot=0.1.1
```

### Then in your Python code:

```python
from honeypot import create_honeypot_app

app = create_honeypot_app()

if __name__ == "__main__":
    app.run()
```

### Requirements

- Python 3.8+
- MongoDB 4.0+
- Redis 5.0+ (for session management)
- Docker & Docker Compose (for containerized deployment)
- (Optional) MaxMind GeoIP database license key

## ⚙️ Configuration

Configuration options can be set via:
1. Environment variables
2. The `.env` file
3. Direct parameters to `create_honeypot_app()`

### Key Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `SECRET_KEY` | Secret key for sessions | Randomly generated |
| `MONGO_URI` | MongoDB connection URI | `mongodb://localhost:27017/honeypot` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_PASSWORD` | Redis password | `None` |
| `HONEYPOT_ADMIN_PASSWORD` | Admin dashboard password | Required |
| `HONEYPOT_RATE_LIMIT` | Max requests per period | `15` |
| `HONEYPOT_RATE_PERIOD` | Rate limit period in seconds | `60` |
| `MAXMIND_LICENSE_KEY` | MaxMind GeoIP license key | `None` |
| `HONEYPOT_DATA_DIRECTORY` | Directory for data storage | `/app/data` |
| `FLASK_ENV` | Environment (`development`/`production`) | `production` |

Example `.env` file:
```
SECRET_KEY="f926dfdd9fffdafedd195ab8b30e60aa8157736475be9646c41b9b1994e47089"
MONGO_USER="supersecretstrongpassword123!"
MONGO_PASSWORD="Bigstrongpasswordyea112"
REDIS_PASSWORD="Ih9zfuUrgoxnir5qz"
HONEYPOT_ADMIN_PASSWORD="2WW6TUhgfdu3BkuApLA"
HONEYPOT_RATE_LIMIT=5
HONEYPOT_RATE_PERIOD=60
FLASK_ENV=production
HONEYPOT_DATA_DIRECTORY=/app/data
```

## 🔬 Technical Overview

Flask-Honeypot uses a Flask backend to serve deceptive content that appears legitimate to attackers while logging all interactions for security analysis.

### Structure

```bash
.
├── LICENSE
├── MANIFEST.in
├── README.md
├── examples
│   ├── App-js.py
│   ├── enhanced_admin_security.py
│   └── example_flask_integration.py
├── honeypot
│   ├── __init__.py
│   ├── _version.py
│   ├── backend
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── helpers
│   │   │   ├── __init__.py
│   │   │   ├── db_utils.py
│   │   │   ├── geoip_manager.py
│   │   │   ├── proxy_detector.py
│   │   │   └── unhackable.py
│   │   ├── middleware
│   │   │   ├── __init__.py
│   │   │   └── csrf_protection.py
│   │   ├── routes
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── honeypot.py
│   │   │   ├── honeypot_pages.py
│   │   │   └── honeypot_routes.py
│   │   └── templates
│   │       ├── honeypot
│   │       │   ├── admin-dashboard.html
│   │       │   ├── admin-login.html
│   │       │   ├── cloud-dashboard.html
│   │       │   ├── cms-dashboard.html
│   │       │   ├── cpanel-dashboard.html
│   │       │   ├── database-dashboard.html
│   │       │   ├── debug-console.html
│   │       │   ├── devops-dashboard.html
│   │       │   ├── ecommerce-dashboard.html
│   │       │   ├── filesharing-dashboard.html
│   │       │   ├── forum-dashboard.html
│   │       │   ├── framework-dashboard.html
│   │       │   ├── generic-login.html
│   │       │   ├── generic-page.html
│   │       │   ├── iot-dashboard.html
│   │       │   ├── mail-dashboard.html
│   │       │   ├── mobile-api.html
│   │       │   ├── monitoring-dashboard.html
│   │       │   ├── phpmyadmin-dashboard.html
│   │       │   ├── remote-access-dashboard.html
│   │       │   ├── shell.html
│   │       │   └── wp-dashboard.html
│   │       └── redirection
│   │           ├── step1.html
│   │           ├── step10.html
│   │           ├── step11.html
│   │           ├── step12.html
│   │           ├── step13.html
│   │           ├── step14.html
│   │           ├── step15.html
│   │           ├── step2.html
│   │           ├── step3.html
│   │           ├── step4.html
│   │           ├── step5.html
│   │           ├── step6.html
│   │           ├── step7.html
│   │           ├── step8.html
│   │           └── step9.html
│   ├── cli.py
│   ├── config
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── database
│   │   ├── models.py
│   │   ├── mongo-init.js
│   │   └── mongodb.py
│   ├── deploy_templates
│   │   ├── Dockerfile.backend.template
│   │   ├── Dockerfile.nginx.template
│   │   ├── __init__.py
│   │   ├── dev-nginx.conf.template
│   │   ├── docker-compose.dev.yml.template
│   │   ├── docker-compose.yml.template
│   │   ├── dot_env.example
│   │   └── nginx
│   │       ├── nginx.conf.template
│   │       └── sites-enabled
│   │           └── proxy.conf.template
│   ├── frontend
│   │   ├── README.md
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   └── src
│   │       ├── App.js
│   │       ├── components
│   │       │   ├── JsonSyntaxHighlighter.js
│   │       │   ├── LoadingPlaceholder.js
│   │       │   └── csrfHelper.js
│   │       ├── index.css
│   │       ├── index.js
│   │       ├── reportWebVitals.js
│   │       ├── static
│   │       │   ├── css
│   │       │   │   ├── HoneypotTab.css
│   │       │   │   ├── HtmlInteractionsTab.css
│   │       │   │   ├── JsonSyntaxHighlighter.css
│   │       │   │   ├── LoadingPlaceholder.css
│   │       │   │   ├── admin.css
│   │       │   │   └── login.css
│   │       │   ├── js
│   │       │   │   ├── admin.js
│   │       │   │   └── login.js
│   │       │   └── tabs
│   │       │       ├── HoneypotTab.js
│   │       │       ├── HtmlInteractionsTab.js
│   │       │       └── OverviewTab.js
│   │       └── utils
│   │           └── dateUtils.js
│   └── utils
│       └── generate_config.py
├── mongo-init.js
├── pyproject.toml
└── setup_honeypot.sh
```
```
🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦
🟦                                              🟦
🟦  ╔═╗╦  ╔═╗╔═╗╦╔═  ╦ ╦╔═╗╔╗╔╔═╗╦ ╦╔═╗╔═╗╔╦╗  🟦
🟦  ╠╣ ║  ╠═╣╚═╗╠╩╗  ╠═╣║ ║║║║║╣ ╚╦╝╠═╝║ ║ ║   🟦
🟩  ╚  ╩═╝╩ ╩╚═╝╩ ╩  ╩ ╩╚═╝╝╚╝╚═╝ ╩ ╩  ╚═╝ ╩   🟩
🟩                                              🟩
🟩          ⚗️ Trap • Monitor • Analyze ⚗️       🟩
🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩
```


### Core Components

- **Flask Backend**: Serves honeypot pages and logs interactions
- **MongoDB**: Stores interaction data, attacker profiles, and logs
- **Redis**: Manages secure sessions for the admin interface
- **GeoIP Detection**: Identifies attacker locations (requires MaxMind)
- **Proxy Detector**: Identifies Tor exit nodes and known proxies

# 🕸️ Honeypot Traps: Comprehensive Analysis

The Flask-Honeypot framework includes a sophisticated collection of deceptive web interfaces designed to attract, engage, and monitor potential attackers. These traps not only collect credentials but track every interaction, mouse movement, and keyboard input to build comprehensive profiles of attacker behavior.

## Admin Interface Traps
--
### 🔒 Admin Login Portal

The admin login portal (`admin-login.html`) serves as the first line of defense and intelligence gathering:

- **Adaptive Authentication Challenges**: The portal presents initially simple login forms that become increasingly complex with each failed attempt, introducing impossible CAPTCHAs after the second failure
- **Credential Harvesting**: All submitted credentials are logged along with metadata about the user's session
- **Behavioral Analysis Features**: The system tracks mouse movements, typing patterns, and interaction frequency
- **SQL Injection Detection**: Real-time analysis of input fields for SQL patterns like `' OR '1'='1` with warnings that make attackers believe they've been detected
- **Impossible CAPTCHA System**: After multiple failures, the CAPTCHA text purposely moves around the screen or uses unreadable characters from the set of pre-defined patterns like `l1Il1lI1l1Il` or `0oO0oO0oO0o`
- **Fake System Alerts**: Security notifications appear randomly to create pressure and encourage hasty behavior
- **Password Reset Trap**: A password reset option that simulates email sending but never completes, harvesting additional information
- **Two-Factor Authentication Simulation**: Offers 2FA that always fails after collecting the verification code
- **Keyboard Input Scrambling**: Randomly maps keyboard input to different characters while displaying fake "keylogger protection" messages

### 🖥️ Admin Dashboard

The admin dashboard honeypot (`admin-dashboard.html`) is designed to resemble legitimate system administration interfaces:

- **Interactive Statistics Panels**: Displays fake system statistics with real-time updating values that never complete their processes
- **User Management System**: Presents tables of fictitious users with sensitive-looking data
- **Security Alert Section**: Shows fake security notifications that highlight the current session as suspicious
- **Command Terminal Emulation**: Provides a simulated terminal that accepts and responds to commands while logging everything
- **Crypto Mining Simulation**: A fake cryptocurrency miner that appears to be running in the background
- **Popup Storm Trigger**: Actions that generate multiple difficult-to-close popup windows
- **Fake File Downloads**: Options to download "sensitive" data that actually contain tracking content
- **BSOD (Blue Screen) Simulation**: System crash scenarios triggered by certain actions
- **Admin Chat Simulation**: A chat interface where fictitious administrators discuss the "intrusion" in real-time
- **Vanishing UI Elements**: Buttons that move away from the cursor when approached
- **Screen Flicker Effects**: Random screen glitches to create tension and urgency
- **Encryption Ransom Simulation**: A sequence that simulates ransomware encryption of system files
- **Impossible Verification Puzzles**: Mathematical challenges that increase in difficulty and are designed to be unsolvable

### 🛒 E-commerce Administration Panel

The e-commerce dashboard honeypot (`ecommerce-dashboard.html`) targets attackers looking for payment processing systems:

- **Store Performance Metrics**: Fake sales data, revenue figures, and customer statistics
- **Payment Gateway Integration**: Seemingly functional payment processing controls
- **Customer Database Access**: Tables of fictional customers with options to view payment details
- **Order Processing System**: Simulated order management with transaction logs
- **Payment Security Verification**: CAPTCHA systems and security checks for accessing payment data
- **Cryptocurrency Payment Portal**: Bitcoin wallet integration that logs entered wallet addresses
- **Fraud Detection System**: Interactive scanning tools that simulate security processes
- **Sales Analytics**: Graphs and metrics showing store performance
- **API Key Management**: Exposed payment gateway API keys that log when they're copied
- **Customer Account Management**: Password reset and account modification options
- **Store Settings Panel**: Configuration options for the fake store

## Command Line Interfaces

### 🖲️ Terminal Shell

The shell honeypot (`shell.html`) creates a convincing terminal environment:

- **Virtual File System**: Complete simulated Linux directory structure with realistic paths and permissions
- **Command Recognition**: Responds to over 40 standard Linux commands including `ls`, `cd`, `cat`, `pwd`, `grep`, and more
- **Sensitive File Placement**: Strategic placement of files like `.bash_history`, SSH keys, and configuration files with fake credentials
- **Command History Tracking**: All entered commands are recorded with timestamps and session data
- **Password Files**: Accessible `/etc/passwd` with restricted `/etc/shadow` access to appear authentic
- **Nested Directory Mazes**: Deep directory structures that encourage exploration while monitoring navigation patterns
- **System Logs**: Fake log files in `/var/log/` containing login attempts and system events
- **Web Server Configuration**: Apache configuration files and access logs
- **Backup Scripts**: Seemingly useful backup and security scan scripts
- **Matrix Visual Effect**: An interactive "matrix" command that creates engaging visual effects
- **Easter Eggs**: Hidden commands like `cowsay` and `fortune` that encourage prolonged interaction

## Multi-Step Verification Traps

### 🔑 Progressive Access System

The multi-step redirection system (`step1.html` through `step15.html`) creates a convincing security gauntlet:

- **Sequential Security Layers**: A series of verification steps that simulate increasing levels of system access
- **Biometric Authentication Simulation**: Fake fingerprint scanning with progress indicators
- **Security Code Entry**: Emergency backup codes that never actually work
- **Progress Trackers**: Visual indicators showing verification progress that never fully completes
- **Session Timeout Features**: Simulated security timeouts that reset progress
- **Hardware Security Key Verification**: Requests for physical security key insertion
- **Executive Approval Simulation**: Fake waiting for administrator approval
- **Critical Warning Banners**: Red alert notifications about restricted system areas
- **Redirection Chains**: Each successful step leads to another security challenge
- **Verification Failure Scenarios**: Programmed to eventually fail regardless of input
- **IP Address Logging**: Displays the visitor's actual IP address to create urgency

## Technical Implementation Details

These honeypot traps are engineered with sophisticated JavaScript and CSS to create convincing interactive experiences:

- **Real-Time Input Analysis**: Every keystroke in form inputs is monitored and analyzed
- **Mouse Tracking**: Records mouse movements, hesitations, and interaction patterns
- **Randomized Responses**: System responses vary to appear more authentic and prevent pattern recognition
- **Selective Failure Points**: Strategic points where the system always fails regardless of input
- **Timing Analysis**: Monitors time spent on pages and between interactions
- **Browser Fingerprinting**: Collects detailed browser, device, and system information
- **WebSocket Simulations**: Fake real-time connections that appear to be communicating with servers
- **Local Storage Manipulation**: Creates persistent tracking even after page refreshes
- **CSS Animation Effects**: Visual cues that create urgency or induce specific behaviors
- **Mobile Responsiveness**: Traps work on all device types with adaptive interfaces
- **Keyboard Event Interception**: Captures all keyboard inputs including keyboard shortcuts
- **HTTP Request Logging**: Tracks all network requests made during interaction

## Additional Specialized Trap Types

Beyond the core traps detailed above, the framework includes specialized honeypots for various targets:

- **Database Administration Interfaces**: 
  - MySQL, PostgreSQL, and MongoDB admin panels with query execution capabilities
  - Database browsing interfaces with fake tables and records
  - Backup and restore functionality that logs all interaction

- **Content Management Systems**: 
  - WordPress, Joomla, Drupal admin panels with plugin installation pages
  - Theme customization interfaces with file upload capabilities
  - User management and content editing sections

- **Network Device Interfaces**:
  - Router configuration pages with network settings
  - Firewall management interfaces with rule editing
  - Switch and access point dashboards

- **Development Tools**:
  - Jenkins CI/CD pipelines with build histories
  - GitLab/GitHub repository browsers with commit logs
  - Deployment management interfaces

- **Remote Access Systems**:
  - VPN administration portals with user management
  - RDP/VNC connection interfaces
  - SSH key management pages

## 📊 Comprehensive Admin Dashboard for Security Teams

The actual administrator dashboard (for security teams monitoring the honeypots) provides extensive analytical capabilities:

- **Real-Time Activity Monitor**: Live feed of all honeypot interactions across all traps
- **Interaction Timeline**: Chronological view of attacker actions with playback capabilities
- **Geographic Attribution**: IP-based location mapping with ASN information
- **Behavioral Analysis**: Pattern recognition of common attack methodologies
- **Credential Collection**: Database of attempted username/password combinations
- **Command Analysis**: Statistics on most frequently attempted commands
- **Session Replays**: Full visual reconstruction of attacker sessions
- **Attacker Profiling**: Machine learning-based categorization of attack patterns
- **Threat Intelligence Integration**: Cross-reference with known threat actor TTPs
- **Alert Configuration**: Customizable triggers for specific high-risk behaviors
- **Export Capabilities**: Data export in multiple formats for further analysis
- **Tor Exit Node Detection**: Identification of connections from anonymizing networks

The combination of these deceptive interfaces with comprehensive monitoring creates an effective system for detecting, analyzing, and understanding unauthorized access attempts while gathering actionable threat intelligence.
Each interaction is timestamped, geolocated, and stored for analysis.

### Additional Trap Types

- **Database Admin**: MySQL, MongoDB, Redis interfaces
- **File Managers**: Cloud storage and file sharing
- **Email Systems**: Webmail interfaces
- **CMS Systems**: Joomla, Drupal, and other CMS platforms
- **E-commerce**: Shopify, WooCommerce admin panels
- **Network Devices**: Router configuration panels
- **Remote Access**: SSH, RDP, VNC interfaces
- **Development Tools**: Jenkins, GitLab, etc.
- **API Endpoints**: Simulated REST APIs

## 📊 Admin Dashboard

The admin dashboard provides security staff with detailed insights:

- **Overview**: Summary of recent activity
- **Detailed Stats**: In-depth analysis of attack patterns
- **Geographic View**: Map showing attack origins
- **Threat Analysis**: Categorization of attack types
- **Raw Logs**: Complete interaction records
- **System Health**: Monitoring of honeypot operation

## 🔄 Integration

### Integration with Existing Flask Applications

```python
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from honeypot import create_honeypot_app

# Create your main application
main_app = Flask(__name__)

@main_app.route('/')
def index():
    return "My secure application"

# Create the honeypot application
honeypot_app = create_honeypot_app()

# Mount the honeypot at a specific URL prefix
application = DispatcherMiddleware(main_app, {
    '/security': honeypot_app  # Maps to /security/* URLs
})

# For direct Flask execution
if __name__ == "__main__":
    # Create a WSGI app wrapper
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, application, use_reloader=True)
```

### Advanced Integration

For more advanced integration options (such as selective blueprint registration or frontend integration), see the `examples/` directory.

## 🐳 Docker Deployment

For production deployments, use the Docker configuration:

```bash
# Generate deployment files (if you haven't run setup_honeypot.sh)
python -m honeypot.cli init

# Start in production mode
docker-compose up --build -d

# For development mode with hot reloading
docker-compose -f docker-compose.dev.yml up --build -d
```

The Docker deployment includes:
- Nginx web server
- Flask backend
- MongoDB database
- Redis for session management

## 🔐 Security Considerations

### Admin Security

- **Access Restriction**: Limit admin dashboard access to trusted IPs
- **Strong Authentication**: Use complex passwords for the admin interface
- **HTTPS**: Always use SSL/TLS in production, refer to documentation for HTTPS
- **Regular Rotation**: Change admin credentials frequently
- **VPN Access**: Consider placing the admin interface behind a VPN

### Honeypot Placement

- **Segregation**: Run honeypots on separate infrastructure from production systems
- **Firewall Rules**: Implement strict firewall rules for honeypot traffic
- **Resource Limits**: Prevent honeypots from being used for further attacks
- **Legal Compliance**: Ensure your honeypot deployment complies with local laws

### Enhanced Security Module

For additional security, consider using the enhanced security module (refer to examples documentation):

```python
from honeypot import create_honeypot_app
from examples.enhanced_admin_security import setup_enhanced_security

app = create_honeypot_app()
app = setup_enhanced_security(app)
```

This provides:
- IP whitelisting
- Enhanced brute force protection
- Security headers
- Advanced session protection

## 📖 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
__  __                                        __ 
   / / / /___  ____  ___  __  ______  ____  ____/ /_
  / /_/ / __ \/ __ \/ _ \/ / / / __ \/ __ \/ __  __/
 / __  / /_/ / / / /  __/ /_/ / /_/ / /_/ / /_/ /_  
/_/ /_/\____/_/ /_/\___/\__, / .___/\____/\__/\__/  
                       /____/_/                     
    🍯 CATCH THE HACKERS 🍯
    
```

For questions, contributions, or support, please open an issue on GitHub.

### Full Screenshots

#### Screenshot 1
![Screenshot 1](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220546.png)

#### Screenshot 2
![Screenshot 2](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220613.png)

#### Screenshot 3
![Screenshot 3](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220712.png)

#### Screenshot 4
![Screenshot 4](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220719.png)

#### Screenshot 5
![Screenshot 5](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220750.png)

#### Screenshot 6
![Screenshot 6](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220821.png)

#### Screenshot 7
![Screenshot 7](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220840.png)

#### Screenshot 8
![Screenshot 8](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220859.png)

#### Screenshot 9
![Screenshot 9](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220911.png)

#### Screenshot 10
![Screenshot 10](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220933.png)

#### Screenshot 11
![Screenshot 11](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20220946.png)

#### Screenshot 12
![Screenshot 12](https://raw.githubusercontent.com/CarterPerez-dev/CertGames-Core/main/Stack/Architecture/Screenshot%202025-05-02%20221012.png)

```
┌─────────────────────────────────────────────┐
│                                             │
│  [🔴] HONEYPOT v1.0.2                       │
│  ┌───────────────────────────────────────┐  │
│  │ █ █ █▀█ █▄ █ █▀▀ █▄█ █▀█ █▀█ ▀█▀     │  │
│  │ █▀█ █ █ █ ▀█ █▀▀  █  █▀▀ █ █  █      │  │
│  │ ▀ ▀ ▀▀▀ ▀  ▀ ▀▀▀  ▀  ▀   ▀▀▀  ▀      │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  [*] SERVICE STARTED                        │
│  [*] LISTENING FOR CONNECTIONS...           │
│                                             │
└─────────────────────────────────────────────┘
```

@CarterPerez-dev



# 🍯 Flask-Honeypot

<p align="center">
  <img src="docs/images/honeypot-logo.png" alt="Honeypot Framework Logo" width="200"/>
</p>

<p align="center">
  <strong>A comprehensive honeypot system for detecting and analyzing unauthorized access attempts</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-technical-overview">Technical Overview</a> •
  <a href="#-honeypot-pages">Honeypot Pages</a> •
  <a href="#-integration">Integration</a> •
  <a href="#-development">Development</a> •
  <a href="#-docker-deployment">Docker Deployment</a> •
  <a href="#-security-considerations">Security</a> •
  <a href="#-license">License</a>
</p>

## 🔍 Features

Honeypot Framework is a fully-featured security monitoring tool designed to detect and analyze unauthorized access attempts through deliberately exposed decoy services.

- **Multiple honeypot types** (admin panels, WordPress, phpMyAdmin, etc.)
- **Interactive admin dashboard** with real-time monitoring
- **Enhanced threat detection** with Tor/proxy identification
- **GeoIP tracking** for attacker location identification
- **Detailed logging** of all interaction attempts
- **Credential harvesting detection**
- **Security visualizations** with multiple chart types
- **Rate limiting** and IP blocking for attack mitigation
- **Containerized deployment** via Docker
- **Highly customizable** and extensible architecture

## 🔧 Installation

### Using pip (Recommended)

```bash
pip install flask-honeypot
```

### From Source

```bash
git clone https://github.com/username/honeypot-framework.git
cd honeypot-framework
pip install -e .
```

### Requirements

- Python 3.8+
- MongoDB
- Redis (for session management)
- (Optional) MaxMind GeoIP database

## 🚀 Quick Start

### Basic Setup

```python
from honeypot import create_honeypot_app

app = create_honeypot_app()

if __name__ == "__main__":
    app.run(debug=True)
```

### Docker Deployment

For production deployments, use the included Docker configuration:

```bash
# Generate deployment files
python -m honeypot.cli init

# Configure environment variables
cp .env.example .env
nano .env  # Edit configuration values

# Start the honeypot
docker-compose up -d
```

### Accessing the Admin Dashboard

Once running, access the admin dashboard at:

```
http://your-server/honey/login
```

Use the admin password defined in your `.env` file.

## ⚙️ Configuration

Configuration can be provided through environment variables, a `.env` file, or directly in code:

```python
from honeypot import create_honeypot_app

app = create_honeypot_app({
    "SECRET_KEY": "your-secure-key",
    "MONGO_URI": "mongodb://localhost:27017/honeypot",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": 6379,
    "REDIS_PASSWORD": "your-redis-password",
    "HONEYPOT_RATE_LIMIT": 5,
    "HONEYPOT_RATE_PERIOD": 60,
    "HONEYPOT_ADMIN_PASSWORD": "your-secure-admin-password",
    "MAXMIND_LICENSE_KEY": "your-maxmind-license-key"  # Optional, for GeoIP
})
```

### Key Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Randomly generated |
| `MONGO_URI` | MongoDB connection URI | `mongodb://localhost:27017/honeypot` |
| `REDIS_HOST` | Redis host for session storage | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_PASSWORD` | Redis password | `None` |
| `HONEYPOT_RATE_LIMIT` | Max requests per period | `15` |
| `HONEYPOT_RATE_PERIOD` | Rate limit period in seconds | `60` |
| `HONEYPOT_ADMIN_PASSWORD` | Admin dashboard password | Required |
| `FLASK_ENV` | Environment (`development` or `production`) | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAXMIND_LICENSE_KEY` | MaxMind GeoIP database license key | `None` |

## 🔬 Technical Overview

Honeypot Framework integrates Flask (backend) and React (frontend) to create a sophisticated honeypot system capable of detecting and analyzing unauthorized access attempts.

![Architecture Diagram](docs/images/architecture.png)

### Core Components

- **Flask Backend**: Handles requests, logs interactions, and provides API endpoints for the admin dashboard
- **MongoDB**: Stores interaction logs, scan attempts, and security analytics
- **Redis**: Manages secure sessions for the admin interface
- **React Frontend**: Provides an interactive admin dashboard for monitoring and analysis
- **GeoIP Detection**: Identifies attacker geographical locations and ASN information
- **Proxy Detection**: Identifies Tor exit nodes and proxy services

### Data Flow

1. An attacker targets a honeypot endpoint
2. The request is intercepted and logged with extensive metadata
3. The attacker is redirected to a fake html page with variuous (trolls, fake stuff ect ect hwo shoudl i say this?)
4. Interaction details are stored in MongoDB
5. Real-time analytics are updated
6. Security staff can monitor activities via the admin dashboard

## 📊 Admin Dashboard

The admin dashboard provides a comprehensive view of honeypot activities:

- **Overview**: High-level statistics and system status
- **Honeypot Tab**: Detailed analysis of scan attempts and interactions
- **HTML Interactions Tab**: Focuses on client-side interactions with deceptive pages

![Dashboard Screenshot](docs/images/dashboard.png)

## 🕸️ Honeypot Pages

The framework includes a wide variety of deceptive pages designed to attract and track different types of unauthorized access attempts:

### Administrative Interfaces

- **WordPress Admin**: Fake WordPress login and admin panels
- **phpMyAdmin**: Database administration honeypot
- **cPanel**: Hosting control panel simulation
- **General Admin Panels**: Generic admin login forms and dashboards

### CMS and E-commerce

- **Additional CMS Platforms**: Joomla, Drupal, etc.
- **E-commerce Admin**: Shopify, WooCommerce, etc.
- **Forums**: phpBB, vBulletin, etc.

### Technical Services

- **Database Endpoints**: MySQL, MongoDB, Redis, etc.
- **Mail Services**: Webmail, SMTP, etc.
- **Remote Access**: SSH, VNC, RDP honeypots
- **IoT Devices**: Camera systems, routers, etc.
- **DevOps Tools**: Jenkins, GitLab, etc.

### Development and Debug

- **Web Frameworks**: Django, Rails, Laravel, etc.
- **Debug Consoles**: Log viewers, debug panels, etc.
- **Backdoors and Shells**: Simulated backdoors for detecting intrusion attempts

Each honeypot type is carefully crafted to appear legitimate while logging interactions for security analysis.

## 🔄 Integration

### Integration with Existing Flask Application

```python
from flask import Flask, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from honeypot import create_honeypot_app

# Create your main application
main_app = Flask(__name__)

@main_app.route('/')
def index():
    return render_template('index.html', title="My Secure Application")

# Create the honeypot application
honeypot_app = create_honeypot_app()

# Mount the honeypot at a specific URL prefix
application = DispatcherMiddleware(main_app, {
    '/security': honeypot_app  # Map to /security/* URLs
})

# For direct Flask execution
if __name__ == "__main__":
    # Create a WSGI app that wraps the DispatcherMiddleware
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, application, use_reloader=True)
```

### Integration with Existing React Application

```jsx
// In your App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Import your existing components
import HomePage from './components/HomePage';
import ProductsPage from './components/ProductsPage';

// Import the honeypot components
import HoneypotLogin from './honeypot/Login';
import HoneypotDashboard from './honeypot/Dashboard';

const App = () => {
  return (
    <Router>
      <Routes>
        {/* Your main application routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/products" element={<ProductsPage />} />
        
        {/* Honeypot admin routes */}
        <Route path="/security/login" element={<HoneypotLogin />} />
        <Route path="/security/dashboard/*" element={<HoneypotDashboard />} />
      </Routes>
    </Router>
  );
};

export default App;
```

See the `examples/` directory for complete integration examples.

## 🛠️ Development

### Local Development Setup

1. Clone the repository:

```bash
git clone https://github.com/username/honeypot-framework.git
cd honeypot-framework
```

2. Set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:

```bash
pip install -e ".[dev]"
```

4. Run the development server:

```bash
python -m honeypot.cli run
```

### Using Docker for Development

The project includes a development docker-compose file:

```bash
docker-compose -f docker-compose.dev.yml up
```

This will start:
- The Flask backend with hot reloading
- The React frontend with hot reloading
- MongoDB
- Redis

### Project Structure

```
honeypot/
├── backend/           # Flask backend
│   ├── app.py         # Main application factory
│   ├── helpers/       # Utility functions
│   ├── middleware/    # CSRF and other middleware
│   └── routes/        # API and honeypot routes
├── config/            # Configuration management
├── database/          # Database models and connections
├── deploy_templates/  # Docker and deployment templates
├── frontend/          # React frontend
│   ├── public/        # Static assets
│   └── src/           # React source code
└── utils/             # Utility scripts
```

## 🐳 Docker Deployment

For production deployments, the framework includes complete Docker configuration.

### Standard Deployment

```bash
# Generate deployment files
python -m honeypot.cli init

# Configure environment variables
cp .env.example .env
nano .env  # Edit configuration values

# Start the honeypot
docker-compose up -d
```

This will start:
- Nginx for serving the frontend and proxying API requests
- The honeypot backend
- MongoDB for data storage
- Redis for session management

### Custom Deployment

For advanced customization, you can modify the generated Dockerfiles and docker-compose.yml files.

## 🔐 Security Considerations

### Admin Dashboard Security

- Access to the admin dashboard should be restricted to trusted IPs
- Use strong passwords for the admin interface
- Consider placing the admin interface behind a VPN
- Regularly rotate admin credentials
- Enable HTTPS for all connections

### Honeypot Data Handling

- The honeypot may collect potentially sensitive information
- Review and handle logs according to your privacy policy
- Consider legal implications before deploying in production
- Do not use the honeypot to engage in entrapment

### Enhanced Security Module

The framework includes an optional enhanced security module that adds:
- IP whitelisting
- Multi-factor authentication
- Advanced session protection
- Brute force protection
- Enhanced audit logging

To enable:

```python
from honeypot import create_honeypot_app
from honeypot.security import setup_enhanced_security

app = create_honeypot_app()
app = setup_enhanced_security(app)
```

## 📖 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- MaxMind for GeoIP data
- Flask and React communities
- All contributors to this project

## 📧 Contact

For questions, issues, or contributions, please open an issue on GitHub or contact the maintainers at support@example.com.

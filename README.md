# Honeypot Framework

A comprehensive honeypot system for detecting and analyzing unauthorized access attempts. This framework provides both backend (Flask) and frontend (React) components for a complete honeypot solution.
---
## Features

- Multiple honeypot types (admin panels, WordPress, phpMyAdmin, etc.)
- Interactive admin dashboard for monitoring activities
- C2 (Command and Control) server simulation
- Detailed logging of all interactions
- GeoIP-based attacker information
- Rate limiting and security protections
- Docker support for easy deployment
----
## Installation

```bash
pip install honeypot-framework
```
----
## Quick Start

```python
from honeypot import create_honeypot_app

app = create_honeypot_app()

if __name__ == "__main__":
    app.run(debug=True)
```
----
## Configuration

Configuration can be provided through environment variables, a .env file, or directly in the code:

```python
from honeypot import create_honeypot_app

app = create_honeypot_app({
    "SECRET_KEY": "your-secure-key",
    "MONGO_URI": "mongodb://localhost:27017/honeypot",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": 6379,
    "REDIS_PASSWORD": "your-redis-password",
    "HONEYPOT_RATE_LIMIT": 5,
    "HONEYPOT_RATE_PERIOD": 60
})
```

## Docker Deployment

See the examples/full_deployment directory for a complete Docker Compose setup.

## Advanced Usage

### Integration with Existing Flask Application

```python
from flask import Flask
from honeypot import create_honeypot_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

main_app = Flask(__name__)
honeypot_app = create_honeypot_app()

application = DispatcherMiddleware(main_app, {
    '/security': honeypot_app
})
```

### Custom Templates

You can customize the honeypot templates by setting the `HONEYPOT_TEMPLATES_PATH` configuration value:

```python
app = create_honeypot_app({
    "HONEYPOT_TEMPLATES_PATH": "/path/to/your/templates"
})
```


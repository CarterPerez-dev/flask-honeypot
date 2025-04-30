# examples/custom_config.py
from honeypot import create_honeypot_app
import os

# Set environment variables
os.environ["REDIS_HOST"] = "my-redis-server"
os.environ["MONGO_URI"] = "mongodb://user:password@my-mongo-server:27017/honeypot"

# Create a honeypot app with custom configuration
app = create_honeypot_app({
    "HONEYPOT_RATE_LIMIT": 10,
    "HONEYPOT_RATE_PERIOD": 30,
    "SECRET_KEY": "my-secure-key-for-production"
})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

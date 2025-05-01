# examples/simple_honeypot.py
from honeypot import create_honeypot_app

# Create a default honeypot app
app = create_honeypot_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

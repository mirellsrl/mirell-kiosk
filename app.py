# app.py
"""Mirell Kiosk - Main Flask application"""
from flask import Flask, render_template, send_from_directory, make_response
from dotenv import load_dotenv
import os
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Load environment variables at startup
load_dotenv()

# Verify environment variables
if not os.getenv('USER_KEY') or not os.getenv('ACCESS_TOKEN'):
    raise ValueError("Missing required environment variables. Check your .env file")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "reO0jZmUgFCO0g3fy0wAbsYyXHN3OsJD"  # Required for session management

# Configure session for PWA compatibility
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True for HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Allow JavaScript access for PWA
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Better PWA compatibility

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.route('/healthz')
def health():
    """Health check endpoint"""
    return "OK"

@app.route('/wakeup')
def wakeup():
    """Wake up endpoint for keeping the service alive"""
    logging.info("System is woken up")
    return "I'm awake!"

@app.route('/static/js/sw.js')
def sw():
    """Service worker route with correct content type"""
    response = make_response(
        send_from_directory('static/js', 'sw.js')
    )
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.route('/favicon.ico')
def favicon():
    """Favicon endpoint"""
    return send_from_directory(
        os.path.join(app.root_path, 'static/images'),
        'favicon.png', 
        mimetype='image/vnd.microsoft.icon'
    )

# ============================================================================
# ROUTE BLUEPRINTS
# ============================================================================

# Register main routes
from routes.main import register_main_routes
register_main_routes(app)

# Register fiera blueprint
from routes.fiera import fiera_bp
app.register_blueprint(fiera_bp)

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    logging.info("Starting Mirell Kiosk application")
    app.run(debug=True)

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, session
from flask_login import LoginManager, current_user
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the database
db.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/stable-login'

@app.route("/")
def home():
    return render_template('clean_landing.html')

@app.after_request
def add_cache_control_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Response-Timestamp'] = datetime.utcnow().isoformat() + 'Z'
    return response

@app.route("/test-basic")
def test_basic():
    print("TEST-BASIC ROUTE HIT - This should appear in logs")
    app.logger.info("test-basic route was accessed successfully")
    return "✅ Basic test route works!"

@app.route("/cache-test")
def cache_test():
    print("🔍 CACHE TEST ROUTE HIT - Direct Flask route")
    app.logger.info("cache-test route was accessed successfully")
    timestamp = datetime.utcnow().isoformat()
    return f"""
    <h1>🔍 CACHE TEST SUCCESS</h1>
    <p><strong>Timestamp:</strong> {timestamp}</p>
    <p><strong>Route:</strong> Direct Flask route (not blueprint)</p>
    <p><strong>Headers:</strong> Cache control headers should be applied via @after_request</p>
    <p><strong>Test:</strong> Refresh this page - timestamp should change each time</p>
    <hr>
    <p>If you see this message with a fresh timestamp, cache headers are working!</p>
    """

# Basic login required decorator without error handling
def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect('/stable-login')
        return f(*args, **kwargs)
    return decorated_view

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# Register ONLY onboarding blueprint for clean testing
from onboarding_routes import onboarding_bp
app.register_blueprint(onboarding_bp, url_prefix='/onboarding')
app.logger.info("Onboarding blueprint registered successfully")

# Create database tables
with app.app_context():
    import models
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
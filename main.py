"""
Clean production version of Dear Teddy - eliminates blueprint conflicts
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.INFO)

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

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@app.after_request
def add_cache_control_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Response-Timestamp'] = datetime.utcnow().isoformat() + 'Z'
    return response

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# Register ONLY essential blueprints - eliminating conflicts
app.logger.info("Registering core blueprints only...")

# Core onboarding
try:
    from onboarding_routes import onboarding_bp
    app.register_blueprint(onboarding_bp, url_prefix='/onboarding')
    app.logger.info("Core onboarding registered")
except ImportError as e:
    app.logger.warning(f"Onboarding not available: {e}")

# Core authentication
try:
    from login_routes import login_bp
    app.register_blueprint(login_bp, url_prefix='/auth')
    app.logger.info("Core authentication registered")
except ImportError:
    app.logger.warning("Authentication routes not available")

# Main application routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return "Dear Teddy - Mental Wellness App<br><a href='/onboarding/debug'>Test Onboarding</a>"

@app.route('/dashboard')
@login_required  
def dashboard():
    return "Welcome to your dashboard!"

@app.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "blueprints": "core_only"
        }, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

# Create database tables
with app.app_context():
    try:
        import models
        db.create_all()
        app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Database error: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
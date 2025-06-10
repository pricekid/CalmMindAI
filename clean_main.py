"""
Clean production version of Dear Teddy - Core functionality only
This eliminates blueprint conflicts and focuses on essential features
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
    """Prevent caching issues"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Response-Timestamp'] = datetime.utcnow().isoformat() + 'Z'
    return response

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# Register ONLY essential blueprints
try:
    # Core authentication
    from login_routes import login_bp
    app.register_blueprint(login_bp, url_prefix='/auth')
    app.logger.info("✅ Authentication blueprint registered")
except ImportError:
    app.logger.warning("⚠️ Login routes not available")

try:
    # Main journal functionality
    from journal_routes import journal_bp
    app.register_blueprint(journal_bp, url_prefix='/journal')
    app.logger.info("✅ Journal blueprint registered")
except ImportError:
    app.logger.warning("⚠️ Journal routes not available")

try:
    # Onboarding flow
    from onboarding_routes import onboarding_bp
    app.register_blueprint(onboarding_bp, url_prefix='/onboarding')
    app.logger.info("✅ Onboarding blueprint registered")
except ImportError:
    app.logger.warning("⚠️ Onboarding routes not available")

try:
    # Admin functionality (single implementation)
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.logger.info("✅ Admin blueprint registered")
except ImportError:
    app.logger.warning("⚠️ Admin routes not available")

# Core routes
@app.route('/')
def index():
    """Landing page with proper user routing"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Main user dashboard"""
    try:
        from models import JournalEntry
        recent_entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).limit(5).all()
        return render_template('dashboard.html', entries=recent_entries)
    except Exception as e:
        app.logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', entries=[])

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        db.session.execute('SELECT 1')
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }, 200
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors gracefully"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Create database tables
with app.app_context():
    try:
        import models
        db.create_all()
        app.logger.info("✅ Database tables created successfully")
    except Exception as e:
        app.logger.error(f"❌ Database initialization failed: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
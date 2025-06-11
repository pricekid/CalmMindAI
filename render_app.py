import os
import logging
from flask import Flask, url_for, redirect, request, flash, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user, login_required as original_login_required
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_session import Session
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()
mail = Mail()
sess = Session()

# Create the app
app = Flask(__name__)

# Ensure a strong secret key for sessions
if os.environ.get("SESSION_SECRET"):
    app.secret_key = os.environ.get("SESSION_SECRET")
else:
    import secrets
    app.logger.warning("No SESSION_SECRET found, generating a temporary one")
    app.secret_key = secrets.token_hex(32)

# Add custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(s):
    """Convert newlines to HTML line breaks"""
    if s is None:
        return ""
    return s.replace('\n', '<br>')

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///calm_journey.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 60,
    "pool_size": 10,
    "max_overflow": 20,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure CSRF protection
app.config["WTF_CSRF_TIME_LIMIT"] = 7200
app.config["WTF_CSRF_SSL_STRICT"] = False
app.config["WTF_CSRF_ENABLED"] = True

# Configure session cookies
from datetime import timedelta
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_PERMANENT'] = True

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Base URL for production
app.config['BASE_URL'] = os.environ.get('BASE_URL', '')

# Initialize extensions
db.init_app(app)
csrf.init_app(app)
mail.init_app(app)
sess.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'stable_login'

@login_manager.user_loader
def load_user(user_id):
    try:
        from models import User
        return User.query.get(user_id)
    except:
        return None

@login_manager.unauthorized_handler
def unauthorized():
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('stable_login'))

# Custom login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('stable_login'))
        return f(*args, **kwargs)
    return decorated_view

# Error handlers
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}")
    return render_template('error.html', error="An unexpected error occurred"), 500

# Core routes for production
@app.route('/complete-landing')
def complete_landing():
    """Complete landing page for marketing integration"""
    return render_template('complete_landing_page.html')

@app.route('/')
def index():
    """Main application route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('complete_landing'))

# Register core blueprints only
with app.app_context():
    # Import models to create tables
    try:
        import models
        db.create_all()
        app.logger.info("Database tables created")
    except Exception as e:
        app.logger.error(f"Error creating database tables: {e}")

    # Register essential routes
    try:
        import routes
        app.logger.info("Core routes registered")
    except Exception as e:
        app.logger.error(f"Error registering routes: {e}")

    # Register admin routes
    try:
        import admin_routes
        app.logger.info("Admin routes registered")
    except Exception as e:
        app.logger.error(f"Error registering admin routes: {e}")

    # Register marketing integration
    try:
        import marketing_integration
        app.logger.info("Marketing integration registered")
    except Exception as e:
        app.logger.error(f"Error registering marketing integration: {e}")

    # Register stable login
    try:
        import stable_login
        app.logger.info("Stable login registered")
    except Exception as e:
        app.logger.error(f"Error registering stable login: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
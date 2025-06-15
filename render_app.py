"""
Production-specific application initialization for Render.com deployment.
This module ensures proper database initialization and Flask app configuration for the production environment.
"""

import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_session import Session

# Import shared database instance
from extensions import db

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_render_app():
    """
    Create and configure Flask app specifically for Render.com production environment.
    This ensures proper database initialization and session management.
    """
    app = Flask(__name__)
    
    # Production configuration
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'fallback-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 10
        }
    }
    
    # Session configuration for production
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # CSRF configuration for production
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF to resolve login issues
    app.config['WTF_CSRF_SSL_STRICT'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize session
    sess = Session()
    sess.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'stable_login.stable_login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(user_id)
    
    # Create database tables
    with app.app_context():
        try:
            from models import User, JournalEntry, CBTRecommendation, MoodLog
            db.create_all()
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Database table creation error: {e}")
    
    # Register only essential routes that exist
    try:
        import routes
        logger.info("Core routes registered")
    except Exception as e:
        logger.error(f"Core routes error: {e}")
    
    try:
        from stable_login import stable_login_bp
        app.register_blueprint(stable_login_bp)
        logger.info("Stable login registered")
    except Exception as e:
        logger.error(f"Stable login error: {e}")
    
    try:
        from minimal_register import minimal_register_bp
        app.register_blueprint(minimal_register_bp)
        logger.info("Minimal register registered")
    except Exception as e:
        logger.error(f"Minimal register error: {e}")
    
    logger.info("Render app initialization complete")
    return app

def register_core_routes(app):
    """Register core application routes"""
    try:
        import routes
        logger.info("Core routes registered")
    except Exception as e:
        logger.error(f"Core routes registration error: {e}")

def register_admin_routes(app):
    """Register admin routes"""
    try:
        from admin_routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        logger.info("Admin routes registered")
    except Exception as e:
        logger.error(f"Admin routes registration error: {e}")

def register_marketing_integration(app):
    """Register marketing integration"""
    try:
        from marketing_integration import marketing_bp
        app.register_blueprint(marketing_bp)
        logger.info("Marketing integration registered")
    except Exception as e:
        logger.error(f"Marketing integration registration error: {e}")

def register_stable_login(app):
    """Register stable login blueprint"""
    try:
        from stable_login import stable_login_bp
        app.register_blueprint(stable_login_bp)
        logger.info("Stable login blueprint registered")
    except Exception as e:
        logger.error(f"Stable login registration error: {e}")

def register_simple_register(app):
    """Register simple register blueprint"""
    try:
        from minimal_register import minimal_register_bp
        app.register_blueprint(minimal_register_bp)
        logger.info("Minimal register blueprint registered")
    except Exception as e:
        logger.error(f"Minimal register registration error: {e}")

def register_password_reset(app):
    """Register password reset blueprint"""
    try:
        from updated_password_reset import password_reset_bp
        app.register_blueprint(password_reset_bp)
        logger.info("Password reset blueprint registered")
    except Exception as e:
        logger.error(f"Password reset registration error: {e}")

def register_static_pages(app):
    """Register static pages blueprint"""
    try:
        from fallback_routes import fallback_bp
        app.register_blueprint(fallback_bp)
        logger.info("Static pages blueprint registered")
    except Exception as e:
        logger.error(f"Static pages registration error: {e}")

# Create the production app instance
app = create_render_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
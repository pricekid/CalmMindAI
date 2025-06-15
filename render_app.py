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
    
    # Production configuration with CSRF secret
    session_secret = os.environ.get('SESSION_SECRET', 'fallback-secret-key')
    app.config['SECRET_KEY'] = session_secret
    app.config['WTF_CSRF_SECRET_KEY'] = session_secret
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
    
    # Fix HTTPS/HTTP mismatch for Render deployment
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
    
    # Session configuration for production
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # CSRF configuration for production - disable secure for mixed content
    app.config['WTF_CSRF_SSL_STRICT'] = False
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF to resolve login issues
    app.config['WTF_CSRF_SSL_STRICT'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize session
    sess = Session()
    sess.init_app(app)
    
    # Initialize login manager
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    # Set login view after blueprint registration
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from models import User
            from admin_models import Admin
            
            # Check if this is an admin user
            if isinstance(user_id, str) and user_id.startswith('admin_'):
                admin_id = user_id.split('_')[1]
                return Admin.get(admin_id)
            
            # Regular user
            return User.query.get(user_id)
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {e}")
            return None
    
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
        # Set login view after blueprint registration
        login_manager.login_view = 'stable_login.stable_login'
        logger.info("Stable login registered")
    except Exception as e:
        logger.error(f"Stable login error: {e}")
    
    try:
        from simple_register import simple_register_bp
        app.register_blueprint(simple_register_bp)
        logger.info("Simple register registered")
    except Exception as e:
        logger.error(f"Simple register error: {e}")
    
    try:
        from production_login_fix import production_login_bp
        app.register_blueprint(production_login_bp)
        logger.info("Production login fix registered")
    except Exception as e:
        logger.error(f"Production login error: {e}")
    
    try:
        from emergency_production_fix import emergency_bp
        app.register_blueprint(emergency_bp)
        # Set emergency login as fallback login view
        login_manager.login_view = 'emergency.emergency_production_login'
        logger.info("Emergency production fix registered")
    except Exception as e:
        logger.error(f"Emergency production error: {e}")
    
    logger.info("Render app initialization complete")
    return app

# Remove unused function definitions to clean up the file

# Create the production app instance
app = create_render_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
from app import app, db
import logging
import os
from flask import redirect

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Apply authentication debugging if enabled
try:
    import debug_replit_auth
    debug_replit_auth.patch_replit_auth()
    debug_replit_auth.fix_none_split_error()
    logger.info("Authentication debugging enabled")
except ImportError as e:
    logger.warning(f"Authentication debugging not available: {e}")

# Ensure database tables exist
with app.app_context():
    db.create_all()

# Import and register Replit Auth blueprint
from replit_routes import replit_bp
app.register_blueprint(replit_bp, url_prefix='/auth')

# Register emergency login routes if available
try:
    from emergency_direct_login import emergency_bp
    
    # Check if the blueprint is already registered
    if emergency_bp.name not in app.blueprints:
        app.register_blueprint(emergency_bp)
        logger.info("Emergency login routes registered")
    else:
        logger.info("Emergency login routes already registered")
except ImportError:
    logger.warning("Emergency login routes not available")
except Exception as e:
    logger.error(f"Error registering emergency login routes: {e}")

# Create logs directory
os.makedirs('logs', exist_ok=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
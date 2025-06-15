"""
Production-compatible full Dear Teddy application.
Includes all features with robust error handling for production deployment.
"""

import os
import logging
import sys
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_production_app():
    """Create production app with all Dear Teddy features"""
    try:
        logger.info("Creating production Dear Teddy application")
        
        # Import the full application factory
        from app import create_app
        
        # Create the app with production settings
        app = create_app()
        
        # Add production-specific configurations
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Production session configuration
        app.config['SESSION_PERMANENT'] = True
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        
        # Fix HTTPS/HTTP for Render
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
        
        # Import and register all routes
        try:
            # Import routes in the correct order to avoid circular imports
            import forms  # Import forms first
            import routes
            import admin_routes
            import journal_routes
            import account_routes
            logger.info("All Dear Teddy routes loaded successfully")
        except Exception as e:
            logger.error(f"Routes import error: {e}")
            # Add basic login route with form
            from flask import render_template, request, flash, redirect, url_for
            from flask_login import login_user
            from werkzeug.security import check_password_hash
            
            @app.route('/login', methods=['GET', 'POST'])
            def login():
                try:
                    from forms import LoginForm
                    form = LoginForm()
                    if form.validate_on_submit():
                        from models import User
                        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
                        if user and check_password_hash(user.password_hash, form.password.data):
                            login_user(user, remember=True)
                            return redirect(url_for('dashboard'))
                        flash('Invalid email or password.', 'error')
                    return render_template('login.html', form=form)
                except Exception as e:
                    logger.error(f"Login route error: {e}")
                    return "Login temporarily unavailable", 500
        
        # Create database tables
        with app.app_context():
            try:
                from extensions import db
                import models  # Import all models
                db.create_all()
                logger.info("Production database tables created successfully")
                
                # Initialize admin user if needed
                try:
                    from admin_models import Admin
                    if not Admin.query.first():
                        admin = Admin(username='admin')
                        admin.set_password('admin123')
                        db.session.add(admin)
                        db.session.commit()
                        logger.info("Admin user created for production")
                except Exception as admin_e:
                    logger.warning(f"Admin user creation skipped: {admin_e}")
                    
            except Exception as e:
                logger.error(f"Database initialization error: {e}")
        
        logger.info("Production Dear Teddy application created successfully")
        return app
        
    except Exception as e:
        logger.error(f"Critical error creating production app: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fallback to minimal app if full app fails
        try:
            from minimal_render_app import app as minimal_app
            logger.info("Falling back to minimal app")
            return minimal_app
        except:
            raise

# Create the production app
app = create_production_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting production server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
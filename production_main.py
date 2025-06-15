"""
Production-only main file for Render deployment.
This ensures the minimal app is used for production without environment detection issues.
"""

import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

try:
    logger.info("Starting Dear Teddy production application")
    # Import the full application with all features
    from app import create_app
    app = create_app()
    
    # Apply production-specific configurations
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    
    # Initialize Flask-Login properly
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(user_id)
    
    # Import all routes to ensure full functionality
    try:
        import routes
        import admin_routes
        import journal_routes
        import account_routes
        logger.info("All route modules imported successfully")
    except Exception as route_error:
        logger.error(f"Route import error: {route_error}")
        # Add basic fallback routes if main routes fail
        from flask import redirect, render_template, request, flash
        from flask_login import current_user, login_user
        from werkzeug.security import check_password_hash
        
        @app.route('/')
        def index():
            if current_user.is_authenticated:
                return redirect('/dashboard')
            return redirect('/login')
        
        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                if email and password:
                    from models import User
                    user = User.query.filter_by(email=email).first()
                    if user and user.password_hash and check_password_hash(user.password_hash, password):
                        login_user(user, remember=True)
                        return redirect('/dashboard')
                flash('Invalid email or password.', 'error')
            return render_template('login.html')
        
        @app.route('/dashboard')
        def dashboard():
            if not current_user.is_authenticated:
                return redirect('/login')
            return render_template('dashboard.html', user=current_user)
    
    logger.info("Full Dear Teddy application imported successfully")
    
except Exception as e:
    logger.error(f"Critical error during app creation: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting production server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        logger.error(f"Production server startup error: {e}")
        raise
"""
Render.com deployment initialization module.

This module contains the necessary configuration and setup
for deploying the application on Render.com with proper authentication.
"""

import os
import logging
from flask import Blueprint, render_template, redirect, flash, request, session, url_for
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from models import User

# Set up logging
logger = logging.getLogger(__name__)

# Create the blueprint
render_bp = Blueprint('render', __name__)

# Define routes specific for Render.com deployment
@render_bp.route('/r-login', methods=['GET', 'POST'])
def render_login():
    """
    Simplified login route for Render.com deployments.
    This completely bypasses CSRF protection to work reliably on Render.
    """
    if current_user.is_authenticated:
        return redirect('/dashboard')
        
    error = None
    if request.method == 'POST':
        # Extract form data
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        # Log login attempt for debugging
        logger.info(f"Render login attempt for email: {email}")
        
        # Validate inputs
        if not email or not password:
            error = "Email and password are required"
            return render_template('r_login.html', error=error)
            
        # Look up the user
        user = User.query.filter(User.email.ilike(email)).first()
        
        # Validate password
        if user and user.check_password(password):
            # Set session to be permanent
            session.permanent = True
            session['login_source'] = 'render'
            
            # Log in the user
            login_user(user, remember=remember)
            
            # Set multiple session flags to ensure authentication is maintained
            session['render_authenticated'] = True
            session['login_method'] = 'render_direct' 
            session['direct_auth'] = user.id
            session['auth_source'] = 'render_optimized'
            session.permanent = True
            
            # Force session to save immediately
            session.modified = True
            
            logger.info(f"User {user.id} logged in successfully via Render direct login")
            
            # Redirect directly to dashboard with secure authentication
            return redirect('/dashboard?render_auth=true&direct=1')
        else:
            error = "Invalid email or password"
    
    # Render the login template
    return render_template('r_login.html', error=error)

@render_bp.route('/r-logout')
def render_logout():
    """Logout route for Render.com deployments."""
    if current_user.is_authenticated:
        logger.info(f"User {current_user.id} logged out via Render logout")
    
    # Clear session and log out
    logout_user()
    for key in list(session.keys()):
        session.pop(key, None)
    
    # Redirect to login
    return redirect('/r-login')

def register_render_routes(app):
    """
    Register Render.com-specific routes with the application.
    
    Args:
        app: The Flask application
    """
    # Register the blueprint
    app.register_blueprint(render_bp)
    
    # CRITICAL: Always exempt the render_login function from CSRF
    if hasattr(app, 'csrf'):
        app.csrf.exempt(render_bp)
        app.csrf.exempt(render_login)
        logger.info("CSRF protection completely disabled for Render.com login routes")
    
    # Add an environment flag
    app.config['IS_RENDER'] = os.environ.get('RENDER', 'false').lower() == 'true'
    logger.info(f"Render deployment mode: {app.config['IS_RENDER']}")
    
    # Modify the main login route to use Render login when appropriate
    @app.route('/login-selector')
    def login_selector():
        """Redirect to the appropriate login page based on deployment environment."""
        if app.config['IS_RENDER'] or request.args.get('render') == 'true':
            return redirect('/r-login')
        else:
            return redirect('/stable-login')
    
    # Patch main login route if on Render
    if app.config['IS_RENDER']:
        @app.route('/')
        def index_redirect():
            """Main route redirect for Render deployment."""
            if current_user.is_authenticated:
                return redirect('/dashboard')
            return redirect('/r-login')
    
    return app
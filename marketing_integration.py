"""
Marketing site integration for Dear Teddy.
Handles authentication flow between dearteddy.app and the Flask app on render.com.
"""

import os
import logging
from flask import Blueprint, request, redirect, session, flash
from flask_login import current_user

marketing_bp = Blueprint('marketing', __name__)
logger = logging.getLogger(__name__)

# Configure the render.com app URL for production
RENDER_APP_URL = os.environ.get('RENDER_APP_URL', 'https://dear-teddy.onrender.com')

@marketing_bp.route('/from-marketing')
def from_marketing():
    """
    Handle users coming from the dearteddy.app marketing site.
    This route processes marketing site redirects and directs users appropriately.
    """
    # Get the action parameter from the marketing site
    action = request.args.get('action', 'login')
    source = request.args.get('source', 'marketing')
    
    # Log the marketing site traffic
    logger.info(f"User arrived from marketing site - Action: {action}, Source: {source}")
    
    # Store marketing source in session for analytics
    session['marketing_source'] = source
    session['marketing_action'] = action
    
    # If user is already authenticated, go to dashboard
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    # Route based on the action from marketing site
    if action == 'signup' or action == 'register':
        flash('Welcome to Dear Teddy! Create your account to start journaling.', 'info')
        return redirect('/register-simple')
    elif action == 'get-started':
        flash('Welcome to Dear Teddy! Sign up to begin your wellness journey.', 'info')
        return redirect('/register-simple')
    else:  # Default to login
        return redirect('/stable-login')

@marketing_bp.route('/marketing-signup')
def marketing_signup():
    """Direct signup route for marketing site users"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    session['marketing_source'] = 'direct_signup'
    flash('Create your Dear Teddy account to start your mental wellness journey.', 'info')
    return redirect('/register-simple')

@marketing_bp.route('/marketing-login')
def marketing_login():
    """Direct login route for marketing site users"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    session['marketing_source'] = 'direct_login'
    return redirect('/stable-login')

@marketing_bp.route('/app-redirect')
def app_redirect():
    """
    Redirect route that can be used by the marketing site.
    Example: https://dear-teddy.onrender.com/app-redirect?action=signup
    """
    return from_marketing()

def get_marketing_redirect_urls():
    """
    Return the URLs that should be configured on the dearteddy.app marketing site.
    These URLs should be used for the Login and Sign Up buttons.
    """
    base_url = RENDER_APP_URL
    
    return {
        'login_url': f"{base_url}/marketing-login",
        'signup_url': f"{base_url}/marketing-signup", 
        'get_started_url': f"{base_url}/from-marketing?action=get-started",
        'app_redirect_url': f"{base_url}/app-redirect"
    }

def register_marketing_integration(app):
    """Register the marketing integration blueprint with the Flask app"""
    app.register_blueprint(marketing_bp)
    
    # Log the redirect URLs for configuration
    urls = get_marketing_redirect_urls()
    logger.info("Marketing integration registered. Configure these URLs on dearteddy.app:")
    for name, url in urls.items():
        logger.info(f"  {name}: {url}")
    
    return app
"""
Configure the Flask app to use the production login as default in production environments.
This will help ensure reliable login experience on the Render deployment.
"""

import os
import logging
from flask import Flask, redirect, request, url_for

logger = logging.getLogger(__name__)

def configure_production_login_as_default(app):
    """
    Configure the app to use production login as default in production environments.
    This function adds a route that intercepts requests to /stable-login 
    and redirects them to /production-login when running in production.
    """
    # Check if we're in a production environment - Render sets this env var
    is_production = 'RENDER' in os.environ or os.environ.get('ENVIRONMENT') == 'production'
    
    if is_production:
        logger.info("Production environment detected - configuring production login as default")
        
        # Add a route to redirect /stable-login to /production-login in production
        # Replace the existing route with a new route
        @app.route('/stable-login-redirect', methods=['GET'])
        def redirect_to_production_login():
            # Only redirect GET requests to avoid breaking form submissions
            logger.info("Redirecting from stable login to production login")
            # Preserve any query parameters like 'next'
            query_string = request.query_string.decode() if request.query_string else ''
            target = '/production-login'
            if query_string:
                target = f'{target}?{query_string}'
            return redirect(target)
        
        # Update the login_manager to point to production login
        app.config['LOGIN_MANAGER_VIEW'] = '/production-login'
            
        logger.info("Production login redirection configured successfully")
    else:
        logger.info("Development environment detected - using standard login")
    
    return app
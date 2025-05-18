"""
Production login middleware solution for Render deployment.
This ensures users are directed to the enhanced login page in production.
"""

import os
import logging
from flask import redirect, request
from werkzeug.wsgi import ClosingIterator

logger = logging.getLogger(__name__)

class ProductionLoginMiddleware:
    """
    Middleware that redirects /stable-login to /production-login in production.
    This avoids conflicts with existing routes and the login manager settings.
    """
    
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
        self.is_production = 'RENDER' in os.environ or os.environ.get('ENVIRONMENT') == 'production'
        if self.is_production:
            logger.info("ProductionLoginMiddleware: Production environment detected")
        else:
            logger.info("ProductionLoginMiddleware: Development environment detected")
    
    def __call__(self, environ, start_response):
        # Only apply middleware in production
        if not self.is_production:
            return self.wsgi_app(environ, start_response)
        
        # Check if this is a GET request to /stable-login
        path_info = environ.get('PATH_INFO', '')
        request_method = environ.get('REQUEST_METHOD', '')
        
        if path_info == '/stable-login' and request_method == 'GET':
            logger.info(f"ProductionLoginMiddleware: Redirecting {path_info} to /production-login")
            
            # Get any query parameters
            query_string = environ.get('QUERY_STRING', '')
            target = '/production-login'
            if query_string:
                target = f'{target}?{query_string}'
            
            # Create redirect response
            def start_redirection(status, headers, exc_info=None):
                new_headers = [('Location', target), ('Content-Type', 'text/html')]
                return start_response('302 Found', new_headers)
            
            # Return empty response with redirect
            return [b'Redirecting to enhanced login...']
        
        # For all other requests, use the normal app
        return self.wsgi_app(environ, start_response)


def apply_production_login_middleware(app):
    """
    Apply the production login middleware to the Flask app.
    This should be called directly from main.py.
    """
    app.wsgi_app = ProductionLoginMiddleware(app.wsgi_app)
    logger.info("ProductionLoginMiddleware applied to the application")
    return app
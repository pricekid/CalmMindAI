"""
CSRF Debug Middleware.

This middleware logs CSRF token validation details to help diagnose issues
with CSRF token validation failures.
"""
from flask import request, session
import logging

class CSRFDebugMiddleware:
    """
    Middleware to debug CSRF token validation issues.
    This logs details about the token in the session and in form submissions.
    """
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', '')
        
        # Only log CSRF debug information, don't try to access the request context
        if method == 'POST':
            self.logger.debug(f"CSRF Debug - Path: {path}, Method: {method}")
        
        # Pass through to the actual application
        return self.app(environ, start_response)
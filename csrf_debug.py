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
        
        # Only debug for POST requests
        if method == 'POST':
            with self.app.request_context(environ):
                self.logger.debug(f"CSRF Debug - Route: {path}")
                
                # Log session details
                session_id = session.get('_id')
                session_token = session.get('_csrf_token')
                
                self.logger.debug(f"Session ID: {session_id}")
                self.logger.debug(f"Session token exists: {session_token is not None}")
                if session_token:
                    self.logger.debug(f"Session token length: {len(session_token)}")
                
                # Log form submission details
                if request.form:
                    form_token = request.form.get('csrf_token')
                    self.logger.debug(f"Form token exists: {form_token is not None}")
                    if form_token:
                        self.logger.debug(f"Form token length: {len(form_token)}")
                        self.logger.debug(f"Tokens match: {form_token == session_token}")
        
        return self.app(environ, start_response)
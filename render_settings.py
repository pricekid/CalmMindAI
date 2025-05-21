"""
Render.com deployment configuration settings.

This module contains specific settings and configurations for
running the application on Render.com's hosting environment.
"""

import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

def init_render_settings(app):
    """
    Initialize Render-specific settings for the application.
    
    Args:
        app: The Flask application instance
    """
    # Set environment flag
    app.config['IS_RENDER'] = True
    
    # Force HTTPS on Render
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Set session cookie settings for Render
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configure logging for Render
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Log deployment information
    logger.info("Render deployment settings initialized")
    
    return app

def is_render_environment():
    """
    Check if the application is running in Render.com environment.
    
    Returns:
        bool: True if running on Render.com, False otherwise
    """
    return os.environ.get('RENDER') == 'true'
"""
Render.com compatibility module for Dear Teddy.

This module helps ensure the application functions properly on Render.com by:
1. Configuring session cookies appropriately for Render.com environment
2. Adjusting CSRF protection settings to work with Render.com's proxy setup
3. Providing environment-specific login handling
"""

import os
import logging
from flask import Flask, session

logger = logging.getLogger(__name__)

def init_render_compatibility(app):
    """
    Initialize Render.com compatibility settings.
    
    This function applies configuration changes needed for
    the application to work correctly when deployed on Render.com.
    
    Args:
        app: The Flask application instance
    """
    # Add the RENDER environment variable to the app config for easy checking
    app.config['IS_RENDER'] = os.environ.get('RENDER', 'false').lower() == 'true'
    
    # Log the environment detection
    if app.config['IS_RENDER']:
        logger.info("Render.com environment detected - applying compatibility settings")
    else:
        logger.info("Non-Render environment detected (likely Replit)")
    
    # Adjust session cookie settings for Render.com
    if app.config['IS_RENDER']:
        # Ensure cookies work behind Render's proxy
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Allow cross-site cookies
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        
        # CSRF settings need adjustment for Render.com
        app.config['WTF_CSRF_SSL_STRICT'] = False  # Disable strict SSL checking for CSRF
        app.config['WTF_CSRF_TIME_LIMIT'] = 86400  # Extend CSRF token lifetime to 24 hours for Render
        
        logger.info("Applied Render.com-specific cookie and CSRF settings")
    
    # Return the updated app
    return app

def is_render_environment():
    """
    Check if the current environment is Render.com.
    
    Returns:
        bool: True if running on Render.com, False otherwise
    """
    return os.environ.get('RENDER', 'false').lower() == 'true'
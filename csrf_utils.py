"""
Utilities for consistent CSRF token generation and validation.

This module provides centralized functions for CSRF token handling
to ensure consistent token generation across the application.
"""
import logging
from flask import current_app, session

logger = logging.getLogger(__name__)

def get_csrf_token():
    """
    Consistently generate and retrieve CSRF token.
    Returns the same token within a session.
    
    Returns:
        str: The CSRF token for the current session
    """
    try:
        from flask_wtf.csrf import generate_csrf
        token = generate_csrf()
        logger.debug("Generated/retrieved CSRF token")
        return token
    except Exception as e:
        logger.error(f"CSRF token generation error: {e}")
        # Emergency fallback - only for recovery scenarios
        import hashlib
        import time
        emergency_token = hashlib.sha256(f"emergency_{time.time()}".encode()).hexdigest()
        logger.warning(f"Using emergency CSRF token")
        return emergency_token

def validate_csrf_token(token):
    """
    Validate a CSRF token with detailed error logging.
    
    Args:
        token: The CSRF token to validate
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        from flask_wtf.csrf import validate_csrf
        validate_csrf(token)
        return True
    except Exception as e:
        logger.error(f"CSRF token validation error: {str(e)}")
        # Log session token for debugging
        if '_csrf_token' in session:
            session_token = session['_csrf_token']
            token_length = len(session_token) if session_token else 0
            token_prefix = session_token[:10] + '...' if token_length > 10 else session_token
            logger.error(f"Session token: {token_prefix} (length: {token_length})")
        else:
            logger.error("No CSRF token in session")
            
        # Log provided token for debugging
        if token:
            token_length = len(token)
            token_prefix = token[:10] + '...' if token_length > 10 else token
            logger.error(f"Provided token: {token_prefix} (length: {token_length})")
        else:
            logger.error("No token provided")
            
        return False
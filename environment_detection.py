"""
Environment detection module for Dear Teddy application.
Provides functions to determine the current hosting environment and appropriate URLs.
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_render():
    """
    Check if the application is running on Render.com
    
    Returns:
        bool: True if running on Render, False otherwise
    """
    return os.environ.get('RENDER', '').lower() == 'true'

def is_replit():
    """
    Check if the application is running on Replit
    
    Returns:
        bool: True if running on Replit, False otherwise
    """
    return os.environ.get('REPL_ID') is not None

def get_base_url():
    """
    Get the base URL for the current environment
    
    Returns:
        str: The base URL for the current environment
    """
    if is_render():
        # Render deployment URL
        return "https://dearteddy-4vqj.onrender.com"
    elif is_replit():
        # Replit URL
        return "https://calm-mind-ai-naturalarts.replit.app"
    else:
        # Local development or other environment
        return "http://localhost:5000"

def log_environment():
    """Log the detected environment information"""
    env_type = "Render" if is_render() else "Replit" if is_replit() else "Other/Local"
    base_url = get_base_url()
    
    logger.info(f"Detected environment: {env_type}")
    logger.info(f"Base URL: {base_url}")
    
    return {
        "environment": env_type,
        "base_url": base_url
    }
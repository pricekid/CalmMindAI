"""
Redirect script to make sure all login attempts go to the stable login.
This script will be registered in app.py to handle all login redirections.
"""

import os
import logging
from flask import Blueprint, redirect, request, current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for login redirection
redirect_login_bp = Blueprint('redirect_login', __name__)

@redirect_login_bp.route('/r-login')
def redirect_r_login():
    """Redirect r-login to stable login"""
    logger.info("Redirecting from r-login to stable-login")
    return redirect('/stable-login')

@redirect_login_bp.route('/direct-login')
def redirect_direct_login():
    """Redirect direct-login to stable login"""
    logger.info("Redirecting from direct-login to stable-login")
    return redirect('/stable-login')

@redirect_login_bp.route('/emergency-login')
def redirect_emergency_login():
    """Redirect emergency-login to stable login"""
    logger.info("Redirecting from emergency-login to stable-login")
    return redirect('/stable-login')

@redirect_login_bp.route('/test-login')
def redirect_test_login():
    """Redirect test-login to stable login"""
    logger.info("Redirecting from test-login to stable-login")
    return redirect('/stable-login')

@redirect_login_bp.route('/hc-login')
def redirect_hc_login():
    """Redirect hc-login to stable login"""
    logger.info("Redirecting from hc-login to stable-login")
    return redirect('/stable-login')

def register_login_redirects(app):
    """Register the login redirection blueprint with the app"""
    app.register_blueprint(redirect_login_bp)
    logger.info("Login redirection to stable-login registered successfully")
    return app
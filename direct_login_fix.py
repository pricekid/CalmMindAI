"""
Emergency direct login solution for Render deployments.

This module provides an alternative login approach that works
reliably on Render.com by bypassing potential environment-specific issues.
"""

import os
import logging
from flask import Blueprint, render_template, redirect, request, session, flash
from flask_login import login_user, current_user
from models import User
from app import db
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
direct_login_bp = Blueprint('direct_login', __name__)

@direct_login_bp.route('/direct-login', methods=['GET', 'POST'])
def direct_login():
    """
    Ultra-simplified direct login without any CSRF protection.
    For use only in emergency situations where standard login fails.
    """
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    # Track login errors
    error = None
    
    # Check if we have form submission
    if request.method == 'POST':
        # Get login details
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        # Log the attempt
        logger.info(f"Direct login attempt for: {email}")
        
        if not email or not password:
            error = "Email and password are required"
        else:
            try:
                # Check for case-insensitive match
                user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
                
                # Log if user found
                if user:
                    logger.info(f"User found for email: {email} with ID: {user.id}")
                    
                    # Verify password
                    if user.check_password(password):
                        # Save user info for debugging
                        session['direct_login_id'] = user.id
                        session['direct_login_email'] = user.email
                        session['direct_login_remember'] = remember
                        session.permanent = True
                        
                        # Perform login
                        login_user(user, remember=remember)
                        
                        # Set all authentication flags
                        session['authenticated'] = True
                        session['login_method'] = 'direct'
                        session['auth_timestamp'] = True
                        session.modified = True
                        
                        # Success log
                        logger.info(f"Direct login successful for user {user.id}")
                        
                        # Redirect to dashboard 
                        return redirect('/dashboard?direct=1&auth=true')
                    else:
                        logger.warning(f"Invalid password for user: {user.id}")
                        error = "Invalid email or password"
                else:
                    logger.warning(f"No user found for email: {email}")
                    error = "Invalid email or password"
            except Exception as e:
                logger.error(f"Error during direct login: {str(e)}")
                error = "An error occurred during login. Please try again."
    
    # Show login template with any errors
    return render_template('direct_login.html', error=error)

def register_direct_login(app):
    """
    Register the direct login blueprint with the application.
    
    Args:
        app: The Flask application
    """
    # Register blueprint
    app.register_blueprint(direct_login_bp)
    
    # Exempt from CSRF protection
    if hasattr(app, 'csrf'):
        app.csrf.exempt(direct_login_bp)
    
    # Log registration
    logger.info("Direct login blueprint registered successfully")
    
    return app
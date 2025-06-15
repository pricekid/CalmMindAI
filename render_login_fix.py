"""
Special login module for Render.com deployment.
This fixes session and cookie handling issues specific to the Render.com environment.
"""

import logging
import os
from flask import Blueprint, render_template, redirect, request, flash, session, url_for
from flask_login import login_user, current_user, logout_user
from extensions import db
from models import User
from werkzeug.security import check_password_hash
from urllib.parse import urlparse

render_login_bp = Blueprint('render_login', __name__)
logger = logging.getLogger(__name__)

@render_login_bp.route('/render-login', methods=['GET', 'POST'])
def render_login():
    """Login route with simplified handling for Render.com"""
    # Already logged in
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    error = None
    if request.method == 'POST':
        # Log request details for debugging
        logger.info(f"Login POST request received with form data keys: {list(request.form.keys())}")
        
        # Extract form data
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        # Basic validation
        if not email or not password:
            error = 'Email and password are required'
            logger.warning(f"Login attempt without email or password")
        else:
            try:
                # Find user by email (case-insensitive)
                user = User.query.filter(User.email.ilike(email)).first()
                logger.info(f"Login attempt - User found: {user is not None}")
                
                if user and user.check_password(password):
                    # Login successful
                    # Explicitly set session cookie parameters
                    session.permanent = True
                    # Add a session marker to verify persistence
                    session['login_origin'] = 'render_login'
                    session.modified = True
                    
                    # Complete login
                    login_user(user, remember=remember)
                    logger.info(f"User {user.id} logged in successfully via render_login")
                    
                    # Redirect handling
                    next_page = request.args.get('next')
                    if not next_page or urlparse(next_page).netloc != '':
                        next_page = '/dashboard'
                    return redirect(next_page)
                else:
                    error = 'Invalid email or password'
                    logger.warning(f"Failed login attempt for email: {email}")
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                error = 'An error occurred during login. Please try again.'
    
    # Set session to permanent with extended lifetime
    session.permanent = True
    session.modified = True
    
    return render_template('render_login.html', error=error)

@render_login_bp.route('/render-logout')
def render_logout():
    """Logout route with proper session clearing for Render.com"""
    # Log the logout
    if current_user.is_authenticated:
        logger.info(f"User {current_user.id} logged out")
    
    # Clear the session completely
    logout_user()
    for key in list(session.keys()):
        session.pop(key, None)
    
    # Redirect to login
    return redirect('/render-login')
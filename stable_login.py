"""
Stable login module for Calm Journey.
Provides a Blueprint to handle user authentication with enhanced CSRF protection.
"""

import logging
from flask import Blueprint, render_template, redirect, request, flash, session
from flask_login import login_user, current_user
from models import User, db
from csrf_utils import get_csrf_token
import os

stable_login_bp = Blueprint('stable_login', __name__)
logger = logging.getLogger(__name__)

@stable_login_bp.route('/stable-login', methods=['GET', 'POST'])
def stable_login():
    """Login route with careful CSRF handling"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    error = None
    if request.method == 'POST':
        # Always log CSRF token for debugging
        form_token = request.form.get('csrf_token')
        session_token = session.get('_csrf_token')
        logger.info(f"Login attempt - Form token length: {len(form_token) if form_token else 0}")
        logger.info(f"Login attempt - Session token length: {len(session_token) if session_token else 0}")
        
        email = request.form.get('email')
        email = email.lower() if email else ''
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        # Extra safety checks
        if not email or not password:
            error = 'Email and password are required'
        else:
            try:
                # Query user with extra logging
                user = User.query.filter_by(email=email).first()
                logger.info(f"Login attempt - User found: {user is not None}")
                
                # Check if user exists and password is correct
                if user:
                    # For debugging
                    logger.info(f"User password hash exists: {user.password_hash is not None}")
                    
                    # Login successful if password check passes
                    if user.check_password(password):
                        # Set permanent session before login
                        session.permanent = True
                        login_user(user, remember=remember)
                        logger.info(f"User {user.id} logged in successfully")
                    
                        # Redirect to next page or dashboard
                        next_page = request.args.get('next')
                        if next_page and next_page.startswith('/'):
                            return redirect(next_page)
                        return redirect('/dashboard')
                    else:
                        error = 'Invalid email or password'
                        logger.warning(f"Failed login attempt for email: {email}")
                else:
                    error = 'Invalid email or password'
                    logger.warning(f"Failed login attempt for email: {email}")
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                error = 'An error occurred during login. Please try again.'
    
    # Always get a fresh token and ensure it's explicitly stored in the session
    csrf_token = get_csrf_token()
    session['_csrf_token'] = csrf_token
    
    # Set session to permanent with extended lifetime
    session.permanent = True
    # Force session save
    session.modified = True
    
    return render_template('stable_login.html', 
                          csrf_token=csrf_token, 
                          error=error)

# Replit Auth route removed as requested
"""
Stable login implementation with careful CSRF handling.

This module provides a robust login system that properly handles
CSRF tokens and session management to address persistent CSRF issues.
"""
import logging
from flask import Blueprint, render_template, redirect, request, flash, session
from flask_login import login_user, current_user
from models import User
from csrf_utils import get_csrf_token
from datetime import timedelta

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
        logger.info(f"Login attempt - Session token exists: {session_token is not None}")
        
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        # Validate inputs
        if not email or not password:
            error = 'Email and password are required'
        else:
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                # Set permanent session before login
                session.permanent = True
                login_user(user, remember=remember)
                logger.info(f"User {user.id} logged in successfully")
                return redirect('/dashboard')
            else:
                error = 'Invalid email or password'
                logger.warning(f"Failed login attempt for email: {email}")
    
    # Always get a fresh token for GET requests
    csrf_token = get_csrf_token()
    
    # Set session to permanent with extended lifetime
    session.permanent = True
    
    return render_template('stable_login.html', 
                          csrf_token=csrf_token, 
                          error=error)
"""
Production login fix for the Render deployment of Dear Teddy.
This module provides a more robust login handler for the production environment.
"""

import os
import logging
from flask import Blueprint, render_template, redirect, request, flash, session, jsonify
from flask_login import login_user, current_user
from models import User, db
from werkzeug.security import check_password_hash
from sqlalchemy import func

production_login_bp = Blueprint('production_login', __name__)
logger = logging.getLogger(__name__)

@production_login_bp.route('/production-login', methods=['GET', 'POST'])
def production_login():
    """
    Production login route with enhanced email handling.
    Specifically designed to work in the Render deployment environment.
    """
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    error = None
    debug_info = {}
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        debug_info['original_email'] = email
        
        # Convert email to lowercase and strip whitespace for consistency
        email_normalized = email.lower().strip() if email else ''
        debug_info['normalized_email'] = email_normalized
        
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        # Extra safety checks
        if not email or not password:
            error = 'Email and password are required'
        else:
            try:
                # Log the attempt details for debugging
                logger.info(f"Production login attempt with email: {email_normalized}")
                
                # Try multiple approaches to find the user to handle case sensitivity issues
                
                # 1. Try exact case-sensitive match first
                user = User.query.filter(User.email == email_normalized).first()
                
                # 2. If not found, try case-insensitive match with SQLAlchemy func.lower
                if not user:
                    # Use SQLAlchemy's func.lower for database-level case-insensitive comparison
                    user = User.query.filter(func.lower(User.email) == func.lower(email_normalized)).first()
                    
                # 3. If still not found, try raw SQL query as a last resort
                if not user:
                    try:
                        # Raw SQL query with LOWER function for maximum compatibility
                        from sqlalchemy import text
                        sql = text("SELECT * FROM \"user\" WHERE LOWER(email) = LOWER(:email) LIMIT 1")
                        result = db.session.execute(sql, {"email": email_normalized}).fetchone()
                        
                        if result:
                            # Convert the result to a User object
                            user = User.query.get(result[0])  # First column should be id
                    except Exception as sql_error:
                        logger.error(f"SQL error during login: {str(sql_error)}")
                
                logger.info(f"Login attempt - User found: {user is not None}")
                
                if user:
                    # For debugging
                    logger.info(f"Found user with email: {user.email}")
                    logger.info(f"User password hash exists: {user.password_hash is not None}")
                    
                    # Validate password
                    password_valid = user.check_password(password)
                    logger.info(f"Password validation result: {password_valid}")
                    
                    if password_valid:
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
                        logger.warning(f"Failed login attempt - invalid password for email: {email_normalized}")
                else:
                    error = 'Invalid email or password'
                    logger.warning(f"Failed login attempt - user not found for email: {email_normalized}")
            except Exception as e:
                logger.error(f"Production login error: {str(e)}")
                error = f'An error occurred during login. Please try again.'
    
    # Generate CSRF token
    csrf_token = session.get('_csrf_token', os.urandom(32).hex())
    session['_csrf_token'] = csrf_token
    
    # Set session to permanent for extended lifetime
    session.permanent = True
    session.modified = True
    
    return render_template('production_login.html', 
                         csrf_token=csrf_token, 
                         error=error,
                         debug_info=debug_info if os.environ.get('DEBUG') else None)
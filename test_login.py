"""
Test login module for Dear Teddy.
Provides a detailed diagnostic login page to help troubleshoot login issues.
"""

import logging
from flask import Blueprint, render_template, redirect, request, flash, session, jsonify
from flask_login import login_user, current_user
from models import User, db
from csrf_utils import get_csrf_token
import os

test_login_bp = Blueprint('test_login', __name__)
logger = logging.getLogger(__name__)

@test_login_bp.route('/test-login', methods=['GET', 'POST'])
def test_login():
    """Diagnostic login route with detailed feedback for troubleshooting"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    error = None
    debug_info = {}
    
    if request.method == 'POST':
        # Create diagnostic information
        debug_info['method'] = 'POST'
        
        # Always log CSRF token for debugging
        form_token = request.form.get('csrf_token')
        session_token = session.get('_csrf_token')
        debug_info['form_token_length'] = len(form_token) if form_token else 0
        debug_info['session_token_length'] = len(session_token) if session_token else 0
        
        email = request.form.get('email')
        debug_info['original_email'] = email
        
        email = email.lower().strip() if email else ''
        debug_info['processed_email'] = email
        
        password = request.form.get('password', '')
        debug_info['password_provided'] = bool(password)
        
        remember = request.form.get('remember') == 'on'
        debug_info['remember_me'] = remember
        
        # Extra safety checks
        if not email or not password:
            error = 'Email and password are required'
            debug_info['validation_error'] = 'Email and password are required'
        else:
            try:
                # Check if any user with this email exists
                user_exact = User.query.filter(User.email == email).first()
                debug_info['exact_match_found'] = user_exact is not None
                
                # Query user with case-insensitive email matching
                user = User.query.filter(User.email.ilike(email)).first()
                debug_info['case_insensitive_match_found'] = user is not None
                
                if user:
                    debug_info['user_id'] = user.id
                    debug_info['stored_email'] = user.email
                    debug_info['password_hash_exists'] = user.password_hash is not None
                    
                    # Password validation
                    password_valid = user.check_password(password)
                    debug_info['password_valid'] = password_valid
                    
                    if password_valid:
                        # Set permanent session before login
                        session.permanent = True
                        login_user(user, remember=remember)
                        debug_info['login_successful'] = True
                        
                        # Redirect to next page or dashboard
                        next_page = request.args.get('next')
                        if next_page and next_page.startswith('/'):
                            return redirect(next_page)
                        return redirect('/dashboard')
                    else:
                        error = 'Invalid password'
                        debug_info['login_error'] = 'Invalid password'
                else:
                    error = 'Email not found'
                    debug_info['login_error'] = 'Email not found'
                    
                    # Search for similar emails to suggest
                    similar_users = User.query.filter(User.email.ilike(f'%{email.split("@")[0]}%')).all()
                    if similar_users:
                        debug_info['similar_emails'] = [u.email for u in similar_users]
                    
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                error = f'An error occurred during login: {str(e)}'
                debug_info['exception'] = str(e)
    
    # Always get a fresh token and ensure it's explicitly stored in the session
    csrf_token = get_csrf_token()
    session['_csrf_token'] = csrf_token
    
    # Set session to permanent with extended lifetime
    session.permanent = True
    # Force session save
    session.modified = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'error': error,
            'debug_info': debug_info
        })
    
    return render_template('test_login.html', 
                          csrf_token=csrf_token, 
                          error=error,
                          debug_info=debug_info)
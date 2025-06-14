"""
Stable login module for Dear Teddy with comprehensive error logging.
Provides a Blueprint to handle user authentication with detailed debugging.
"""

import logging
import traceback
from flask import Blueprint, render_template, redirect, request, flash, session
from flask_login import login_user, current_user
from models import User, db
from flask_wtf.csrf import generate_csrf
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email
import os

stable_login_bp = Blueprint('stable_login', __name__)
logger = logging.getLogger(__name__)

class StableLoginForm(FlaskForm):
    """Simple login form without CSRF validation"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

@stable_login_bp.route('/stable-login', methods=['GET', 'POST'])
def stable_login():
    """Login route with comprehensive error logging and debugging"""
    
    if current_user.is_authenticated:
        logger.info("✅ User already authenticated, redirecting to dashboard")
        return redirect('/dashboard')
    
    form = StableLoginForm()
    error_message = None

    if request.method == 'POST':
        try:
            # Extract form data
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = request.form.get('remember') == 'on'
            form_token = request.form.get('csrf_token')
            session_token = session.get('_csrf_token')
            
            # Log comprehensive request details
            logger.info(f"🔍 LOGIN ATTEMPT STARTED")
            logger.info(f"  📧 Email: {email}")
            logger.info(f"  🔑 Password provided: {bool(password)}")
            logger.info(f"  🏷️ Remember me: {remember}")
            logger.info(f"  🎫 Form CSRF token length: {len(form_token) if form_token else 0}")
            logger.info(f"  🎫 Session CSRF token length: {len(session_token) if session_token else 0}")
            logger.info(f"  📋 Request method: {request.method}")
            logger.info(f"  🌐 User agent: {request.headers.get('User-Agent', 'Unknown')}")
            logger.info(f"  📍 Remote address: {request.remote_addr}")
            logger.info(f"  📋 Form data keys: {list(request.form.keys())}")
            logger.info(f"  📋 Session keys: {list(session.keys())}")
            
            # Since this blueprint is CSRF exempt, skip CSRF validation
            if not form_token:
                logger.info("ℹ️ CSRF token missing but blueprint is exempt - proceeding")
            
            # Validate input fields
            if not email or not password:
                error_message = 'Email and password are required'
                logger.warning(f"❌ Login failed - Missing fields: Email={bool(email)}, Password={bool(password)}")
                return render_template('stable_login.html', form=form, error=error_message)
            
            # Proceed with authentication
            logger.info(f"🔍 Starting database lookup for email: {email}")
            
            # Query user with case-insensitive email matching
            user = User.query.filter(User.email.ilike(email)).first()
            logger.info(f"👤 Database query result - User found: {user is not None}")
            
            if user:
                # Log user details for debugging
                logger.info(f"👤 User details:")
                logger.info(f"  - ID: {user.id}")
                logger.info(f"  - Email: {user.email}")
                logger.info(f"  - Has password hash: {user.password_hash is not None}")
                logger.info(f"  - Password hash length: {len(user.password_hash) if user.password_hash else 0}")
                
                # Validate password
                logger.info(f"🔐 Starting password validation...")
                password_valid = user.check_password(password)
                logger.info(f"🔐 Password validation result: {password_valid}")
                
                if password_valid:
                    # Set permanent session before login
                    session.permanent = True
                    logger.info(f"📋 Session set to permanent: {session.permanent}")
                    
                    # Perform login
                    logger.info(f"🔓 Attempting to log in user...")
                    login_user(user, remember=remember)
                    logger.info(f"✅ User {user.id} logged in successfully")
                    
                    # Check authentication status after login
                    logger.info(f"📋 Post-login authentication status: {current_user.is_authenticated}")
                    logger.info(f"📋 Current user ID: {current_user.get_id() if current_user.is_authenticated else 'None'}")
                    
                    # Redirect logic
                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/'):
                        logger.info(f"🔀 Redirecting to next page: {next_page}")
                        return redirect(next_page)
                    
                    logger.info(f"🔀 Redirecting to dashboard")
                    return redirect('/dashboard')
                else:
                    error_message = 'Invalid email or password'
                    logger.warning(f"❌ Login failed - Invalid password for email: {email}")
            else:
                error_message = 'Invalid email or password'
                logger.warning(f"❌ Login failed - User not found for email: {email}")
                
        except Exception as e:
            logger.error(f"🔥 LOGIN EXCEPTION OCCURRED:")
            logger.error(f"🔥 Exception type: {type(e).__name__}")
            logger.error(f"🔥 Exception message: {str(e)}")
            logger.error(f"🔥 Full traceback:")
            logger.error(traceback.format_exc())
            error_message = 'An internal error occurred during login. Please try again.'

    # Set session properties
    session.permanent = True
    session.modified = True
    
    try:
        logger.info(f"📄 Rendering login template with error: {error_message}")
        return render_template('stable_login.html', form=form, error=error_message)
    except Exception as e:
        logger.error(f"🔥 Template rendering error: {str(e)}")
        logger.error(f"🔥 Template error traceback: {traceback.format_exc()}")
        
        # Fallback simple HTML response
        fallback_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Dear Teddy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 400px; margin: 0 auto; padding: 20px; background: white; border-radius: 8px; }}
                input {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }}
                button {{ width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
                .error {{ color: #dc3545; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Dear Teddy - Login</h1>
                <form method="post">
                    <input type="email" name="email" placeholder="Email" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <label><input type="checkbox" name="remember"> Remember Me</label>
                    <button type="submit">Sign In</button>
                </form>
                {f'<div class="error">{error_message}</div>' if error_message else ''}
                <p><a href="/register">Don't have an account? Sign up</a></p>
            </div>
        </body>
        </html>
        """
        return fallback_html
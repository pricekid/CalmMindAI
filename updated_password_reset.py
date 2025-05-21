"""
Updated password reset routes that use environment detection to provide correct URLs
in password reset emails.
"""

import os
import logging
import secrets
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_mail import Message
from werkzeug.security import generate_password_hash
from urllib.parse import urlencode

# Import from our environment detection module
from environment_detection import get_base_url, is_render, is_replit, log_environment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
updated_pwd_reset_bp = Blueprint('updated_pwd_reset', __name__)

def send_password_reset_email(app, user):
    """
    Send a password reset email to the user with the appropriate URL
    based on the detected environment.
    """
    # Get current time as timestamp
    timestamp = int(time.time())
    
    # Create a secure token
    token = secrets.token_urlsafe(32)
    
    # Set token expiration to 60 minutes from now
    expires = timestamp + 3600
    
    # Store the token in the user object
    user.reset_token = token
    user.reset_token_expires = expires
    
    # Get the base URL for the current environment
    base_url = get_base_url()
    logger.info(f"Using base URL for password reset: {base_url}")
    
    # Create the reset URL with the token
    params = urlencode({'email': user.email, 'expires': expires})
    reset_url = f"{base_url}/reset-password/{token}?{params}"
    
    # Create email subject and body
    subject = "Dear Teddy Password Reset"
    
    # Email body in HTML format with environment-specific URL
    html = render_template(
        'email/password_reset.html',
        reset_url=reset_url,
        user=user,
        expires_minutes=60
    )
    
    # Import the app's email functionality
    from improved_email_service import send_email
    
    # Send the email
    try:
        send_email(
            recipient=user.email,
            subject=subject,
            html_content=html
        )
        logger.info(f"Password reset email sent to {user.email} with URL: {reset_url}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return False

@updated_pwd_reset_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Handle forgot password requests.
    """
    from app import db
    from models import User
    
    # Check if user is already logged in
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('forgot_password.html', title='Forgot Password')
        
        # Find the user by email (case insensitive)
        user = User.query.filter(User.email.ilike(email)).first()
        
        if user:
            # Log which environment we're using for the reset
            env_info = log_environment()
            logger.info(f"Password reset requested for {email} in {env_info['environment']} environment")
            
            # Send the reset email
            success = send_password_reset_email(None, user)
            
            if success:
                # Update the user in the database
                try:
                    db.session.commit()
                    logger.info(f"Reset token saved for user {user.id}")
                except Exception as db_error:
                    logger.error(f"Database error saving reset token: {str(db_error)}")
                    db.session.rollback()
                    flash('An error occurred. Please try again later.', 'danger')
                    return render_template('forgot_password.html', title='Forgot Password')
                
                # Show success message
                flash('A password reset link has been sent to your email address.', 'success')
                return redirect('/login')
            else:
                # Failed to send email
                flash('Failed to send reset email. Please try again later.', 'danger')
        else:
            # Don't reveal that the user doesn't exist for security reasons
            logger.warning(f"Password reset requested for non-existent user: {email}")
            flash('If an account exists with that email, a password reset link has been sent.', 'info')
            return redirect('/login')
    
    # GET request - show form
    return render_template('forgot_password.html', title='Forgot Password')

@updated_pwd_reset_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Handle password reset with token.
    """
    from app import db
    from models import User
    
    # Check if user is already logged in
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    # Get email and expiry from query parameters
    email = request.args.get('email')
    expires = request.args.get('expires')
    
    if not email or not expires:
        flash('Invalid reset link. Missing parameters.', 'danger')
        return redirect('/forgot-password')
    
    # Check if the token has expired
    try:
        expiry_time = int(expires)
        current_time = int(time.time())
        
        if current_time > expiry_time:
            flash('Password reset link has expired. Please request a new one.', 'danger')
            return redirect('/forgot-password')
    except ValueError:
        flash('Invalid reset link. Please request a new one.', 'danger')
        return redirect('/forgot-password')
    
    # Find the user with the given email and token
    user = User.query.filter_by(email=email, reset_token=token).first()
    
    if not user:
        flash('Invalid reset link. Please request a new one.', 'danger')
        return redirect('/forgot-password')
    
    # Handle form submission
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            # Update the user's password
            user.password_hash = generate_password_hash(password)
            user.reset_token = None
            user.reset_token_expires = None
            
            try:
                db.session.commit()
                flash('Your password has been reset successfully. You can now log in.', 'success')
                return redirect('/login')
            except Exception as e:
                logger.error(f"Error updating password: {str(e)}")
                db.session.rollback()
                flash('An error occurred. Please try again.', 'danger')
    
    # GET request - show form
    return render_template('reset_password.html', title='Reset Password', token=token, email=email, expires=expires)

def register_password_reset(app):
    """
    Register the password reset blueprint with the app.
    """
    app.register_blueprint(updated_pwd_reset_bp)
    logger.info("Password reset routes registered with updated SendGrid email integration")
    
    # Log the environment we're running in
    env_info = log_environment()
    logger.info(f"Password reset configured for {env_info['environment']} environment")
    logger.info(f"Using base URL: {env_info['base_url']}")
    
    return app
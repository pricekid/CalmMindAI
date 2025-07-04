"""
Enhanced password reset functionality with improved error handling and diagnostics.
This module handles password reset request, token generation, and password updates.
"""
import os
import logging
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import current_user
from werkzeug.security import generate_password_hash

# Import the new email service
from new_email_service import send_password_reset_email

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
password_reset_bp = Blueprint('password_reset', __name__)

# Dictionary to store reset tokens (in a production app, these should be in a database)
# Format: {token: {'user_id': user_id, 'email': email, 'expires': expires_datetime}}
reset_tokens = {}

def generate_token():
    """Generate a secure token for password reset"""
    return secrets.token_urlsafe(32)

def get_base_url():
    """Get the base URL of the application"""
    # In production, this should come from configuration
    return os.environ.get('BASE_URL', 'https://dearteddy-app.replit.app')

def store_reset_token(user_id, email):
    """
    Store a password reset token.
    
    Args:
        user_id: The user ID
        email: The user's email address
        
    Returns:
        str: The generated token
    """
    token = generate_token()
    expires = datetime.utcnow() + timedelta(hours=1)
    
    reset_tokens[token] = {
        'user_id': user_id,
        'email': email,
        'expires': expires
    }
    
    return token

def validate_token(token):
    """
    Validate a password reset token.
    
    Args:
        token: The token to validate
        
    Returns:
        dict or None: The token data if valid, None otherwise
    """
    token_data = reset_tokens.get(token)
    if not token_data:
        return None
        
    if token_data['expires'] < datetime.utcnow():
        # Token expired
        del reset_tokens[token]
        return None
        
    return token_data

def clear_expired_tokens():
    """Clear expired tokens"""
    now = datetime.utcnow()
    expired_tokens = [
        token for token, data in reset_tokens.items()
        if data['expires'] < now
    ]
    
    for token in expired_tokens:
        del reset_tokens[token]
        
    return len(expired_tokens)

@password_reset_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('forgot_password.html')
            
        # Find user by email
        from app import db
        from models import User
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal that the user doesn't exist for security
            flash('If your email is registered, you will receive a password reset link shortly.', 'info')
            return render_template('forgot_password.html')
            
        # Generate and store token
        token = store_reset_token(user.id, email)
        
        # Send reset email
        reset_url = f"{get_base_url()}/reset-password/{token}"
        result = send_password_reset_email(email, token, reset_url)
        
        if result.get('success'):
            flash('If your email is registered, you will receive a password reset link shortly.', 'info')
            if result.get('fallback'):
                logger.warning(f"Password reset email for {email} saved to fallback system")
                flash('Note: Our email delivery system is currently in maintenance mode. Please check your account with admin if you don\'t receive an email.', 'warning')
        else:
            logger.error(f"Failed to send password reset email to {email}: {result.get('error')}")
            flash('An error occurred while sending the password reset email. Please try again later.', 'danger')
            
        return render_template('forgot_password.html')
        
    return render_template('forgot_password.html')

@password_reset_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    # Validate token
    token_data = validate_token(token)
    if not token_data:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('password_reset.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or len(password) < 8:
            flash('Please enter a password with at least 8 characters.', 'danger')
            return render_template('reset_password.html', token=token)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
            
        # Update password
        from app import db
        from models import User
        
        user = User.query.get(token_data['user_id'])
        if not user:
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('password_reset.forgot_password'))
            
        # Update user's password
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        
        # Remove used token
        del reset_tokens[token]
        
        flash('Your password has been updated! You can now log in with your new password.', 'success')
        return redirect('/stable-login')
        
    return render_template('reset_password.html', token=token)

@password_reset_bp.route('/api/password-reset/metrics', methods=['GET'])
def reset_metrics():
    """Get password reset metrics (admin only)"""
    # In a real app, this would be protected
    expired = clear_expired_tokens()
    
    return jsonify({
        'active_tokens': len(reset_tokens),
        'expired_tokens_cleared': expired,
        'timestamp': datetime.utcnow().isoformat()
    })

def register_password_reset(app):
    """Register password reset routes with Flask app"""
    app.register_blueprint(password_reset_bp)
    logger.info("Password reset routes registered with SendGrid email integration")
    return True
"""
Password reset functionality with proper blueprint and templates.
"""

import os
import logging
import secrets
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, flash, url_for
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint with unique name
pwd_reset_bp = Blueprint('password_reset_pages', __name__, url_prefix='/pwd-reset')

@pwd_reset_bp.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    """Handle password reset requests"""
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('pwd_reset/forgot.html')
        
        # Here we would normally look up the user and send an email
        # For now, we'll just show a success message
        flash('If an account exists with that email, you will receive a password reset link shortly.', 'success')
        logger.info(f"Password reset requested for email: {email}")
        
        return redirect('/pwd-reset/forgot')
    
    return render_template('pwd_reset/forgot.html')

@pwd_reset_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('pwd_reset/reset.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('pwd_reset/reset.html', token=token)
        
        # Here we would validate the token and update the password
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect('/stable-login')
    
    return render_template('pwd_reset/reset.html', token=token)
"""
Super basic login route with minimal dependencies to fix the JSON parsing issues.
"""
import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, Blueprint
from flask_login import LoginManager, login_user, current_user, logout_user
from models import User
from app import db

logger = logging.getLogger(__name__)
basic_login_bp = Blueprint('basic_login', __name__)

@basic_login_bp.route('/basic-login', methods=['GET', 'POST'])
def basic_login():
    """
    Login route with minimal dependencies and error handling.
    """
    # Check if user is already logged in
    if current_user.is_authenticated:
        # If logged in as admin, redirect to admin dashboard
        if hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
            return redirect(url_for('admin.dashboard'))
        # Otherwise, go to the regular dashboard
        return redirect(url_for('dashboard'))
    
    # Process form submission
    if request.method == 'POST':
        try:
            # Get form data directly from request
            email = request.form.get('email', '').lower() if request.form.get('email') else ''
            password = request.form.get('password', '')
            remember = 'remember' in request.form
            
            # Validate submission
            if not email or not password:
                flash('Email and password are required.', 'danger')
                return render_template('basic_login.html')
            
            # Find user
            user = User.query.filter_by(email=email).first()
            
            # Validate credentials
            if user and user.check_password(password):
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                
                # Redirect based on next parameter
                if next_page and next_page.startswith('/admin'):
                    flash('You need admin privileges to access that page.', 'warning')
                    return redirect(url_for('dashboard'))
                
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check your email and password.', 'danger')
        except Exception as e:
            # Log error, but don't expose to user
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')
    
    # Render login form for GET requests or unsuccessful POST
    return render_template('basic_login.html')
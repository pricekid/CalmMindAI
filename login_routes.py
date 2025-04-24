"""
Special login routes that handle the JSON parsing error.
"""
import os
import logging
from flask import (
    render_template, url_for, flash, redirect, 
    request, jsonify, Blueprint, Response
)
from flask_login import current_user, login_user
from werkzeug.security import check_password_hash
from models import User
from app import db

login_bp = Blueprint('login_routes', __name__)
logger = logging.getLogger(__name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Super simplified login route that uses our simplified template without complex data handling.
    """
    # Check if user is already logged in
    if current_user.is_authenticated:
        # If logged in as admin, redirect to admin dashboard
        if hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
            return redirect(url_for('admin.dashboard'))
        # Otherwise, go to the regular dashboard using direct path
        return redirect('/dashboard')
    
    try:
        if request.method == 'POST':
            # Get values directly from the request form
            email = request.form.get('email', '').lower()
            password = request.form.get('password', '')
            remember = 'remember' in request.form
            
            # Basic validation
            if not email or not password:
                flash('Email and password are required.', 'danger')
                return render_template('simple_login.html')
            
            # Find user
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                
                # Don't redirect to admin pages from regular login
                if next_page and next_page.startswith('/admin'):
                    flash('You need admin privileges to access that page.', 'warning')
                    return redirect('/dashboard')
                    
                return redirect(next_page if next_page and not next_page.startswith('/admin') else '/dashboard')
            else:
                flash('Login unsuccessful. Please check your email and password.', 'danger')
                return render_template('simple_login.html')
        
        # For GET requests, just show the form
        return render_template('simple_login.html')
        
    except Exception as e:
        # Log the error
        logger.error(f"Error in login process: {str(e)}")
        
        # Show a generic error page
        return render_template('error.html', 
                            title='Login Error',
                            color='#dc3545',
                            alert_type='danger',
                            alert_heading='Error',
                            alert_message='We\'re having trouble processing your login.',
                            messages=[
                                'We encountered an issue while trying to log you in. This could be due to temporary technical issues.',
                                'Please try again in a few minutes.'
                            ],
                            buttons=[
                                {'url': '/', 'class': 'btn-primary', 'text': 'Go to Home'},
                                {'url': '/login', 'class': 'btn-light', 'text': 'Try Again'}
                            ]), 500
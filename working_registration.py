"""
Working Registration System
CSRF-exempt registration that works reliably for production
"""

from flask import Blueprint, request, render_template, redirect, flash, session
from flask_login import login_user, current_user
from models import User, db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

working_registration_bp = Blueprint('working_registration', __name__)

@working_registration_bp.route('/working-register', methods=['GET', 'POST'])
def working_register():
    """CSRF-exempt registration route that always works"""
    
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            logger.info(f"Registration attempt for email: {email}")
            
            # Validation
            if not all([username, email, password, confirm_password]):
                flash('All fields are required.', 'error')
                return render_template('working_register.html', 
                                     username=username, email=email)
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('working_register.html', 
                                     username=username, email=email)
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('working_register.html', 
                                     username=username, email=email)
            
            # Check if user exists
            existing_user = User.query.filter(
                (func.lower(User.email) == email) | (User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email.lower() == email:
                    flash('Email already registered. Please use a different email.', 'error')
                else:
                    flash('Username already taken. Please choose a different username.', 'error')
                return render_template('working_register.html', 
                                     username=username if existing_user.email.lower() != email else '',
                                     email=email if existing_user.email.lower() == email else '')
            
            # Create user
            user = User(username=username, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Auto-login
            session.permanent = True
            login_user(user, remember=True)
            
            logger.info(f"User {user.id} registered and logged in successfully")
            flash('Registration successful! Welcome to Dear Teddy.', 'success')
            return redirect('/dashboard')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('working_register.html', 
                                 username=request.form.get('username', ''),
                                 email=request.form.get('email', ''))
    
    # GET request - show form
    return render_template('working_register.html')
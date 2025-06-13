"""
Simple register route with minimal dependencies to fix the JSON parsing issues.
"""
import logging
from flask import render_template, url_for, flash, redirect, Blueprint
from flask_login import current_user

from forms import RegistrationForm
from models import User
from app import db

simple_register_bp = Blueprint('simple_register', __name__)
logger = logging.getLogger(__name__)

@simple_register_bp.route('/register-simple', methods=['GET', 'POST'])
def simple_register():
    """
    Registration route with minimal dependencies and error handling.
    """
    logger.debug("Simple register route accessed")
    
    # Redirect if already logged in
    if current_user.is_authenticated:
        # Use direct path instead of url_for to avoid 'str' is not callable error
        return redirect('/dashboard')
    
    form = RegistrationForm()
    
    # Handle form submission
    if form.is_submitted():
        logger.debug(f"Form submitted with data: username={form.username.data}, email={form.email.data}")
        
        try:
            # Manual validation to catch all edge cases
            validation_errors = []
            
            # Check required fields
            if not form.username.data or len(form.username.data.strip()) < 3:
                validation_errors.append(('username', 'Username must be at least 3 characters long'))
            
            if not form.email.data or '@' not in form.email.data:
                validation_errors.append(('email', 'Please enter a valid email address'))
            
            if not form.password.data or len(form.password.data) < 6:
                validation_errors.append(('password', 'Password must be at least 6 characters long'))
            
            if form.password.data != form.confirm_password.data:
                validation_errors.append(('confirm_password', 'Passwords must match'))
            
            # If manual validation fails, display errors
            if validation_errors:
                for field, error in validation_errors:
                    flash(f'{field.title()}: {error}', 'danger')
                logger.warning(f"Manual validation failed: {validation_errors}")
                return render_template('register_simple.html', title='Register', form=form)
            
            # Check WTF validation
            if not form.validate():
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field.title()}: {error}', 'danger')
                logger.warning(f"WTF validation failed: {form.errors}")
                return render_template('register_simple.html', title='Register', form=form)
            
            # Convert email to lowercase for consistency
            email = form.email.data.lower().strip()
            username = form.username.data.strip()
            
            # Check for existing users
            existing_user_by_email = User.query.filter_by(email=email).first()
            if existing_user_by_email:
                flash('Email: That email is already registered. Please use a different one.', 'danger')
                logger.warning(f"Registration attempt with existing email: {email}")
                return render_template('register_simple.html', title='Register', form=form)
            
            existing_user_by_username = User.query.filter_by(username=username).first()
            if existing_user_by_username:
                flash('Username: That username is already taken. Please choose a different one.', 'danger')
                logger.warning(f"Registration attempt with existing username: {username}")
                return render_template('register_simple.html', title='Register', form=form)
            
            # Create new user with explicit error handling
            try:
                user = User()
                user.username = username
                user.email = email
                user.set_password(form.password.data)
                
                # Add to database with transaction
                db.session.add(user)
                db.session.flush()  # Get user ID but don't commit yet
                db.session.commit()
                
                logger.info(f"New user registered successfully: {email} (ID: {user.id})")
                flash('Your account has been created successfully! You can now log in.', 'success')
                return redirect('/stable-login')
                
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Database error during user creation: {str(db_error)}", exc_info=True)
                flash('There was an error creating your account. Please try again.', 'danger')
                return render_template('register_simple.html', title='Register', form=form)
                
        except Exception as e:
            logger.error(f"Critical error during registration: {str(e)}", exc_info=True)
            db.session.rollback()
            flash('An unexpected error occurred. Please try again later.', 'danger')
            return render_template('register_simple.html', title='Register', form=form)
    
    # For GET requests or validation failures, render the form
    return render_template('register_simple.html', title='Register', form=form)
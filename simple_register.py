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
    
    # Check if this is a POST request
    if form.is_submitted():
        try:
            # Validate the form and capture detailed errors
            if form.validate():
                # Convert email to lowercase for case-insensitive matching
                email = form.email.data.lower() if form.email.data else None
                
                # Check for existing user with comprehensive error handling
                existing_user_by_email = User.query.filter_by(email=email).first()
                if existing_user_by_email:
                    form.email.errors.append('That email is already registered. Please use a different one.')
                    logger.warning(f"Registration attempt with existing email: {email}")
                    return render_template('register_simple.html', title='Register', form=form)
                
                existing_user_by_username = User.query.filter_by(username=form.username.data).first()
                if existing_user_by_username:
                    form.username.errors.append('That username is already taken. Please choose a different one.')
                    logger.warning(f"Registration attempt with existing username: {form.username.data}")
                    return render_template('register_simple.html', title='Register', form=form)
                
                # Create new user
                user = User(username=form.username.data, email=email)
                user.set_password(form.password.data)
                
                db.session.add(user)
                db.session.commit()
                
                logger.info(f"New user registered successfully: {email}")
                flash('Your account has been created successfully! You can now log in.', 'success')
                return redirect('/stable-login')
            else:
                # Form validation failed - log and display errors
                logger.warning(f"Form validation errors: {form.errors}")
                
                # Flash specific validation errors
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field.title()}: {error}', 'danger')
                
                return render_template('register_simple.html', title='Register', form=form)
                
        except Exception as e:
            logger.error(f"Critical error during registration: {str(e)}", exc_info=True)
            db.session.rollback()
            flash('There was an unexpected error creating your account. Please try again later.', 'danger')
            return render_template('register_simple.html', title='Register', form=form)
    
    # For GET requests or validation failures, render the form
    return render_template('register_simple.html', title='Register', form=form)
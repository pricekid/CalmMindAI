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
    
    # Check if form submission is valid
    if form.validate_on_submit():
        try:
            # Convert email to lowercase for case-insensitive matching
            email = form.email.data.lower() if form.email.data else None
            user = User(username=form.username.data, email=email)
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Your account has been created successfully! You can now log in.', 'success')
            # Use direct path instead of url_for
            return redirect('/stable-login')  # Use stable login route
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            db.session.rollback()
            flash('There was an error creating your account. Please try again.', 'danger')
            return render_template('register_simple.html', title='Register', form=form)
    else:
        # Log validation errors for debugging
        if form.errors:
            logger.debug(f"Form validation errors: {form.errors}")
    
    # For GET requests or validation failures, render the form
    return render_template('register_simple.html', title='Register', form=form)
"""
Simple register route with minimal dependencies to fix the JSON parsing issues.
Also handles referral codes from invite links.
"""
import logging
from flask import render_template, url_for, flash, redirect, Blueprint, request, session
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
    Handles referral codes from the query parameters.
    """
    logger.debug("Simple register route accessed")
    
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Check for referral code in the query parameters
    referral_code = request.args.get('ref')
    if referral_code:
        # Store the referral code in the session
        session['referral_code'] = referral_code
        logger.info(f"Stored referral code in session: {referral_code}")
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Convert email to lowercase for case-insensitive matching
            email = form.email.data.lower() if form.email.data else None
            user = User(username=form.username.data, email=email)
            user.set_password(form.password.data)
            
            # Generate a unique referral code for this user
            user.referral_code = User.generate_referral_code()
            
            # Check if user was referred by someone
            if 'referral_code' in session:
                referrer_code = session.get('referral_code')
                logger.info(f"User has a referral code in session: {referrer_code}")
                
                # Find the referring user
                referrer = User.query.filter_by(referral_code=referrer_code).first()
                if referrer:
                    logger.info(f"Found referrer: User ID {referrer.id}")
                    user.referred_by = referrer.id
                    # You could add additional logic here, such as giving points or benefits to the referrer
                
                # Clear the referral code from the session after use
                session.pop('referral_code', None)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))  # Use main login route
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            db.session.rollback()
            flash('There was an error creating your account. Please try again.', 'danger')
    
    # Add referral info to the template context if available
    referral_info = None
    if 'referral_code' in session:
        referrer = User.query.filter_by(referral_code=session['referral_code']).first()
        if referrer:
            referral_info = {
                'username': referrer.username
            }
    
    # Use a simplified template to avoid potential rendering issues
    return render_template('register_simple.html', title='Register', form=form, referral_info=referral_info)
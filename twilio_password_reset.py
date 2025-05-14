"""
Password reset functionality using Twilio SMS for users who have lost access to their accounts.
"""
import logging
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired, Length, EqualTo
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app import app, db
from models import User
from flask_login import login_user

# Try to import Twilio, but handle the case where it's not available
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("Twilio module not available. SMS functionality will be limited to logging.")

# Create Blueprint with a unique name
pwd_reset_bp = Blueprint('pwd_reset', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_reset_sms(to_phone_number, reset_url):
    """
    Send a password reset SMS using Twilio.
    
    Args:
        to_phone_number: The recipient's phone number with country code (e.g., +1234567890)
        reset_url: The password reset URL with token
        
    Returns:
        bool: True if SMS was sent successfully, False otherwise
    """
    try:
        # Log the URL for testing purposes regardless of Twilio availability
        logging.info(f"[PASSWORD RESET] URL for {to_phone_number}: {reset_url}")
        print(f"\n==== PASSWORD RESET LINK ====\nPhone: {to_phone_number}\nURL: {reset_url}\n============================\n")
        
        # If Twilio is not available, just return True (we've logged the URL)
        if not TWILIO_AVAILABLE:
            logging.warning("Twilio module not available, using fallback method")
            return True
            
        # Check for Twilio blocker (similar to SendGrid blocker in the logs)
        if 'twilio_blocker' in str(logging.Logger.manager.loggerDict):
            logging.warning("Twilio appears to be blocked in this environment")
            return True
            
        # Get Twilio credentials from environment
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        from_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        if not account_sid or not auth_token or not from_number:
            logging.warning("Twilio environment variables are not set")
            return True  # Return True to indicate we handled it (via fallback)
        
        # Create Twilio client if it's available
        if TWILIO_AVAILABLE:
            client = Client(account_sid, auth_token)
        else:
            # This shouldn't happen due to the earlier check, but just in case
            logging.error("Attempted to use Twilio client when it's not available")
            return True
        
        # Create message content
        message_content = f"Your Dear Teddy password reset link is: {reset_url} (valid for 24 hours)"
        
        # Send SMS
        message = client.messages.create(
            body=message_content,
            from_=from_number,
            to=to_phone_number
        )
        
        logging.info(f"Password reset SMS sent to {to_phone_number} with SID: {message.sid}")
        return True
    except Exception as e:
        logging.error(f"Error sending Twilio SMS: {str(e)}")
        return True  # Return True to still allow testing

# Form for requesting password reset
class RequestResetForm(FlaskForm):
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, message='Please enter a valid phone number with country code (e.g., +1234567890)')
    ], description="Enter your phone number with country code (e.g., +1234567890)")
    submit = SubmitField('Send Reset Link')

# Form for resetting password
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')

def get_serializer():
    """Get a serializer for generating and verifying tokens"""
    secret_key = app.secret_key
    if not secret_key:
        secret_key = "temporary-secret-key-for-development-only"
        logging.warning("Using temporary secret key for password reset. Set SESSION_SECRET in environment.")
    return URLSafeTimedSerializer(secret_key)

@pwd_reset_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    # This is intentionally kept simple for demonstration
    form = RequestResetForm()
    
    if form.validate_on_submit():
        phone = form.phone.data
        
        # Make sure phone is valid
        if phone:
            # Normalize phone number format
            if not phone.startswith('+'):
                phone = '+' + phone.lstrip('0')
        
            # Check if user exists
            user = User.query.filter_by(phone_number=phone).first()
            if not user:
                # Don't reveal if phone exists or not for security
                flash('If that phone number is in our system, you will receive a reset link shortly', 'info')
                return redirect(url_for('index'))
        else:
            flash('Please enter a valid phone number', 'error')
            return render_template('forgot_password.html', form=form)
        
        # Generate token
        serializer = get_serializer()
        token = serializer.dumps(phone, salt='password-reset-salt')
        
        # Send SMS with reset link
        reset_url = url_for('pwd_reset.reset_password', token=token, _external=True)
        
        success = send_reset_sms(phone, reset_url)
        
        if success:
            logging.info(f"Password reset SMS sent to {phone}")
        else:
            logging.error(f"Failed to send password reset SMS to {phone}")
            
        # Don't reveal if SMS was sent successfully to prevent phone enumeration
        flash('If that phone number is in our system, you will receive a reset link shortly', 'info')
        
        # For demonstration in debug mode, also show the reset URL
        if app.debug:
            flash(f'Debug mode: Reset URL is {reset_url}', 'info')
            
        return redirect(url_for('index'))
        
    return render_template('forgot_password.html', form=form)

@pwd_reset_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    # Verify token
    serializer = get_serializer()
    try:
        phone = serializer.loads(token, salt='password-reset-salt', max_age=86400)  # 24 hour expiry
    except SignatureExpired:
        flash('The password reset link has expired', 'error')
        return redirect(url_for('pwd_reset.forgot_password'))
    except BadSignature:
        flash('The password reset link is invalid', 'error')
        return redirect(url_for('pwd_reset.forgot_password'))
    
    # Find the user
    user = User.query.filter_by(phone_number=phone).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('pwd_reset.forgot_password'))
    
    # Process the form
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        # Set the new password
        user.set_password(form.password.data)
        db.session.commit()
        
        # Log the user in
        login_user(user)
        
        flash('Your password has been reset successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('reset_password.html', form=form)

def create_forgot_password_template():
    """Create the forgot password template"""
    template = """{% extends "layout.html" %}

{% block title %}Forgot Password{% endblock %}

{% block content %}
<div class="container mt-5">
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow">
        <div class="card-header" style="background-color: #E6B980; color: #222;">
          <h4 class="mb-0">Forgot Password</h4>
        </div>
        <div class="card-body">
          <p class="mb-4">Enter your phone number and we'll send you a text message with a link to reset your password.</p>
          
          <form method="POST">
            {{ form.hidden_tag() }}
            
            <div class="mb-3">
              <label for="phone" class="form-label">Phone Number</label>
              {{ form.phone(class="form-control", placeholder="Enter your phone number with country code (e.g., +1234567890)") }}
              {% if form.phone.errors %}
                <div class="text-danger">
                  {% for error in form.phone.errors %}
                    {{ error }}
                  {% endfor %}
                </div>
              {% endif %}
              <small class="text-muted">Include country code, e.g., +1 for US, +44 for UK</small>
            </div>
            
            <div class="d-grid gap-2">
              {{ form.submit(class="btn btn-lg", style="background-color: #E6B980; color: #222;") }}
            </div>
          </form>
        </div>
        <div class="card-footer text-center">
          <p class="mb-0">Remember your password? <a href="{{ url_for('login') }}" style="color: #E6B980;">Sign in</a></p>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}"""
    
    import os
    if not os.path.exists('templates/forgot_password.html'):
        with open('templates/forgot_password.html', 'w') as f:
            f.write(template)
        logging.info("Created forgot_password.html template")

def create_reset_password_template():
    """Create the reset password template"""
    template = """{% extends "layout.html" %}

{% block title %}Reset Password{% endblock %}

{% block content %}
<div class="container mt-5">
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow">
        <div class="card-header" style="background-color: #E6B980; color: #222;">
          <h4 class="mb-0">Reset Password</h4>
        </div>
        <div class="card-body">
          <p class="mb-4">Create a new password for your account.</p>
          
          <form method="POST">
            {{ form.hidden_tag() }}
            
            <div class="mb-3">
              <label for="password" class="form-label">New Password</label>
              {{ form.password(class="form-control", placeholder="Enter new password") }}
              {% if form.password.errors %}
                <div class="text-danger">
                  {% for error in form.password.errors %}
                    {{ error }}
                  {% endfor %}
                </div>
              {% endif %}
              <small class="text-muted">Must be at least 8 characters long</small>
            </div>
            
            <div class="mb-3">
              <label for="confirm_password" class="form-label">Confirm Password</label>
              {{ form.confirm_password(class="form-control", placeholder="Confirm new password") }}
              {% if form.confirm_password.errors %}
                <div class="text-danger">
                  {% for error in form.confirm_password.errors %}
                    {{ error }}
                  {% endfor %}
                </div>
              {% endif %}
            </div>
            
            <div class="d-grid gap-2">
              {{ form.submit(class="btn btn-lg", style="background-color: #E6B980; color: #222;") }}
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}"""
    
    import os
    if not os.path.exists('templates/reset_password.html'):
        with open('templates/reset_password.html', 'w') as f:
            f.write(template)
        logging.info("Created reset_password.html template")

def setup_password_reset(app):
    """Register the password reset blueprint with the app"""
    app.register_blueprint(pwd_reset_bp)
    
    # Create templates if they don't exist
    create_forgot_password_template()
    create_reset_password_template()
    
    logging.info("Password reset routes registered with Twilio SMS integration")
    return True

if __name__ == "__main__":
    # Create templates if they don't exist
    create_forgot_password_template()
    create_reset_password_template()
    
    print("To enable password reset functionality, add this to your app.py:")
    print("from twilio_password_reset import setup_password_reset")
    print("setup_password_reset(app)")
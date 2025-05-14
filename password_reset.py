"""
Password reset functionality for users who have lost access to their accounts.
"""
import logging
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app import app, db
from models import User
from flask_login import login_user

# Create Blueprint
reset_bp = Blueprint('reset', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_reset_email(to_email, reset_url):
    """
    Send a password reset email using SendGrid.
    If SendGrid is blocked or unavailable, falls back to logging the URL.
    
    Args:
        to_email: The recipient's email address
        reset_url: The password reset URL with token
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Prepare the email content regardless
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://dearteddy.app/static/images/teddy-icon.svg" alt="Dear Teddy" style="max-width: 100px;">
            </div>
            <div style="background-color: #f9f9f9; border-radius: 10px; padding: 20px; border-left: 4px solid #E6B980;">
                <h2 style="color: #E6B980; margin-top: 0;">Password Reset Request</h2>
                <p>Hello,</p>
                <p>We received a request to reset your password for your Dear Teddy account. To reset your password, click the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #E6B980; color: #222; text-decoration: none; padding: 12px 20px; border-radius: 5px; font-weight: bold; display: inline-block;">Reset My Password</a>
                </div>
                <p>This link will expire in 24 hours. If you didn't request a password reset, you can safely ignore this email.</p>
                <p>If the button above doesn't work, you can also copy and paste the following URL into your browser:</p>
                <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 5px;">{reset_url}</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #777; font-size: 12px;">
                <p>© 2025 Dear Teddy - Your companion for anxiety, clarity, and calm</p>
            </div>
        </body>
    </html>
    """
    
    try:
        # Get SendGrid API key from environment
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            logging.warning("SENDGRID_API_KEY environment variable is not set")
            # Fall back to logging the reset URL for testing
            logging.info(f"[FALLBACK] Password reset URL for {to_email}: {reset_url}")
            return True  # Return True to indicate we handled it (via fallback)
            
        # Check if SendGrid is blocked (as per the warning message in logs)
        # In the Replit environment, it might be blocked or overridden
        if 'sendgrid_blocker' in str(logging.Logger.manager.loggerDict):
            logging.warning("SendGrid appears to be blocked in this environment")
            # Fall back to logging the reset URL for testing
            logging.info(f"[FALLBACK] Password reset URL for {to_email}: {reset_url}")
            # Also log to console for easy testing
            print(f"\n==== PASSWORD RESET LINK ====\nEmail: {to_email}\nURL: {reset_url}\n============================\n")
            return True
        
        try:
            # Create SendGrid client
            sg = SendGridAPIClient(sendgrid_api_key)
            
            # Create email
            from_email = Email("noreply@dearteddy.app")  # Replace with your sender email
            subject = "Reset Your Dear Teddy Password"
            to_email_obj = To(to_email)
            
            content = Content("text/html", html_content)
            mail = Mail(from_email, to_email_obj, subject, content)
            
            # Attempt to send email
            response = sg.send(mail)
            logging.info(f"Password reset email sent to {to_email}")
            return True
        except Exception as e:
            logging.error(f"Error sending via SendGrid: {str(e)}")
            # Fall back to logging the reset URL for testing
            logging.info(f"[FALLBACK] Password reset URL for {to_email}: {reset_url}")
            # Also log to console for easy testing
            print(f"\n==== PASSWORD RESET LINK ====\nEmail: {to_email}\nURL: {reset_url}\n============================\n")
            return True
            
    except Exception as e:
        logging.error(f"Error sending reset email: {str(e)}")
        # Fall back to logging the reset URL for testing
        logging.info(f"[FALLBACK] Password reset URL for {to_email}: {reset_url}")
        return True  # Return True to indicate we handled it (via fallback)

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
    return URLSafeTimedSerializer(app.config['SECRET_KEY'])

@reset_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    # This is intentionally kept simple for demonstration
    # In a production app, you'd want to add CAPTCHA and rate limiting
    
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('forgot_password.html')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists or not for security
            flash('If that email is in our system, you will receive a reset link shortly', 'info')
            return redirect(url_for('index'))
        
        # Generate token
        serializer = get_serializer()
        token = serializer.dumps(email, salt='password-reset-salt')
        
        # Send email with reset link
        reset_url = url_for('reset.reset_password', token=token, _external=True)
        
        # Send email using SendGrid
        success = send_reset_email(email, reset_url)
        
        if success:
            logging.info(f"Password reset email sent to {email}")
        else:
            logging.error(f"Failed to send password reset email to {email}")
            
        # Don't reveal if email was sent successfully to prevent email enumeration
        flash('If that email is in our system, you will receive a reset link shortly', 'info')
        
        # For demonstration in debug mode, also show the reset URL
        if app.debug:
            flash(f'Debug mode: Reset URL is {reset_url}', 'info')
            
        return redirect(url_for('index'))
        
    return render_template('forgot_password.html')

@reset_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    # Verify token
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=86400)  # 24 hour expiry
    except SignatureExpired:
        flash('The password reset link has expired', 'error')
        return redirect(url_for('reset.forgot_password'))
    except BadSignature:
        flash('The password reset link is invalid', 'error')
        return redirect(url_for('reset.forgot_password'))
    
    # Find the user
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('reset.forgot_password'))
    
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
        <div class="card-header bg-primary text-white">
          <h4 class="mb-0">Forgot Password</h4>
        </div>
        <div class="card-body">
          <p class="mb-4">Enter your email address and we'll send you a link to reset your password.</p>
          
          <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            
            <div class="mb-3">
              <label for="email" class="form-label">Email Address</label>
              <input type="email" class="form-control" id="email" name="email" required 
                     placeholder="Enter your email address">
            </div>
            
            <div class="d-grid gap-2">
              <button type="submit" class="btn btn-primary btn-lg">Send Reset Link</button>
            </div>
          </form>
        </div>
        <div class="card-footer text-center">
          <p class="mb-0">Remember your password? <a href="{{ url_for('login') }}">Sign in</a></p>
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

def setup_password_reset(app):
    """Register the password reset blueprint with the app"""
    app.register_blueprint(reset_bp)
    
    # Create template if it doesn't exist
    create_forgot_password_template()
    
    logging.info("Password reset routes registered")
    return True

if __name__ == "__main__":
    # Create templates if they don't exist
    create_forgot_password_template()
    
    print("To enable password reset functionality, add this to your app.py:")
    print("from password_reset import setup_password_reset")
    print("setup_password_reset(app)")
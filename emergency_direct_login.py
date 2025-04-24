"""
Standalone emergency login system that bypasses CSRF protection.
This is a TEMPORARY solution to regain access when the main login system is broken.
"""
import os
import logging
from flask import Blueprint, request, redirect, flash, Response
from flask_login import login_user, current_user
from models import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint - will be registered in main.py
emergency_bp = Blueprint('emergency', __name__)

@emergency_bp.route('/emergency-login', methods=['GET', 'POST'])
def emergency_login():
    """
    Provides a bare-bones login form with no CSRF protection or JSON parsing.
    FOR EMERGENCY USE ONLY when regular login is broken.
    """
    # Check if user is already logged in
    if current_user.is_authenticated:
        # If logged in as admin, redirect to admin dashboard
        if hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
            return redirect('/admin/dashboard')
        # Otherwise, go to the regular dashboard using direct path
        return redirect('/dashboard')
    
    # Process form submission
    error_message = None
    success = False
    
    if request.method == 'POST':
        try:
            # Get form data directly from request
            email = request.form.get('email', '').lower() if request.form.get('email') else ''
            password = request.form.get('password', '')
            
            # Basic validation
            if not email or not password:
                error_message = 'Email and password are required.'
            else:
                # Find user
                user = User.query.filter_by(email=email).first()
                
                # Validate credentials
                if user and user.check_password(password):
                    login_user(user, remember=True)
                    return redirect('/dashboard')
                else:
                    error_message = 'Login unsuccessful. Please check your email and password.'
        except Exception as e:
            # Log error, but don't expose details to user
            logger.error(f"Emergency login error: {str(e)}")
            error_message = 'An error occurred during login. Please try again.'
    
    # Simple HTML form with no CSRF token or complex template
    emergency_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Login - Calm Journey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #1a1a1a; color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 500px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
            h1 {{ color: #0d6efd; text-align: center; margin-bottom: 20px; }}
            .error {{ background-color: #dc3545; color: white; padding: 10px; border-radius: 4px; margin-bottom: 20px; }}
            .success {{ background-color: #198754; color: white; padding: 10px; border-radius: 4px; margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 5px; }}
            input[type="email"], input[type="password"] {{ width: 100%; padding: 8px; margin-bottom: 15px; background-color: #343a40; border: 1px solid #495057; color: #f8f9fa; border-radius: 4px; }}
            button {{ width: 100%; padding: 10px; background-color: #0d6efd; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
            .register-link {{ text-align: center; margin-top: 15px; }}
            .warning {{ background-color: #ffc107; padding: 10px; border-radius: 4px; margin-top: 20px; color: #212529; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Emergency Login</h1>
            
            {f'<div class="error">{error_message}</div>' if error_message else ''}
            
            <form method="POST" action="/emergency-login">
                <div>
                    <label for="email">Email Address:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Login Now</button>
            </form>
            
            <div class="warning">
                <strong>Note:</strong> This is an emergency login page with reduced security features.
                It should only be used when the regular login system is not working.
            </div>
        </div>
    </body>
    </html>
    """
    
    return Response(emergency_html, 200, content_type='text/html')
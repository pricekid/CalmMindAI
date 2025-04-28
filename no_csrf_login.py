"""
Standalone login system without CSRF protection.
This bypasses the Flask-WTF CSRF system entirely for maximum compatibility.
"""
import os
import logging
from flask import Blueprint, render_template, redirect, request, flash, Response
from flask_login import login_user, current_user, logout_user
from models import User
from werkzeug.security import check_password_hash

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
no_csrf_bp = Blueprint('no_csrf', __name__)

@no_csrf_bp.route('/direct-login', methods=['GET', 'POST'])
def direct_login():
    """
    Login route without any CSRF protection.
    This is a last-resort option when standard login is failing.
    """
    # Check if user is already logged in
    if current_user.is_authenticated:
        logger.info(f"User {current_user.id} is already logged in, redirecting to dashboard")
        return redirect('/dashboard')
    
    error_message = None
    
    # Process login form submission
    if request.method == 'POST':
        try:
            # Get form data directly
            email = request.form.get('email', '').lower()
            password = request.form.get('password', '')
            remember = request.form.get('remember') == 'on'
            
            logger.info(f"Login attempt for email: {email}")
            
            # Basic validation
            if not email or not password:
                error_message = 'Email and password are required.'
                logger.warning(f"Login attempt missing email or password: {email}")
            else:
                # Find user by email
                user = User.query.filter_by(email=email).first()
                
                if user and user.check_password(password):
                    # Successful login
                    login_user(user, remember=remember)
                    logger.info(f"Successful login for user ID: {user.id}")
                    
                    # Redirect to dashboard
                    return redirect('/dashboard')
                else:
                    # Failed login
                    error_message = 'Invalid email or password.'
                    logger.warning(f"Failed login attempt for email: {email}")
        
        except Exception as e:
            # Log the error
            logger.error(f"Login error: {str(e)}")
            error_message = 'An unexpected error occurred. Please try again.'
    
    # Render login form with direct HTML (no template)
    login_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Direct Login - No CSRF</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/css/bootstrap.min.css">
        <style>
            body {{ background-color: #1a1a1a; color: #f8f9fa; padding: 20px; }}
            .container {{ max-width: 500px; margin: 40px auto; }}
            .card {{ background-color: #212529; border: none; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.3); }}
            .card-header {{ background-color: #0d6efd; color: white; border-radius: 10px 10px 0 0; }}
            .form-control {{ background-color: #343a40; color: #f8f9fa; border-color: #495057; }}
            .form-control:focus {{ background-color: #343a40; color: #f8f9fa; }}
            .btn-primary {{ background-color: #0d6efd; }}
            .alert {{ margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h3 class="mb-0 text-center">Direct Login (No CSRF)</h3>
                </div>
                <div class="card-body">
                    {f'<div class="alert alert-danger">{error_message}</div>' if error_message else ''}
                    
                    <form method="POST" action="/direct-login">
                        <div class="mb-3">
                            <label for="email" class="form-label">Email Address</label>
                            <input type="email" class="form-control" id="email" name="email" required>
                        </div>
                        <div class="mb-3">
                            <label for="password" class="form-label">Password</label>
                            <input type="password" class="form-control" id="password" name="password" required>
                        </div>
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="remember" name="remember">
                            <label class="form-check-label" for="remember">Remember Me</label>
                        </div>
                        <div class="d-grid">
                            <button type="submit" class="btn btn-primary">Login</button>
                        </div>
                    </form>
                    
                    <div class="mt-3 text-center">
                        <p>Don't have an account? <a href="/register">Sign Up</a></p>
                    </div>
                </div>
                <div class="card-footer text-center text-muted">
                    <small>This is a special login form without CSRF protection.</small>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return Response(login_html, 200, content_type='text/html')
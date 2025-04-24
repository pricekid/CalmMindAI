"""
Super basic login route with minimal dependencies to fix the JSON parsing issues.
"""
import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, Blueprint
from flask_login import LoginManager, login_user, current_user, logout_user
from models import User
from app import db

logger = logging.getLogger(__name__)
basic_login_bp = Blueprint('basic_login', __name__)

@basic_login_bp.route('/basic-login', methods=['GET', 'POST'])
def basic_login():
    """
    Login route with minimal dependencies and error handling.
    """
    # Check if user is already logged in
    if current_user.is_authenticated:
        # If logged in as admin, redirect to admin dashboard
        if hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
            # Use direct path instead of url_for
            return redirect('/admin/dashboard')
        # Otherwise, go to the regular dashboard using direct path
        return redirect('/dashboard')
    
    # Get any flash messages for display
    flash_messages = []
    from flask import get_flashed_messages
    try:
        flashed = get_flashed_messages(with_categories=True)
        flash_messages = [{"category": category, "message": message} for category, message in flashed]
    except Exception as flash_error:
        logger.error(f"Error getting flash messages: {str(flash_error)}")
    
    # Process form submission
    if request.method == 'POST':
        try:
            # Get form data directly from request
            email = request.form.get('email', '').lower() if request.form.get('email') else ''
            password = request.form.get('password', '')
            remember = 'remember' in request.form
            
            # Skip CSRF validation for emergency login
            logger.info("Skipping CSRF validation for emergency login")
            
            # Validate submission
            if not email or not password:
                flash('Email and password are required.', 'danger')
                flash_messages.append({"category": "danger", "message": "Email and password are required."})
            else:
                # Find user
                user = User.query.filter_by(email=email).first()
                
                # Validate credentials
                if user and user.check_password(password):
                    login_user(user, remember=remember)
                    next_page = request.args.get('next')
                    
                    # Redirect based on next parameter
                    if next_page and next_page.startswith('/admin'):
                        flash('You need admin privileges to access that page.', 'warning')
                        return redirect('/dashboard')
                    
                    return redirect(next_page or '/dashboard')
                else:
                    flash('Login unsuccessful. Please check your email and password.', 'danger')
                    flash_messages.append({"category": "danger", "message": "Login unsuccessful. Please check your email and password."})
        except Exception as e:
            # Log error, but don't expose details to user
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')
            flash_messages.append({"category": "danger", "message": "An error occurred during login. Please try again."})
    
    # Generate a CSRF token directly through Flask's built-in functions
    csrf_token = "emergency_token"  # Default fallback
    try:
        from flask_wtf.csrf import generate_csrf
        csrf_token = generate_csrf()
        logger.debug("Generated CSRF token for login page")
    except Exception as csrf_error:
        logger.error(f"Could not generate CSRF token: {str(csrf_error)}")
    
    # Create flash messages HTML
    flash_html = ""
    for msg in flash_messages:
        category = msg.get("category", "info")
        message = msg.get("message", "")
        flash_html += f"""
        <div class="alert alert-{category} alert-dismissible fade show" role="alert">
            {message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        """
    
    # For GET requests, render an inline HTML form to avoid template rendering issues
    emergency_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login to Calm Journey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/css/bootstrap.min.css">
        <link rel="stylesheet" href="/static/css/styles.css">
        <style>
            body {{ background-color: #1a1a1a; color: #f8f9fa; }}
            .card {{ background-color: #212529; border: none; }}
            .card-header {{ background-color: #0d6efd; color: white; }}
            .form-control {{ background-color: #343a40; color: #f8f9fa; border-color: #495057; }}
            .form-control:focus {{ background-color: #343a40; color: #f8f9fa; }}
            .btn-primary {{ background-color: #0d6efd; }}
            .alert {{ padding: 10px; margin-bottom: 15px; border-radius: 4px; }}
            .alert-danger {{ background-color: #dc3545; color: white; }}
            .alert-success {{ background-color: #198754; color: white; }}
            .alert-info {{ background-color: #0dcaf0; color: white; }}
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <div class="row">
                <div class="col-md-6 mx-auto">
                    <!-- Flash messages -->
                    {flash_html}
                    
                    <div class="card shadow">
                        <div class="card-header">
                            <h3 class="mb-0">Login to Calm Journey</h3>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="/basic-login">
                                <input type="hidden" name="csrf_token" value="{csrf_token}">
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
                                    <label class="form-check-label" for="remember">Remember me</label>
                                </div>
                                <div class="d-grid">
                                    <button type="submit" class="btn btn-primary">Login</button>
                                </div>
                            </form>
                            <div class="mt-3 text-center">
                                <p>Don't have an account? <a href="/register">Sign up</a></p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Bootstrap and custom scripts -->
        <script src="/static/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    from flask import Response
    return Response(emergency_html, 200, content_type='text/html')
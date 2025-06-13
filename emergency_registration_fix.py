#!/usr/bin/env python3
"""
Emergency registration system that bypasses the problematic areas.
This creates a completely isolated registration route that should work in production.
"""

from flask import Blueprint, request, render_template_string, redirect, flash, url_for
from werkzeug.security import generate_password_hash
import uuid
import logging
import os
import sys

# Add the current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db

# Create blueprint
emergency_register_bp = Blueprint('emergency_register', __name__)

# Simple HTML template embedded in Python
EMERGENCY_REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - Dear Teddy</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .card { border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .btn-primary { background-color: #1D4D4F; border-color: #1D4D4F; }
        .btn-primary:hover { background-color: #16393b; border-color: #16393b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card mt-5">
                    <div class="card-header text-center">
                        <h3>Create Your Account</h3>
                        <p class="text-muted">Join Dear Teddy for personalized journaling</p>
                    </div>
                    <div class="card-body">
                        {% if error %}
                            <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        
                        {% if success %}
                            <div class="alert alert-success">{{ success }}</div>
                            <div class="text-center">
                                <a href="/stable-login" class="btn btn-primary">Continue to Login</a>
                            </div>
                        {% else %}
                        <form method="POST">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="username" name="username" 
                                       value="{{ username or '' }}" required minlength="3" maxlength="64">
                            </div>
                            
                            <div class="mb-3">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" name="email" 
                                       value="{{ email or '' }}" required maxlength="120">
                            </div>
                            
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" 
                                       required minlength="6" maxlength="128">
                            </div>
                            
                            <div class="mb-3">
                                <label for="confirm_password" class="form-label">Confirm Password</label>
                                <input type="password" class="form-control" id="confirm_password" name="confirm_password" 
                                       required minlength="6" maxlength="128">
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">Create Account</button>
                            </div>
                        </form>
                        
                        <div class="text-center mt-3">
                            <p>Already have an account? <a href="/stable-login">Log in here</a></p>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

@emergency_register_bp.route('/emergency-register', methods=['GET', 'POST'])
def emergency_register():
    """Emergency registration route that bypasses complex dependencies"""
    
    if request.method == 'GET':
        return render_template_string(EMERGENCY_REGISTER_TEMPLATE)
    
    # Handle POST request
    try:
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Basic validation
        if not username or len(username) < 3:
            return render_template_string(EMERGENCY_REGISTER_TEMPLATE, 
                                        error="Username must be at least 3 characters long",
                                        username=username, email=email)
        
        if not email or '@' not in email:
            return render_template_string(EMERGENCY_REGISTER_TEMPLATE, 
                                        error="Please enter a valid email address",
                                        username=username, email=email)
        
        if not password or len(password) < 6:
            return render_template_string(EMERGENCY_REGISTER_TEMPLATE, 
                                        error="Password must be at least 6 characters long",
                                        username=username, email=email)
        
        if password != confirm_password:
            return render_template_string(EMERGENCY_REGISTER_TEMPLATE, 
                                        error="Passwords do not match",
                                        username=username, email=email)
        
        # Import User model dynamically to avoid import issues
        from models import User
        
        # Check for existing users
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return render_template_string(EMERGENCY_REGISTER_TEMPLATE, 
                                        error="That email is already registered",
                                        username=username)
        
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            return render_template_string(EMERGENCY_REGISTER_TEMPLATE, 
                                        error="That username is already taken",
                                        email=email)
        
        # Create new user
        new_user = User()
        new_user.id = str(uuid.uuid4())
        new_user.username = username
        new_user.email = email
        new_user.password_hash = generate_password_hash(password)
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        logging.info(f"Emergency registration successful: {email}")
        
        return render_template_string(EMERGENCY_REGISTER_TEMPLATE, 
                                    success="Account created successfully! You can now log in.")
        
    except Exception as e:
        logging.error(f"Emergency registration error: {str(e)}", exc_info=True)
        db.session.rollback()
        
        return render_template_string(EMERGENCY_REGISTER_TEMPLATE, 
                                    error="An error occurred creating your account. Please try again.",
                                    username=request.form.get('username', ''),
                                    email=request.form.get('email', ''))

def register_emergency_routes(app):
    """Register the emergency registration blueprint"""
    app.register_blueprint(emergency_register_bp)
    logging.info("Emergency registration route registered at /emergency-register")

if __name__ == "__main__":
    print("Emergency registration module loaded successfully")
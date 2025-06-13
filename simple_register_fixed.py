
#!/usr/bin/env python3
"""
Clean, simple registration blueprint that uses the shared database instance correctly.
"""
from flask import Blueprint, request, render_template_string, redirect, flash, jsonify
from werkzeug.security import generate_password_hash
import uuid
import re

# Import the shared database instance - DO NOT create a new one
from extensions import db

simple_register_bp = Blueprint('simple_register_fixed', __name__)

# Simple registration template
REGISTRATION_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Simple Registration - Dear Teddy</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; background-color: #1a1a1a; color: #ffffff; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #ffffff; }
        input[type="text"], input[type="email"], input[type="password"] { 
            width: 100%; padding: 10px; border: 1px solid #444; border-radius: 4px; 
            background-color: #333; color: #ffffff; 
        }
        .btn { padding: 12px 24px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background-color: #0056b3; }
        .error { color: #dc3545; margin-top: 10px; }
        .success { color: #28a745; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Create Account - Dear Teddy</h1>
    
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    
    {% if success %}
        <div class="success">{{ success }}</div>
    {% else %}
        <form method="POST" action="/register-simple">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <div class="form-group">
                <label for="confirm_password">Confirm Password:</label>
                <input type="password" id="confirm_password" name="confirm_password" required>
            </div>
            
            <button type="submit" class="btn">Create Account</button>
        </form>
        
        <p><a href="/stable-login" style="color: #007bff;">Already have an account? Login</a></p>
    {% endif %}
</body>
</html>
'''

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Basic password validation"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@simple_register_bp.route('/register-simple', methods=['GET', 'POST'])
def register_simple():
    """Simple registration route with proper error handling"""
    
    if request.method == 'GET':
        return render_template_string(REGISTRATION_TEMPLATE)
    
    # Handle POST request
    try:
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate input
        if not username or not email or not password or not confirm_password:
            return render_template_string(REGISTRATION_TEMPLATE, 
                                        error="All fields are required")
        
        if len(username) < 3:
            return render_template_string(REGISTRATION_TEMPLATE, 
                                        error="Username must be at least 3 characters long")
        
        if not validate_email(email):
            return render_template_string(REGISTRATION_TEMPLATE, 
                                        error="Please enter a valid email address")
        
        valid_password, password_msg = validate_password(password)
        if not valid_password:
            return render_template_string(REGISTRATION_TEMPLATE, 
                                        error=password_msg)
        
        if password != confirm_password:
            return render_template_string(REGISTRATION_TEMPLATE, 
                                        error="Passwords do not match")
        
        # Import User model here to avoid circular imports
        from models import User
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                error_msg = "Username already taken"
            else:
                error_msg = "Email already registered"
            return render_template_string(REGISTRATION_TEMPLATE, error=error_msg)
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        new_user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            demographics_collected=False,
            welcome_message_shown=False,
            notifications_enabled=True
        )
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        # Success response
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    success=f"Account created successfully! You can now login with username: {username}")
        
    except Exception as e:
        # Log the error and rollback
        print(f"Registration error: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
        
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    error="Registration failed due to a server error. Please try again.")

# Health check endpoint
@simple_register_bp.route('/register-simple/health')
def register_health():
    """Health check for the registration system"""
    try:
        # Test database connection
        from models import User
        User.query.first()
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

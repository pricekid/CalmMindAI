"""
Standalone registration system that bypasses SQLAlchemy initialization issues.
This creates users directly through raw SQL to avoid the Flask-SQLAlchemy model issues.
"""
import os
import psycopg2
import uuid
import hashlib
from flask import Blueprint, request, render_template_string, flash, redirect, url_for
from werkzeug.security import generate_password_hash

standalone_register_bp = Blueprint('standalone_register', __name__)

# Simple registration template
REGISTRATION_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - Dear Teddy</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #333;
            margin: 0;
            font-size: 2rem;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        input[type="text"], input[type="email"], input[type="password"] {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="email"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #5a6fd8;
        }
        .error {
            color: #e74c3c;
            margin-bottom: 1rem;
            padding: 0.5rem;
            background: #fdf2f2;
            border-radius: 5px;
            border-left: 4px solid #e74c3c;
        }
        .success {
            color: #27ae60;
            margin-bottom: 1rem;
            padding: 0.5rem;
            background: #f0f9f0;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
        }
        .links {
            text-align: center;
            margin-top: 1rem;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
        }
        .links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Dear Teddy</h1>
            <p>Join our mental wellness community</p>
        </div>
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if success %}
            <div class="success">{{ success }}</div>
        {% endif %}
        
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required 
                       value="{{ request.form.username if request.form.username else '' }}"
                       minlength="3" maxlength="20">
            </div>
            
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required 
                       value="{{ request.form.email if request.form.email else '' }}">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required 
                       minlength="6">
            </div>
            
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="confirm_password" required 
                       minlength="6">
            </div>
            
            <button type="submit" class="btn">Create Account</button>
        </form>
        
        <div class="links">
            <a href="/stable-login">Already have an account? Sign in</a>
        </div>
    </div>
</body>
</html>
"""

def get_db_connection():
    """Get direct PostgreSQL connection bypassing SQLAlchemy"""
    try:
        return psycopg2.connect(os.environ.get('DATABASE_URL'))
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def user_exists(username, email):
    """Check if user already exists"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM \"user\" WHERE username = %s OR email = %s",
            (username, email)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Error checking user existence: {e}")
        if conn:
            conn.close()
        return False

def create_user(username, email, password):
    """Create user with direct SQL insert"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        # Insert new user
        cursor.execute("""
            INSERT INTO "user" (id, username, email, password_hash, created_at, 
                              demographics_collected, notifications_enabled, 
                              morning_reminder_enabled, evening_reminder_enabled,
                              sms_notifications_enabled, welcome_message_shown)
            VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
        """, (user_id, username, email, password_hash, False, True, True, True, False, False))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

@standalone_register_bp.route('/standalone-register', methods=['GET', 'POST'])
def standalone_register():
    """Standalone registration that bypasses SQLAlchemy completely"""
    if request.method == 'GET':
        return render_template_string(REGISTRATION_TEMPLATE)
    
    # Handle POST request
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validation
    if not username or not email or not password:
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    error="All fields are required")
    
    if len(username) < 3:
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    error="Username must be at least 3 characters")
    
    if len(password) < 6:
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    error="Password must be at least 6 characters")
    
    if password != confirm_password:
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    error="Passwords do not match")
    
    # Check if user already exists
    if user_exists(username, email):
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    error="Username or email already exists")
    
    # Create the user
    if create_user(username, email, password):
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    success="Account created successfully! You can now sign in.")
    else:
        return render_template_string(REGISTRATION_TEMPLATE, 
                                    error="Registration failed. Please try again.")

def register_standalone_routes(app):
    """Register the standalone registration blueprint"""
    app.register_blueprint(standalone_register_bp)
    print("Standalone registration route registered at /standalone-register")
"""
Completely isolated registration system for production environments.
This operates independently of Flask-SQLAlchemy to avoid initialization issues.
"""
import os
import sys
import logging
from flask import Flask, request, render_template_string, redirect, url_for
import psycopg2
import uuid
from werkzeug.security import generate_password_hash
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create minimal Flask app
isolated_app = Flask(__name__)
isolated_app.secret_key = os.environ.get("SESSION_SECRET", "fallback_key")

# Simple registration template
REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Join Dear Teddy</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .card {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 450px;
        }
        .logo {
            text-align: center;
            margin-bottom: 2.5rem;
        }
        .logo h1 {
            color: #333;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .logo p {
            color: #666;
            font-size: 1.1rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .message {
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            text-align: center;
            font-weight: 500;
        }
        .error {
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
        }
        .success {
            background: #f0fdf4;
            color: #16a34a;
            border: 1px solid #bbf7d0;
        }
        .footer {
            text-align: center;
            margin-top: 2rem;
        }
        .footer a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">
            <h1>Dear Teddy</h1>
            <p>Your personal wellness companion</p>
        </div>
        
        {% if message %}
        <div class="message {{ message_type }}">
            {{ message }}
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required 
                       minlength="3" maxlength="20" 
                       value="{{ username or '' }}"
                       placeholder="Choose a unique username">
            </div>
            
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" required 
                       value="{{ email or '' }}"
                       placeholder="your@email.com">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required 
                       minlength="6" placeholder="At least 6 characters">
            </div>
            
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="confirm_password" required 
                       minlength="6" placeholder="Confirm your password">
            </div>
            
            <button type="submit" class="btn">Create Account</button>
        </form>
        
        <div class="footer">
            <a href="/stable-login">Already have an account? Sign in</a>
        </div>
    </div>
</body>
</html>
"""

def get_database_connection():
    """Get database connection using environment variables"""
    try:
        # Try DATABASE_URL first
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url)
        
        # Fall back to individual components
        return psycopg2.connect(
            host=os.environ.get('PGHOST', 'localhost'),
            database=os.environ.get('PGDATABASE', 'postgres'),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD', ''),
            port=os.environ.get('PGPORT', '5432')
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def validate_email_format(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def check_existing_user(username, email):
    """Check if username or email already exists"""
    conn = get_database_connection()
    if not conn:
        return True  # Assume exists if can't check
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM "user" WHERE username = %s OR email = %s',
            (username.lower(), email.lower())
        )
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
    except Exception as e:
        logger.error(f"Error checking existing user: {e}")
        if conn:
            conn.close()
        return True

def create_new_user(username, email, password):
    """Create new user in database"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        # Insert user with default values
        cursor.execute("""
            INSERT INTO "user" (
                id, username, email, password_hash, created_at,
                demographics_collected, notifications_enabled,
                morning_reminder_enabled, evening_reminder_enabled,
                sms_notifications_enabled, welcome_message_shown
            ) VALUES (
                %s, %s, %s, %s, NOW(),
                FALSE, TRUE, TRUE, TRUE, FALSE, FALSE
            )
        """, (user_id, username, email, password_hash))
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"User created successfully: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

@isolated_app.route('/isolated-register', methods=['GET', 'POST'])
def isolated_register():
    """Isolated registration endpoint"""
    if request.method == 'GET':
        return render_template_string(REGISTER_TEMPLATE)
    
    # Handle POST request
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Store form values for template
    form_data = {
        'username': username,
        'email': email
    }
    
    # Validation
    if not username or not email or not password:
        return render_template_string(REGISTER_TEMPLATE,
                                    message="Please fill in all fields",
                                    message_type="error",
                                    **form_data)
    
    if len(username) < 3:
        return render_template_string(REGISTER_TEMPLATE,
                                    message="Username must be at least 3 characters",
                                    message_type="error",
                                    **form_data)
    
    if not validate_email_format(email):
        return render_template_string(REGISTER_TEMPLATE,
                                    message="Please enter a valid email address",
                                    message_type="error",
                                    **form_data)
    
    if len(password) < 6:
        return render_template_string(REGISTER_TEMPLATE,
                                    message="Password must be at least 6 characters",
                                    message_type="error",
                                    **form_data)
    
    if password != confirm_password:
        return render_template_string(REGISTER_TEMPLATE,
                                    message="Passwords do not match",
                                    message_type="error",
                                    **form_data)
    
    # Check if user already exists
    if check_existing_user(username, email):
        return render_template_string(REGISTER_TEMPLATE,
                                    message="Username or email already exists",
                                    message_type="error",
                                    **form_data)
    
    # Create the user
    if create_new_user(username, email, password):
        return render_template_string(REGISTER_TEMPLATE,
                                    message="Account created successfully! You can now sign in.",
                                    message_type="success")
    else:
        return render_template_string(REGISTER_TEMPLATE,
                                    message="Registration failed. Please try again.",
                                    message_type="error",
                                    **form_data)

@isolated_app.route('/')
def index():
    """Redirect to registration"""
    return redirect(url_for('isolated_register'))

if __name__ == '__main__':
    # Run as standalone app for testing
    isolated_app.run(host='0.0.0.0', port=5001, debug=True)
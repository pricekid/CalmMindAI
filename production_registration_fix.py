"""
Production registration fix that bypasses SQLAlchemy completely.
This creates a direct database registration system for production environments.
"""
import os
import psycopg2
import uuid
import hashlib
from flask import Blueprint, request, jsonify, render_template_string
from werkzeug.security import generate_password_hash
import re

production_fix_bp = Blueprint('production_fix', __name__)

# Minimal HTML template for registration
MINIMAL_REGISTRATION = """
<!DOCTYPE html>
<html>
<head>
    <title>Register - Dear Teddy</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .error { color: red; margin-bottom: 15px; }
        .success { color: green; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h2>Register for Dear Teddy</h2>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    {% if success %}<div class="success">{{ success }}</div>{% endif %}
    <form method="POST">
        <div class="form-group">
            <label>Username:</label>
            <input type="text" name="username" required minlength="3" value="{{ request.form.username or '' }}">
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email" required value="{{ request.form.email or '' }}">
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" name="password" required minlength="6">
        </div>
        <div class="form-group">
            <label>Confirm Password:</label>
            <input type="password" name="confirm_password" required minlength="6">
        </div>
        <button type="submit">Create Account</button>
    </form>
    <p><a href="/stable-login">Already have an account? Sign in</a></p>
</body>
</html>
"""

def get_direct_db_connection():
    """Get direct PostgreSQL connection using environment variables"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            # Try individual components
            conn = psycopg2.connect(
                host=os.environ.get('PGHOST', 'localhost'),
                database=os.environ.get('PGDATABASE', 'postgres'),
                user=os.environ.get('PGUSER', 'postgres'),
                password=os.environ.get('PGPASSWORD', ''),
                port=os.environ.get('PGPORT', '5432')
            )
        else:
            conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def validate_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def check_user_exists_direct(username, email):
    """Check if user exists using direct SQL"""
    conn = get_direct_db_connection()
    if not conn:
        return True  # Assume exists if can't check
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM "user" WHERE username = %s OR email = %s',
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
        return True  # Assume exists on error

def create_user_direct(username, email, password):
    """Create user with direct SQL insert"""
    conn = get_direct_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        # Insert with all required fields
        cursor.execute("""
            INSERT INTO "user" (
                id, username, email, password_hash, created_at, 
                demographics_collected, notifications_enabled, 
                morning_reminder_enabled, evening_reminder_enabled,
                sms_notifications_enabled, welcome_message_shown
            ) VALUES (%s, %s, %s, %s, NOW(), FALSE, TRUE, TRUE, TRUE, FALSE, FALSE)
        """, (user_id, username, email, password_hash))
        
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

@production_fix_bp.route('/production-register', methods=['GET', 'POST'])
def production_register():
    """Production registration that bypasses all Flask-SQLAlchemy issues"""
    if request.method == 'GET':
        return render_template_string(MINIMAL_REGISTRATION)
    
    # Handle POST
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validation
    if not username or not email or not password:
        return render_template_string(MINIMAL_REGISTRATION, error="All fields are required")
    
    if len(username) < 3:
        return render_template_string(MINIMAL_REGISTRATION, error="Username must be at least 3 characters")
    
    if not validate_email(email):
        return render_template_string(MINIMAL_REGISTRATION, error="Please enter a valid email address")
    
    if len(password) < 6:
        return render_template_string(MINIMAL_REGISTRATION, error="Password must be at least 6 characters")
    
    if password != confirm_password:
        return render_template_string(MINIMAL_REGISTRATION, error="Passwords do not match")
    
    # Check if user exists
    if check_user_exists_direct(username, email):
        return render_template_string(MINIMAL_REGISTRATION, error="Username or email already exists")
    
    # Create user
    if create_user_direct(username, email, password):
        return render_template_string(MINIMAL_REGISTRATION, 
                                    success="Account created successfully! You can now sign in.")
    else:
        return render_template_string(MINIMAL_REGISTRATION, 
                                    error="Registration failed. Please try again.")

@production_fix_bp.route('/api/production-register', methods=['POST'])
def api_production_register():
    """API endpoint for production registration"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email address'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user exists
        if check_user_exists_direct(username, email):
            return jsonify({'error': 'Username or email already exists'}), 400
        
        # Create user
        if create_user_direct(username, email, password):
            return jsonify({'success': True, 'message': 'Account created successfully'})
        else:
            return jsonify({'error': 'Registration failed'}), 500
            
    except Exception as e:
        print(f"API registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

def register_production_fix(app):
    """Register the production fix blueprint"""
    app.register_blueprint(production_fix_bp)
    print("Production registration fix registered at /production-register")
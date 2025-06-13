"""
Final registration solution - completely isolated from Flask app complexities
"""
import os
import uuid
import psycopg2
import re
from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash

final_register_bp = Blueprint('final_register', __name__)

def get_db_connection():
    """Get database connection using environment variables"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url)
        return psycopg2.connect(
            host=os.environ.get('PGHOST', 'localhost'),
            database=os.environ.get('PGDATABASE', 'postgres'),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD', ''),
            port=os.environ.get('PGPORT', '5432')
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def validate_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def user_exists(username, email):
    """Check if user already exists"""
    conn = get_db_connection()
    if not conn:
        return True
    
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
        print(f"User exists check error: {e}")
        if conn:
            conn.close()
        return True

def create_user(username, email, password):
    """Create user directly in database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        cursor.execute("""
            INSERT INTO "user" (
                id, username, email, password_hash, created_at,
                demographics_collected, notifications_enabled,
                morning_reminder_enabled, evening_reminder_enabled,
                sms_notifications_enabled, welcome_message_shown
            ) VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
        """, (user_id, username, email, password_hash, False, True, True, True, False, False))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"User created successfully: {username}")
        return True
    except Exception as e:
        print(f"User creation error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

@final_register_bp.route('/final-register', methods=['GET', 'POST'])
def final_register():
    """Final registration endpoint - completely isolated"""
    
    if request.method == 'GET':
        # Return simple HTML registration form
        html_content = """
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
            padding: 20px;
        }
        .container {
            background: white;
            padding: 2.5rem;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 420px;
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #333;
            margin: 0 0 0.5rem 0;
            font-size: 2.2rem;
        }
        .logo p {
            color: #666;
            margin: 0;
        }
        .form-group {
            margin-bottom: 1.2rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 600;
        }
        input[type="text"], input[type="email"], input[type="password"] {
            width: 100%;
            padding: 0.8rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 0.8rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-1px);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .message {
            margin-bottom: 1rem;
            padding: 0.7rem;
            border-radius: 6px;
            border-left: 4px solid;
        }
        .error {
            color: #e74c3c;
            background: #fdf2f2;
            border-left-color: #e74c3c;
        }
        .success {
            color: #27ae60;
            background: #f0f9f0;
            border-left-color: #27ae60;
        }
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
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
            <p>Your wellness companion</p>
        </div>
        
        <div id="message"></div>
        
        <form id="registerForm">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required 
                       minlength="3" maxlength="20">
            </div>
            
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required minlength="6">
            </div>
            
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="confirm_password" required minlength="6">
            </div>
            
            <button type="submit" class="btn" id="submitBtn">Create Account</button>
        </form>
        
        <div class="links">
            <a href="/stable-login">Already have an account? Sign in</a>
        </div>
    </div>

    <script>
        document.getElementById('registerForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const form = e.target;
            const formData = new FormData(form);
            const submitBtn = document.getElementById('submitBtn');
            const messageDiv = document.getElementById('message');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating Account...';
            
            fetch('/final-register', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                messageDiv.innerHTML = '';
                
                if (data.success) {
                    messageDiv.innerHTML = '<div class="message success">' + data.message + '</div>';
                    form.reset();
                    setTimeout(() => {
                        window.location.href = '/stable-login';
                    }, 2000);
                } else {
                    messageDiv.innerHTML = '<div class="message error">' + data.message + '</div>';
                }
            })
            .catch(error => {
                messageDiv.innerHTML = '<div class="message error">Registration failed. Please try again.</div>';
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Account';
            });
        });
    </script>
</body>
</html>"""
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
    
    # Handle POST request
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            })
        
        if len(username) < 3:
            return jsonify({
                'success': False,
                'message': 'Username must be at least 3 characters'
            })
        
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address'
            })
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters'
            })
        
        if password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Passwords do not match'
            })
        
        # Check if user exists
        if user_exists(username, email):
            return jsonify({
                'success': False,
                'message': 'Username or email already exists'
            })
        
        # Create user
        if create_user(username, email, password):
            return jsonify({
                'success': True,
                'message': 'Account created successfully! Redirecting to login...'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Registration failed. Please try again.'
            })
    
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'message': 'Registration failed. Please try again.'
        })
"""
Simple register route with minimal dependencies to fix the JSON parsing issues.
"""
import logging
import os
import uuid
import psycopg2
from flask import render_template, url_for, flash, redirect, Blueprint, request, render_template_string
from flask_login import current_user
from werkzeug.security import generate_password_hash
import re

simple_register_bp = Blueprint('simple_register', __name__)
logger = logging.getLogger(__name__)

# Simple registration template without dependencies
SIMPLE_REGISTER_TEMPLATE = """
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
        .error {
            color: #e74c3c;
            margin-bottom: 1rem;
            padding: 0.7rem;
            background: #fdf2f2;
            border-radius: 6px;
            border-left: 4px solid #e74c3c;
        }
        .success {
            color: #27ae60;
            margin-bottom: 1rem;
            padding: 0.7rem;
            background: #f0f9f0;
            border-radius: 6px;
            border-left: 4px solid #27ae60;
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
                       value="{{ username or '' }}" minlength="3" maxlength="20">
            </div>
            
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required 
                       value="{{ email or '' }}">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required minlength="6">
            </div>
            
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="confirm_password" required minlength="6">
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
    """Get direct database connection"""
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
        logger.error(f"Database connection error: {e}")
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
        logger.error(f"Error checking user existence: {e}")
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
            ) VALUES (%s, %s, %s, %s, NOW(), FALSE, TRUE, TRUE, TRUE, FALSE, FALSE)
        """, (user_id, username, email, password_hash))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

@simple_register_bp.route('/register-simple', methods=['GET', 'POST'])
def simple_register():
    """Registration route that bypasses SQLAlchemy issues"""
    logger.debug("Simple register route accessed")
    
    if request.method == 'GET':
        return render_template_string(SIMPLE_REGISTER_TEMPLATE)
    
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
        return render_template_string(SIMPLE_REGISTER_TEMPLATE,
                                    error="All fields are required",
                                    **form_data)
    
    if len(username) < 3:
        return render_template_string(SIMPLE_REGISTER_TEMPLATE,
                                    error="Username must be at least 3 characters",
                                    **form_data)
    
    if not validate_email(email):
        return render_template_string(SIMPLE_REGISTER_TEMPLATE,
                                    error="Please enter a valid email address",
                                    **form_data)
    
    if len(password) < 6:
        return render_template_string(SIMPLE_REGISTER_TEMPLATE,
                                    error="Password must be at least 6 characters",
                                    **form_data)
    
    if password != confirm_password:
        return render_template_string(SIMPLE_REGISTER_TEMPLATE,
                                    error="Passwords do not match",
                                    **form_data)
    
    # Check if user exists
    if user_exists(username, email):
        return render_template_string(SIMPLE_REGISTER_TEMPLATE,
                                    error="Username or email already exists",
                                    **form_data)
    
    # Create user
    if create_user(username, email, password):
        return render_template_string(SIMPLE_REGISTER_TEMPLATE,
                                    success="Account created successfully! You can now sign in.")
    else:
        return render_template_string(SIMPLE_REGISTER_TEMPLATE,
                                    error="Registration failed. Please try again.",
                                    **form_data)
            username = form.username.data.strip()
            
            # Check for existing users
            existing_user_by_email = User.query.filter_by(email=email).first()
            if existing_user_by_email:
                flash('Email: That email is already registered. Please use a different one.', 'danger')
                logger.warning(f"Registration attempt with existing email: {email}")
                return render_template('register_simple.html', title='Register', form=form)
            
            existing_user_by_username = User.query.filter_by(username=username).first()
            if existing_user_by_username:
                flash('Username: That username is already taken. Please choose a different one.', 'danger')
                logger.warning(f"Registration attempt with existing username: {username}")
                return render_template('register_simple.html', title='Register', form=form)
            
            # Create new user with explicit error handling
            try:
                user = User()
                user.username = username
                user.email = email
                user.set_password(form.password.data)
                
                # Add to database with transaction
                db.session.add(user)
                db.session.flush()  # Get user ID but don't commit yet
                db.session.commit()
                
                logger.info(f"New user registered successfully: {email} (ID: {user.id})")
                flash('Your account has been created successfully! You can now log in.', 'success')
                return redirect('/stable-login')
                
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Database error during user creation: {str(db_error)}", exc_info=True)
                flash('There was an error creating your account. Please try again.', 'danger')
                return render_template('register_simple.html', title='Register', form=form)
                
        except Exception as e:
            logger.error(f"Critical error during registration: {str(e)}", exc_info=True)
            db.session.rollback()
            flash('An unexpected error occurred. Please try again later.', 'danger')
            return render_template('register_simple.html', title='Register', form=form)
    
    # For GET requests or validation failures, render the form
    return render_template('register_simple.html', title='Register', form=form)
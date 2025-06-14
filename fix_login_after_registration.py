#!/usr/bin/env python3
"""
Fix for the login-after-registration issue caused by session secret change.
This addresses the "unexpected error" that occurs after successful registration.
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, flash, session, jsonify, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Create Flask app with robust session handling
app = Flask(__name__)

# Configuration with session error handling
app.secret_key = os.environ.get("SESSION_SECRET", "dear-teddy-super-secret-key-2025-mental-wellness-app")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

# Initialize extensions
db = SQLAlchemy(app, model_class=Base)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Add session error handling to prevent crashes
@app.before_request
def handle_session_errors():
    """Handle corrupted sessions from session secret changes"""
    try:
        # Test session accessibility
        test_val = session.get('_test', None)
        # Try to set a test value
        session['_test'] = 'ok'
    except Exception as e:
        logger.warning(f"Session error detected, clearing session: {e}")
        try:
            session.clear()
        except:
            pass
        # Create new session
        session.permanent = True

# User model - exactly matching existing database
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile information  
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    profile_image_url = db.Column(db.String(256), nullable=True)
    
    # Settings
    notifications_enabled = db.Column(db.Boolean, default=True)
    demographics_collected = db.Column(db.Boolean, default=False)
    welcome_message_shown = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        """Set password with proper error handling"""
        try:
            self.password_hash = generate_password_hash(password)
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise
    
    def check_password(self, password):
        """Check password with proper error handling"""
        try:
            if not self.password_hash:
                return False
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            logger.error(f"Password check error: {e}")
            return False

@login_manager.user_loader
def load_user(user_id):
    """Load user with error handling"""
    try:
        return User.query.get(user_id)
    except Exception as e:
        logger.error(f"User loading error for ID {user_id}: {e}")
        return None

# Routes with comprehensive error handling
@app.route('/')
def index():
    """Home page with authentication check"""
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return render_template_string("""
        <html><body>
        <h1>Dear Teddy</h1>
        <p>Welcome to your mental wellness companion.</p>
        <a href="/login">Login</a> | <a href="/register">Register</a>
        </body></html>
        """)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Enhanced registration with better error handling"""
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Input validation
            if not all([username, email, password, confirm_password]):
                flash('All fields are required.', 'error')
            elif password != confirm_password:
                flash('Passwords do not match.', 'error')
            elif len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
            else:
                try:
                    # Check if user exists
                    existing_user = User.query.filter(
                        (User.email.ilike(email)) | (User.username == username)
                    ).first()
                    
                    if existing_user:
                        if existing_user.email and existing_user.email.lower() == email:
                            flash('An account with this email already exists.', 'error')
                        else:
                            flash('This username is already taken.', 'error')
                    else:
                        # Create new user with proper session handling
                        user = User()
                        user.username = username
                        user.email = email
                        user.set_password(password)
                        
                        db.session.add(user)
                        db.session.commit()
                        
                        # Clear any existing session data before login
                        session.clear()
                        session.permanent = True
                        
                        # Log user in
                        login_success = login_user(user, remember=True)
                        if login_success:
                            flash('Welcome to Dear Teddy! Your account has been created successfully.', 'success')
                            # Force session save
                            session.modified = True
                            return redirect(url_for('dashboard'))
                        else:
                            flash('Account created but login failed. Please try logging in manually.', 'warning')
                            return redirect(url_for('login'))
                        
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Registration error: {e}")
                    flash('Registration failed due to a server error. Please try again.', 'error')
        
        return render_template_string(REGISTRATION_TEMPLATE)
        
    except Exception as e:
        logger.error(f"Registration route error: {e}")
        return f"Registration system error: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
@app.route('/stable-login', methods=['GET', 'POST'])
def login():
    """Enhanced login with better session handling"""
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = request.form.get('remember') == 'on'
            
            if not email or not password:
                flash('Please enter both email and password.', 'error')
            else:
                try:
                    # Find user
                    user = User.query.filter(User.email.ilike(email)).first()
                    
                    if user and user.check_password(password):
                        # Clear session before login to prevent conflicts
                        session.clear()
                        session.permanent = True
                        
                        # Attempt login
                        login_success = login_user(user, remember=remember)
                        if login_success:
                            # Force session save
                            session.modified = True
                            
                            next_page = request.args.get('next')
                            if next_page and next_page.startswith('/'):
                                return redirect(next_page)
                            return redirect(url_for('dashboard'))
                        else:
                            flash('Login failed due to a session error. Please try again.', 'error')
                    else:
                        flash('Invalid email or password.', 'error')
                        
                except Exception as e:
                    logger.error(f"Login process error: {e}")
                    flash('Login failed due to a server error. Please try again.', 'error')
        
        return render_template_string(LOGIN_TEMPLATE)
        
    except Exception as e:
        logger.error(f"Login route error: {e}")
        return f"Login system error: {str(e)}", 500

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with session validation"""
    try:
        # Validate current user session
        if not current_user or not current_user.is_authenticated:
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('login'))
            
        return render_template_string(DASHBOARD_TEMPLATE, user=current_user)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Dashboard error occurred. Please try logging in again.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Enhanced logout"""
    try:
        logout_user()
        session.clear()
        flash('You have been logged out successfully.', 'info')
    except Exception as e:
        logger.error(f"Logout error: {e}")
    return redirect(url_for('login'))

@app.route('/health')
def health():
    """Health check with session status"""
    try:
        # Test database
        db.session.execute(db.text('SELECT 1'))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Test session
    try:
        session['health_test'] = 'ok'
        session_status = "healthy"
    except Exception as e:
        session_status = f"error: {str(e)}"
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "session": session_status,
        "timestamp": datetime.utcnow().isoformat()
    })

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    """Enhanced error handler"""
    db.session.rollback()
    logger.error(f"500 error: {str(error)}")
    return render_template_string("""
    <html><body>
    <h1>Server Error</h1>
    <p>An unexpected error occurred. Please try again.</p>
    <a href="/">Return Home</a>
    </body></html>
    """), 500

# Templates
REGISTRATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Register - Dear Teddy</title>
    <style>
        body { font-family: Arial; max-width: 400px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { width: 100%; background: #007bff; color: white; padding: 10px; border: none; border-radius: 4px; }
        .error { color: red; margin-bottom: 10px; }
        .success { color: green; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h2>Create Account</h2>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <form method="post">
        <div class="form-group">
            <label>Username:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email" required>
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" name="password" required>
        </div>
        <div class="form-group">
            <label>Confirm Password:</label>
            <input type="password" name="confirm_password" required>
        </div>
        <button type="submit">Create Account</button>
    </form>
    
    <p><a href="/login">Already have an account? Login here</a></p>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Dear Teddy</title>
    <style>
        body { font-family: Arial; max-width: 400px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { width: 100%; background: #007bff; color: white; padding: 10px; border: none; border-radius: 4px; }
        .error { color: red; margin-bottom: 10px; }
        .success { color: green; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h2>Login</h2>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <form method="post">
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email" required>
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" name="password" required>
        </div>
        <div class="form-group">
            <label><input type="checkbox" name="remember"> Remember me</label>
        </div>
        <button type="submit">Login</button>
    </form>
    
    <p><a href="/register">Don't have an account? Register here</a></p>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Dear Teddy</title>
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .logout-btn { background: #dc3545; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome back, {{ user.username }}!</h1>
        <a href="/logout" class="logout-btn">Logout</a>
    </div>
    
    <p>Your mental wellness dashboard is ready.</p>
    <p>Account created: {{ user.created_at.strftime('%B %d, %Y') }}</p>
    <p>Email: {{ user.email }}</p>
</body>
</html>
"""

# Initialize database
with app.app_context():
    try:
        db.create_all()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database init error: {e}")

# WSGI application
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
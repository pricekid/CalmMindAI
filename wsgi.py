#!/usr/bin/env python3
"""
Production WSGI entry point for Dear Teddy
Optimized for deployment platforms like Render, Heroku, etc.
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, session, jsonify, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
import uuid

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Create Flask app
app = Flask(__name__)

# Essential configuration
app.secret_key = os.environ.get("SESSION_SECRET", "dear-teddy-super-secret-key-2025-mental-wellness-app")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db = SQLAlchemy(app, model_class=Base)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
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
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Routes
@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return render_template_string("""
        <h1>Dear Teddy</h1>
        <p>Welcome to your mental wellness companion.</p>
        <a href="/login">Login</a> | <a href="/register">Register</a>
        """)

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation
            if not all([username, email, password, confirm_password]):
                flash('All fields are required.', 'error')
            elif password != confirm_password:
                flash('Passwords do not match.', 'error')
            elif len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
            else:
                # Check if user exists
                existing_user = User.query.filter(
                    (User.email.ilike(email)) | (User.username == username)
                ).first()
                
                if existing_user:
                    if existing_user.email and existing_user.email.lower() == email:
                        flash('Email already registered.', 'error')
                    else:
                        flash('Username already taken.', 'error')
                else:
                    # Create new user
                    user = User()
                    user.username = username
                    user.email = email
                    user.set_password(password)
                    
                    db.session.add(user)
                    db.session.commit()
                    
                    login_user(user)
                    flash('Registration successful!', 'success')
                    return redirect(url_for('dashboard'))
        
        # Simple registration form
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Register - Dear Teddy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="text"], input[type="email"], input[type="password"] { 
                    width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; 
                }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .error { color: red; margin-bottom: 10px; }
                .success { color: green; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <h2>Register for Dear Teddy</h2>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="post">
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
                
                <button type="submit">Register</button>
            </form>
            
            <p><a href="/login">Already have an account? Login here</a></p>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return f"Registration error: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
@app.route('/stable-login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = request.form.get('remember') == 'on'
            
            if not email or not password:
                flash('Email and password are required.', 'error')
            else:
                user = User.query.filter(User.email.ilike(email)).first()
                
                if user and user.check_password(password):
                    session.permanent = True
                    login_user(user, remember=remember)
                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/'):
                        return redirect(next_page)
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid email or password.', 'error')
        
        # Simple login form
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Dear Teddy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="email"], input[type="password"] { 
                    width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; 
                }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .error { color: red; margin-bottom: 10px; }
                .success { color: green; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <h2>Login to Dear Teddy</h2>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="post">
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="remember"> Remember me
                    </label>
                </div>
                
                <button type="submit">Login</button>
            </form>
            
            <p><a href="/register">Don't have an account? Register here</a></p>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return f"Login error: {str(e)}", 500

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Dear Teddy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
                .welcome { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .logout-btn { background: #dc3545; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }
                .logout-btn:hover { background: #c82333; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Dear Teddy Dashboard</h1>
                <a href="/logout" class="logout-btn">Logout</a>
            </div>
            
            <div class="welcome">
                <h2>Welcome back, {{ user.username }}!</h2>
                <p>Your mental wellness companion is here to help.</p>
            </div>
            
            <div>
                <h3>Quick Stats</h3>
                <p>Account created: {{ user.created_at.strftime('%B %d, %Y') }}</p>
                <p>Email: {{ user.email }}</p>
            </div>
        </body>
        </html>
        """, user=current_user)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"Dashboard error: {str(e)}", 500

@app.route('/health')
def health():
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "session_configured": bool(app.secret_key),
        "timestamp": datetime.utcnow().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template_string("""
    <h1>Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <a href="/">Go Home</a>
    """), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal error: {str(error)}")
    return render_template_string("""
    <h1>Internal Server Error</h1>
    <p>Something went wrong. Please try again later.</p>
    <a href="/">Go Home</a>
    """), 500

# Initialize database
try:
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")

# This is the WSGI callable that deployment platforms will use
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

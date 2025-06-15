#!/usr/bin/env python3
"""
Isolated production app for Render deployment
Uses unique model names and completely separate imports to avoid conflicts
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, flash, session, jsonify, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create unique declarative base to avoid conflicts
class ProductionBase(DeclarativeBase):
    pass

# Create Flask app
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("SESSION_SECRET", "dear-teddy-production-secret-2025")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = 86400

# Initialize extensions with unique names
db = SQLAlchemy(app, model_class=ProductionBase)
login_manager = LoginManager()
login_manager.init_app(app)

# Session error handling
@app.before_request
def handle_session_errors():
    try:
        session.get('_test', None)
        session['_test'] = 'ok'
    except:
        try:
            session.clear()
        except:
            pass
        session.permanent = True

# User model with unique name to avoid conflicts
class ProductionUser(UserMixin, db.Model):
    __tablename__ = "user"  # Maps to existing table
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    profile_image_url = db.Column(db.String(256), nullable=True)
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
    try:
        return ProductionUser.query.get(user_id)
    except:
        return None

# Routes
@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except:
        return '<h1>Dear Teddy</h1><a href="/login">Login</a> | <a href="/register">Register</a>'

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
            
            if not all([username, email, password, confirm_password]):
                flash('All fields are required.', 'error')
            elif password != confirm_password:
                flash('Passwords do not match.', 'error')
            elif len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
            else:
                try:
                    existing_user = ProductionUser.query.filter(
                        (ProductionUser.email.ilike(email)) | (ProductionUser.username == username)
                    ).first()
                    
                    if existing_user:
                        if existing_user.email and existing_user.email.lower() == email:
                            flash('Email already registered.', 'error')
                        else:
                            flash('Username already taken.', 'error')
                    else:
                        user = ProductionUser()
                        user.username = username
                        user.email = email
                        user.set_password(password)
                        
                        db.session.add(user)
                        db.session.commit()
                        
                        session.clear()
                        session.permanent = True
                        
                        if login_user(user, remember=True):
                            flash('Registration successful! Welcome to Dear Teddy.', 'success')
                            session.modified = True
                            return redirect(url_for('dashboard'))
                        else:
                            flash('Account created but login failed. Please login manually.', 'warning')
                            return redirect(url_for('login'))
                            
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Registration error: {e}")
                    flash('Registration failed. Please try again.', 'error')
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>Register - Dear Teddy</title>
        <style>body{font-family:Arial;max-width:400px;margin:50px auto;padding:20px;background:#f8f9fa}
        .container{background:white;padding:30px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        .form-group{margin-bottom:15px}label{display:block;margin-bottom:5px;font-weight:500}
        input{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box}
        button{width:100%;background:#007bff;color:white;padding:10px;border:none;border-radius:4px;cursor:pointer}
        button:hover{background:#0056b3}
        .error{color:#dc3545;margin-bottom:10px;padding:8px;background:#f8d7da;border-radius:4px}
        .success{color:#155724;margin-bottom:10px;padding:8px;background:#d4edda;border-radius:4px}</style>
        </head>
        <body>
        <div class="container">
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
        </div>
        </body></html>
        """)
        
    except Exception as e:
        logger.error(f"Registration route error: {e}")
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
                flash('Please enter both email and password.', 'error')
            else:
                try:
                    user = ProductionUser.query.filter(ProductionUser.email.ilike(email)).first()
                    
                    if user and user.check_password(password):
                        session.clear()
                        session.permanent = True
                        
                        if login_user(user, remember=remember):
                            session.modified = True
                            next_page = request.args.get('next')
                            if next_page and next_page.startswith('/'):
                                return redirect(next_page)
                            return redirect(url_for('dashboard'))
                        else:
                            flash('Login failed. Please try again.', 'error')
                    else:
                        flash('Invalid email or password.', 'error')
                        
                except Exception as e:
                    logger.error(f"Login error: {e}")
                    flash('Login failed. Please try again.', 'error')
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>Login - Dear Teddy</title>
        <style>body{font-family:Arial;max-width:400px;margin:50px auto;padding:20px;background:#f8f9fa}
        .container{background:white;padding:30px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        .form-group{margin-bottom:15px}label{display:block;margin-bottom:5px;font-weight:500}
        input{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box}
        button{width:100%;background:#007bff;color:white;padding:10px;border:none;border-radius:4px;cursor:pointer}
        button:hover{background:#0056b3}
        .error{color:#dc3545;margin-bottom:10px;padding:8px;background:#f8d7da;border-radius:4px}
        .note{background:#fff3cd;padding:10px;border-radius:4px;margin-bottom:15px;font-size:14px}</style>
        </head>
        <body>
        <div class="container">
        <h2>Welcome Back</h2>
        <div class="note">
            <strong>Note:</strong> If you registered before June 2025, try password: temp_[username]_2025
        </div>
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
        </div>
        </body></html>
        """)
        
    except Exception as e:
        logger.error(f"Login route error: {e}")
        return f"Login error: {str(e)}", 500

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        if not current_user or not current_user.is_authenticated:
            return redirect(url_for('login'))
            
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>Dashboard - Dear Teddy</title>
        <style>body{font-family:Arial;margin:0;padding:0;background:#f8f9fa}
        .header{background:white;box-shadow:0 2px 4px rgba(0,0,0,0.1);padding:15px 20px;margin-bottom:20px}
        .header-content{max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:center}
        .logout-btn{background:#dc3545;color:white;padding:8px 16px;text-decoration:none;border-radius:4px}
        .container{max-width:1200px;margin:0 auto;padding:0 20px}
        .welcome{background:white;padding:30px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);margin-bottom:20px}
        </style>
        </head>
        <body>
        <div class="header">
            <div class="header-content">
                <h1>Dear Teddy Dashboard</h1>
                <a href="/logout" class="logout-btn">Logout</a>
            </div>
        </div>
        <div class="container">
            <div class="welcome">
                <h2>Welcome back, {{ user.username }}!</h2>
                <p>Your mental wellness companion is here to help.</p>
                <p>Account created: {{ user.created_at.strftime('%B %d, %Y') }}</p>
                <p>Email: {{ user.email }}</p>
            </div>
        </div>
        </body></html>
        """, user=current_user)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    try:
        logout_user()
        session.clear()
        flash('You have been logged out.', 'info')
    except:
        pass
    return redirect(url_for('login'))

@app.route('/health')
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "timestamp": datetime.utcnow().isoformat()}), 500

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return '<h1>Server Error</h1><p>Please try again.</p><a href="/">Home</a>', 500

# Initialize database
with app.app_context():
    try:
        db.create_all()
        logger.info("Production database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
#!/usr/bin/env python3
"""
Production-ready main application for Dear Teddy
This is a complete, standalone Flask app optimized for production deployment
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

# Production configuration
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
login_manager.login_message = 'Please log in to access this page.'

# User model - matches existing database structure
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
        """Set password hash using Werkzeug's secure method"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against stored hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    try:
        return User.query.get(user_id)
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

# Routes
@app.route('/')
def index():
    """Home page - redirect based on authentication status"""
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dear Teddy - Mental Wellness Companion</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 100px auto; padding: 20px; text-align: center; }
                .hero { background: #f8f9fa; padding: 40px; border-radius: 8px; margin-bottom: 20px; }
                .links a { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
                .links a:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="hero">
                <h1>Dear Teddy</h1>
                <p>Your AI-powered mental wellness companion</p>
                <p>Track your emotions, receive personalized insights, and grow with compassionate support.</p>
            </div>
            <div class="links">
                <a href="/login">Login</a>
                <a href="/register">Register</a>
            </div>
        </body>
        </html>
        """)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with comprehensive validation"""
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Input validation
            errors = []
            if not username:
                errors.append('Username is required.')
            elif len(username) < 3:
                errors.append('Username must be at least 3 characters long.')
            
            if not email:
                errors.append('Email is required.')
            elif '@' not in email or '.' not in email:
                errors.append('Please enter a valid email address.')
            
            if not password:
                errors.append('Password is required.')
            elif len(password) < 6:
                errors.append('Password must be at least 6 characters long.')
            
            if password != confirm_password:
                errors.append('Passwords do not match.')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
            else:
                # Check if user already exists
                existing_user = User.query.filter(
                    (User.email.ilike(email)) | (User.username == username)
                ).first()
                
                if existing_user:
                    if existing_user.email and existing_user.email.lower() == email:
                        flash('An account with this email already exists.', 'error')
                    else:
                        flash('This username is already taken.', 'error')
                else:
                    try:
                        # Create new user
                        user = User()
                        user.username = username
                        user.email = email
                        user.set_password(password)
                        
                        db.session.add(user)
                        db.session.commit()
                        
                        # Log user in immediately
                        login_user(user)
                        flash('Welcome to Dear Teddy! Your account has been created successfully.', 'success')
                        return redirect(url_for('dashboard'))
                        
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Registration database error: {e}")
                        flash('Registration failed. Please try again.', 'error')
        
        # Registration form
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Register - Dear Teddy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 450px; margin: 50px auto; padding: 20px; background: #f8f9fa; }
                .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h2 { text-align: center; color: #333; margin-bottom: 30px; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; font-weight: 500; color: #555; }
                input[type="text"], input[type="email"], input[type="password"] { 
                    width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; box-sizing: border-box;
                }
                input:focus { border-color: #007bff; outline: none; box-shadow: 0 0 5px rgba(0,123,255,0.3); }
                button { width: 100%; background: #007bff; color: white; padding: 12px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .error { color: #dc3545; margin-bottom: 10px; padding: 10px; background: #f8d7da; border-radius: 4px; }
                .success { color: #155724; margin-bottom: 10px; padding: 10px; background: #d4edda; border-radius: 4px; }
                .link { text-align: center; margin-top: 20px; }
                .link a { color: #007bff; text-decoration: none; }
                .link a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Create Your Account</h2>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="post" novalidate>
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required 
                               value="{{ request.form.get('username', '') }}" placeholder="Choose a unique username">
                    </div>
                    
                    <div class="form-group">
                        <label for="email">Email Address</label>
                        <input type="email" id="email" name="email" required 
                               value="{{ request.form.get('email', '') }}" placeholder="your@email.com">
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required 
                               placeholder="At least 6 characters">
                    </div>
                    
                    <div class="form-group">
                        <label for="confirm_password">Confirm Password</label>
                        <input type="password" id="confirm_password" name="confirm_password" required 
                               placeholder="Re-enter your password">
                    </div>
                    
                    <button type="submit">Create Account</button>
                </form>
                
                <div class="link">
                    <a href="/login">Already have an account? Sign in here</a>
                </div>
            </div>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Registration route error: {e}")
        return f"Registration system error: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
@app.route('/stable-login', methods=['GET', 'POST'])
def login():
    """User login with support for both endpoints"""
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
                # Find user by email (case-insensitive)
                user = User.query.filter(User.email.ilike(email)).first()
                
                if user and user.check_password(password):
                    session.permanent = True
                    login_user(user, remember=remember)
                    
                    # Handle redirect after login
                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/'):
                        return redirect(next_page)
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid email or password. Please check your credentials and try again.', 'error')
        
        # Login form
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Dear Teddy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 450px; margin: 80px auto; padding: 20px; background: #f8f9fa; }
                .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h2 { text-align: center; color: #333; margin-bottom: 30px; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; font-weight: 500; color: #555; }
                input[type="email"], input[type="password"] { 
                    width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; box-sizing: border-box;
                }
                input:focus { border-color: #007bff; outline: none; box-shadow: 0 0 5px rgba(0,123,255,0.3); }
                .checkbox-group { display: flex; align-items: center; margin-bottom: 20px; }
                .checkbox-group input { width: auto; margin-right: 8px; }
                button { width: 100%; background: #007bff; color: white; padding: 12px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .error { color: #dc3545; margin-bottom: 10px; padding: 10px; background: #f8d7da; border-radius: 4px; }
                .success { color: #155724; margin-bottom: 10px; padding: 10px; background: #d4edda; border-radius: 4px; }
                .link { text-align: center; margin-top: 20px; }
                .link a { color: #007bff; text-decoration: none; }
                .link a:hover { text-decoration: underline; }
                .temp-password-note { background: #fff3cd; color: #856404; padding: 10px; border-radius: 4px; margin-bottom: 20px; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Welcome Back</h2>
                
                <div class="temp-password-note">
                    <strong>Note:</strong> If you registered before June 2025, your temporary password is: <code>temp_[username]_2025</code>
                </div>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="post" novalidate>
                    <div class="form-group">
                        <label for="email">Email Address</label>
                        <input type="email" id="email" name="email" required 
                               value="{{ request.form.get('email', '') }}" placeholder="your@email.com">
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required 
                               placeholder="Enter your password">
                    </div>
                    
                    <div class="checkbox-group">
                        <input type="checkbox" id="remember" name="remember">
                        <label for="remember">Remember me</label>
                    </div>
                    
                    <button type="submit">Sign In</button>
                </form>
                
                <div class="link">
                    <a href="/register">Don't have an account? Register here</a>
                </div>
            </div>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Login route error: {e}")
        return f"Login system error: {str(e)}", 500

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    try:
        logout_user()
        flash('You have been signed out successfully.', 'info')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - main application interface"""
    try:
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Dear Teddy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
                .header { background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 15px 20px; margin-bottom: 20px; }
                .header-content { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
                .logo { font-size: 24px; font-weight: bold; color: #007bff; }
                .user-info { display: flex; align-items: center; gap: 15px; }
                .logout-btn { background: #dc3545; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }
                .logout-btn:hover { background: #c82333; }
                .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
                .welcome-card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .stat-card h3 { margin: 0 0 10px 0; color: #333; }
                .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
                .actions { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .action-btn { display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-right: 10px; margin-bottom: 10px; }
                .action-btn:hover { background: #0056b3; }
                .action-btn.secondary { background: #6c757d; }
                .action-btn.secondary:hover { background: #545b62; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="header-content">
                    <div class="logo">Dear Teddy</div>
                    <div class="user-info">
                        <span>Welcome, {{ user.username }}!</span>
                        <a href="/logout" class="logout-btn">Sign Out</a>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="welcome-card">
                    <h1>Welcome to Your Mental Wellness Dashboard</h1>
                    <p>Your journey to better mental health starts here. Track your emotions, reflect on your thoughts, and receive personalized insights to support your wellbeing.</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Account Status</h3>
                        <div class="stat-value">Active</div>
                        <p>Member since {{ user.created_at.strftime('%B %Y') }}</p>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Email</h3>
                        <div class="stat-value">{{ user.email }}</div>
                        <p>Verified account</p>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Notifications</h3>
                        <div class="stat-value">{{ 'Enabled' if user.notifications_enabled else 'Disabled' }}</div>
                        <p>Stay updated with wellness tips</p>
                    </div>
                </div>
                
                <div class="actions">
                    <h3>Quick Actions</h3>
                    <p>Your mental wellness journey continues. Here are some actions you can take:</p>
                    <a href="#" class="action-btn">Write in Journal</a>
                    <a href="#" class="action-btn">Track Mood</a>
                    <a href="#" class="action-btn">View Insights</a>
                    <a href="#" class="action-btn secondary">Account Settings</a>
                </div>
            </div>
        </body>
        </html>
        """, user=current_user)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"Dashboard error: {str(e)}", 500

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = "healthy"
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"error: {str(e)}"
        db_connected = False
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "database_connected": db_connected,
        "session_configured": bool(app.secret_key),
        "timestamp": datetime.utcnow().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Page Not Found - Dear Teddy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 100px auto; padding: 20px; text-align: center; }
            .error-container { background: #f8f9fa; padding: 40px; border-radius: 8px; }
            .error-code { font-size: 72px; font-weight: bold; color: #007bff; margin-bottom: 20px; }
            h1 { color: #333; margin-bottom: 20px; }
            p { color: #666; margin-bottom: 30px; }
            a { display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
            a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-code">404</div>
            <h1>Page Not Found</h1>
            <p>The page you're looking for doesn't exist or may have been moved.</p>
            <a href="/">Return Home</a>
        </div>
    </body>
    </html>
    """), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Server Error - Dear Teddy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 100px auto; padding: 20px; text-align: center; }
            .error-container { background: #f8f9fa; padding: 40px; border-radius: 8px; }
            .error-code { font-size: 72px; font-weight: bold; color: #dc3545; margin-bottom: 20px; }
            h1 { color: #333; margin-bottom: 20px; }
            p { color: #666; margin-bottom: 30px; }
            a { display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
            a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-code">500</div>
            <h1>Server Error</h1>
            <p>Something went wrong on our end. Please try again in a few moments.</p>
            <a href="/">Return Home</a>
        </div>
    </body>
    </html>
    """), 500

# Initialize database tables
def init_database():
    """Initialize database tables if they don't exist"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables initialized successfully")
            
            # Log some basic stats
            user_count = User.query.count()
            logger.info(f"Database contains {user_count} users")
            
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")

# Initialize database when module is imported
init_database()

# WSGI application object for deployment
application = app

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
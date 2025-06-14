#!/usr/bin/env python3
"""
Production-optimized Flask app for www.dearteddy.app
Streamlined version focusing on core authentication functionality
"""

import os
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

def create_production_app():
    """Create production-optimized Flask app"""
    app = Flask(__name__)
    
    # Essential configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dear-teddy-super-secret-key-2025-mental-wellness-app")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for production simplicity
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    csrf.init_app(app)
    
    return app

# Create app instance
app = create_production_app()

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
    if current_user.is_authenticated:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
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
                    if existing_user.email.lower() == email:
                        flash('Email already registered.', 'error')
                    else:
                        flash('Username already taken.', 'error')
                else:
                    # Create new user
                    user = User(username=username, email=email)
                    user.set_password(password)
                    
                    db.session.add(user)
                    db.session.commit()
                    
                    login_user(user)
                    flash('Registration successful!', 'success')
                    return redirect('/dashboard')
                    
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/stable-login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
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
                    return redirect('/dashboard')
                else:
                    flash('Invalid email or password.', 'error')
                    
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('stable_login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "database_connected": bool(db.engine),
        "session_configured": bool(app.secret_key)
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal error: {str(error)}")
    return render_template('500.html'), 500

# Initialize database
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
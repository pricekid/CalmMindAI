"""
Production-compatible routes for Render deployment.
This module provides essential routes without complex dependencies.
"""

from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
import logging

logger = logging.getLogger(__name__)

def register_production_routes(app):
    """Register essential routes for production deployment."""
    
    @app.route('/')
    def index():
        """Home route - dashboard for logged in users, landing for anonymous."""
        if current_user.is_authenticated:
            try:
                # Simple dashboard without complex dependencies
                return render_template('dashboard.html', 
                                     user=current_user,
                                     badge_data={'current_streak': 0, 'xp_data': {'level': 1, 'level_name': 'Beginner'}})
            except Exception as e:
                logger.error(f"Dashboard error: {e}")
                return render_template('simple_dashboard.html', user=current_user)
        else:
            return render_template('login.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login route."""
        if request.method == 'POST':
            try:
                from models import User
                
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                
                if not email or not password:
                    flash('Please enter both email and password.', 'error')
                    return render_template('login.html')
                
                user = User.query.filter_by(email=email).first()
                
                if user and check_password_hash(user.password_hash, password):
                    login_user(user, remember=True)
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
                else:
                    flash('Invalid email or password.', 'error')
                    
            except Exception as e:
                logger.error(f"Login error: {e}")
                flash('Login system temporarily unavailable.', 'error')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration route."""
        if request.method == 'POST':
            try:
                from models import User
                
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                
                if not email or not password:
                    flash('Please enter both email and password.', 'error')
                    return render_template('register.html')
                
                # Check if user already exists
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already registered. Please login instead.', 'error')
                    return redirect(url_for('login'))
                
                # Create new user
                user = User(email=email, password_hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
                
                login_user(user, remember=True)
                flash('Registration successful! Welcome to Dear Teddy.', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                logger.error(f"Registration error: {e}")
                flash('Registration system temporarily unavailable.', 'error')
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """User logout route."""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for production monitoring."""
        return jsonify({
            'status': 'healthy',
            'database': 'connected' if db.engine else 'disconnected'
        })
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors."""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {e}")
        return render_template('500.html'), 500

    logger.info("Production routes registered successfully")
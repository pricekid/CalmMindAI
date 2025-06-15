"""
Production-specific login fix for Render deployment.
This creates a minimal, working login system that bypasses SQLAlchemy registration issues.
"""

import os
import logging
from flask import Blueprint, render_template, redirect, request, flash, session, jsonify
from flask_login import login_user, current_user, logout_user
from werkzeug.security import check_password_hash
from extensions import db
from models import User
from flask_wtf.csrf import generate_csrf

production_login_bp = Blueprint('production_login', __name__)
logger = logging.getLogger(__name__)

@production_login_bp.route('/production-login', methods=['GET', 'POST'])
def production_login():
    """Production-optimized login route"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Please enter both email and password.', 'error')
                return render_template('production_login.html', csrf_token=generate_csrf())
            
            # Use SQLAlchemy ORM query instead of raw SQL
            user = User.query.filter(User.email.ilike(email)).first()
            
            if user:
                # Verify password
                if user.password_hash and check_password_hash(user.password_hash, password):
                    # Log in the user
                    login_user(user, remember=True)
                    logger.info(f"Production login successful for user: {email}")
                    
                    # Redirect to dashboard
                    return redirect('/dashboard')
                else:
                    logger.warning(f"Invalid password for user: {email}")
                    flash('Invalid email or password.', 'error')
            else:
                logger.warning(f"User not found: {email}")
                flash('Invalid email or password.', 'error')
                    
        except Exception as e:
            logger.error(f"Production login error: {str(e)}")
            flash('Login system temporarily unavailable. Please try again.', 'error')
    
    return render_template('production_login.html', csrf_token=generate_csrf())

@production_login_bp.route('/production-logout')
def production_logout():
    """Production logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect('/')

@production_login_bp.route('/production-test')
def production_test():
    """Test production database connectivity"""
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users")).fetchone()
            user_count = result[0] if result else 0
            
        return jsonify({
            'status': 'success',
            'message': f'Database connection successful. {user_count} users found.',
            'database_url': os.environ.get('DATABASE_URL', 'Not set')[:50] + '...'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
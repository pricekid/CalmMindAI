"""
Emergency production fix to resolve SQLAlchemy registration issues.
This creates a completely isolated login system that bypasses all potential conflicts.
"""

import os
import logging
from flask import Blueprint, render_template, redirect, request, flash, session, jsonify
from flask_login import login_user, current_user, logout_user
from werkzeug.security import check_password_hash
import psycopg2
from urllib.parse import urlparse

emergency_bp = Blueprint('emergency', __name__)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get direct database connection bypassing SQLAlchemy"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL not found")
    
    # Parse the database URL
    parsed = urlparse(database_url)
    
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:]  # Remove leading slash
    )

class SimpleUser:
    """Simple user class for Flask-Login compatibility"""
    def __init__(self, user_id, email, first_name=None):
        self.id = user_id
        self.email = email
        self.first_name = first_name
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

@emergency_bp.route('/emergency-production-login', methods=['GET', 'POST'])
def emergency_production_login():
    """Emergency production login with direct database access"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Please enter both email and password.', 'error')
                return render_template('emergency_login.html')
            
            # Direct database connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Query user directly
            cursor.execute(
                "SELECT id, email, password_hash, first_name FROM users WHERE LOWER(email) = %s",
                (email,)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                user_id, user_email, password_hash, first_name = user_data
                
                # Verify password
                if password_hash and check_password_hash(password_hash, password):
                    # Create simple user object
                    user = SimpleUser(user_id, user_email, first_name)
                    
                    # Log in the user
                    login_user(user, remember=True)
                    logger.info(f"Emergency login successful for user: {email}")
                    
                    cursor.close()
                    conn.close()
                    
                    return redirect('/dashboard')
                else:
                    logger.warning(f"Invalid password for user: {email}")
                    flash('Invalid email or password.', 'error')
            else:
                logger.warning(f"User not found: {email}")
                flash('Invalid email or password.', 'error')
            
            cursor.close()
            conn.close()
                    
        except Exception as e:
            logger.error(f"Emergency login error: {str(e)}")
            flash('Login system temporarily unavailable. Please try again.', 'error')
    
    return render_template('emergency_login.html')

@emergency_bp.route('/emergency-test-db')
def emergency_test_db():
    """Test direct database connectivity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT email FROM users LIMIT 3")
        sample_users = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Direct database connection successful. {user_count} users found.',
            'sample_users': sample_users,
            'database_host': urlparse(os.environ.get('DATABASE_URL')).hostname
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500

@emergency_bp.route('/emergency-logout')
def emergency_logout():
    """Emergency logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect('/')
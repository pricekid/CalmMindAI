"""
Standalone emergency login system that bypasses CSRF protection.
This is a TEMPORARY solution to regain access when the main login system is broken.
"""
import os
import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, redirect, flash, render_template, session, url_for
from flask_login import login_user, current_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import models
from models import User
try:
    from admin_models import Admin
except ImportError:
    logger.warning("Admin model not available, admin login functionality will be limited")
    Admin = None

# Create blueprint - will be registered in main.py
emergency_bp = Blueprint('emergency_direct', __name__)

@emergency_bp.route('/emergency-login', methods=['GET', 'POST'])
def emergency_login():
    """
    Provides a bare-bones login form with no CSRF protection or JSON parsing.
    FOR EMERGENCY USE ONLY when regular login is broken.
    """
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect('/dashboard')

    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            error = 'Email is required.'
        else:
            try:
                with db.session.begin():
                    # Use SQLAlchemy model query
                    user = User.query.filter_by(email=email).first()
                    
                    if user:
                        # Generate a UUID for user if needed
                        if not user.id:
                            user.id = str(uuid.uuid4())
                            db.session.commit()
                            
                        login_user(user)
                        flash(f'Emergency login successful. Welcome {user.email}!', 'success')
                        
                        # Make session permanent to avoid session timeout issues
                        session.permanent = True
                        
                        return redirect('/dashboard')
                    else:
                        # User not found, create a new one
                        new_user = User()
                        new_user.id = str(uuid.uuid4())
                        new_user.email = email
                        new_user.created_at = datetime.utcnow()
                        
                        db.session.add(new_user)
                        db.session.commit()
                        
                        login_user(new_user)
                        flash(f'Created new account and logged in as {email}', 'success')
                        
                        # Make session permanent
                        session.permanent = True
                        
                        return redirect('/dashboard')
            except Exception as e:
                logger.error(f"Error during emergency login: {str(e)}")
                error = f"Database error: {str(e)}"

    return render_template('emergency_login.html', error=error)

@emergency_bp.route('/emergency-admin', methods=['GET', 'POST'])
def emergency_admin():
    """
    Emergency admin login that bypasses normal authentication.
    """
    error = None
    
    # Check if Admin model is available
    if Admin is None:
        error = "Admin functionality is not available in this deployment."
        return render_template('emergency_admin.html', error=error)
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        create_admin = request.form.get('create_admin') == 'yes'
        
        if not username:
            error = 'Username is required.'
        else:
            try:
                with db.session.begin():
                    # Use SQLAlchemy model query
                    admin = Admin.query.filter_by(username=username).first()
                    
                    if admin and not create_admin:
                        # Verify password if we're not creating a new admin
                        if admin.check_password(password):
                            session['is_admin'] = True
                            session['admin_id'] = admin.id
                            session.permanent = True
                            
                            flash(f'Admin login successful. Welcome {admin.username}!', 'success')
                            return redirect('/admin')
                        else:
                            error = 'Invalid password.'
                    elif create_admin:
                        # Create a new admin if requested
                        if not password or len(password) < 8:
                            error = 'Please provide a password with at least 8 characters.'
                        else:
                            # Create new admin
                            new_admin = Admin(username=username)
                            new_admin.set_password(password)
                            db.session.add(new_admin)
                            db.session.commit()
                            
                            session['is_admin'] = True
                            session['admin_id'] = new_admin.id
                            session.permanent = True
                            
                            flash(f'Created new admin account and logged in as {username}', 'success')
                            return redirect('/admin')
                    else:
                        error = 'Admin account not found.'
            except Exception as e:
                logger.error(f"Error during emergency admin login: {str(e)}")
                error = f"Database error: {str(e)}"

    return render_template('emergency_admin.html', error=error)

@emergency_bp.route('/emergency-logout')
def emergency_logout():
    """
    Emergency logout that clears the session.
    """
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/emergency-login')

@emergency_bp.route('/clear-session')
def clear_session():
    """
    Clear the session data for debugging.
    """
    old_session = dict(session)
    session.clear()
    return render_template('debug_session.html', 
                          title='Session Cleared',
                          old_session=old_session,
                          current_session=dict(session))

@emergency_bp.route('/session-status')
def session_status():
    """
    Show current session status for debugging.
    """
    return render_template('debug_session.html',
                          title='Session Status',
                          current_session=dict(session),
                          current_user=current_user)
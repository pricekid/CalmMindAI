"""
Emergency admin access script.
This is a standalone script to provide emergency admin access 
without relying on the main application's authentication system.
"""

from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import login_user, current_user
from admin_models import Admin
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("emergency_admin")

# Create blueprint
emergency_admin_bp = Blueprint('emergency_admin', __name__, url_prefix='/emergency')

@emergency_admin_bp.route('/admin-login')
def direct_admin_login():
    """
    Emergency direct admin login that completely bypasses password checks.
    Only use this for system recovery when normal login is broken.
    """
    # Log the attempt
    logger.info("Emergency admin login attempt")
    
    # Check if already logged in as admin
    if current_user.is_authenticated and hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
        logger.info("User already logged in as admin")
        flash("You are already logged in as admin.", "info")
        return redirect('/admin/dashboard')
    
    # Get admin from database or create default admin
    try:
        # Try to get the admin user from the database
        admin = Admin.get("1")
        if not admin:
            logger.error("Failed to get or create admin user")
            flash("Failed to find or create admin user.", "danger")
            return redirect('/')
            
        logger.info(f"Got admin object: {admin}")
        
        # Set session permanent to True
        from flask import session
        session.permanent = True
        
        # Log in the admin user
        login_user(admin)
        
        # Add custom session variables for extra verification
        session['is_admin'] = True
        session['admin_username'] = admin.username
        
        logger.info("Emergency admin login successful")
        flash("You've been logged in as admin via the emergency login method.", "success")
        return redirect('/admin/dashboard')
    except Exception as e:
        logger.error(f"Emergency admin login failed: {str(e)}")
        flash(f"Emergency admin login failed: {str(e)}", "danger")
        return redirect('/')

@emergency_admin_bp.route('/status')
def status():
    """
    Status page showing current login state and debug info.
    """
    debug_info = {
        "is_authenticated": current_user.is_authenticated,
        "user_id": current_user.get_id() if current_user.is_authenticated else None,
        "is_admin": current_user.get_id().startswith('admin_') if current_user.is_authenticated and hasattr(current_user, 'get_id') else False
    }
    
    return render_template('admin/emergency_status.html', debug_info=debug_info)
    
@emergency_admin_bp.route('/dashboard')
def emergency_dashboard():
    """
    Emergency admin dashboard with minimal functionality.
    """
    # Check if user is logged in as admin
    if not current_user.is_authenticated or not hasattr(current_user, 'get_id') or not current_user.get_id().startswith('admin_'):
        logger.warning("Unauthorized access attempt to emergency dashboard")
        flash("You need to be logged in as admin to access this page.", "danger")
        return redirect('/emergency/admin-login')
        
    # Get some basic stats if possible
    stats = {
        "admin_id": current_user.id,
        "admin_username": current_user.username,
        "login_time": "Current Session"
    }
    
    return render_template('admin/emergency_dashboard.html', stats=stats)
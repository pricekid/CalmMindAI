from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from replit_auth import make_replit_blueprint, require_login

# Create the blueprint
replit_bp = make_replit_blueprint()

@replit_bp.route('/protected')
@require_login
def protected():
    """Example protected route using Replit Auth"""
    return render_template('protected.html',
                         title='Protected Page',
                         user=current_user)

@replit_bp.route('/profile')
@require_login
def profile():
    """Profile page showing user information from Replit Auth"""
    return render_template('profile.html',
                         title='Your Profile',
                         user=current_user)
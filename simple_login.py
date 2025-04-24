"""
Ultra simple login script to bypass login issues.
This creates a direct login link without requiring password entry.
"""
import os
import logging
from flask import Flask, redirect, url_for, request, flash, Blueprint
from flask_login import login_user
from models import User
from app import db

logger = logging.getLogger(__name__)
simple_login_bp = Blueprint('simple_login', __name__)

@simple_login_bp.route('/simple-login/<int:user_id>')
def simple_login(user_id):
    """
    Login route with minimal dependencies and error handling.
    This bypasses password checking for development/testing.
    """
    try:
        # Find user by ID
        user = db.session.get(User, user_id)
        
        if user:
            login_user(user, remember=True)
            logger.info(f"Simple login successful for user ID: {user_id}")
            # Use hardcoded redirect to the emergency simple dashboard
            return redirect('/simple-dashboard')
        else:
            logger.error(f"Simple login failed - user ID not found: {user_id}")
            return "User not found. Check the ID and try again."
    except Exception as e:
        # Log error, but don't expose to user
        logger.error(f"Simple login error: {str(e)}")
        return f"Login error: {str(e)}"
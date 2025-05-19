"""
Test script to debug login functionality.
"""
import os
import logging
from flask import Flask, render_template, redirect, flash
from flask_login import LoginManager, login_user, current_user, logout_user
from models import User
from app import db
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_login(email, password):
    """
    Test the login functionality with the given credentials.
    
    Args:
        email: The user's email
        password: The user's password
        
    Returns:
        bool: True if login is successful, False otherwise
    """
    try:
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.error(f"User with email {email} not found")
            return False
            
        # Test password check
        if user.check_password(password):
            logger.info(f"Login successful for user {email}")
            return True
        else:
            logger.error(f"Password check failed for user {email}")
            return False
            
    except Exception as e:
        logger.error(f"Error during login test: {str(e)}")
        return False

def main():
    """Main function to test login."""
    # Get credentials from command line
    if len(sys.argv) < 3:
        print("Usage: python test_login.py <email> <password>")
        return

    email = sys.argv[1]
    password = sys.argv[2]
    
    # Test login
    success = test_login(email, password)
    
    if success:
        print("Login test successful!")
    else:
        print("Login test failed.")

if __name__ == "__main__":
    # Import the Flask app and context
    from app import app
    
    # Use app context for database operations
    with app.app_context():
        main()
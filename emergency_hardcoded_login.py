"""
Absolutely emergency hardcoded login for Render.com only.

This solution is ONLY for emergency use when nothing else works.
"""

import os
import logging
from flask import Blueprint, redirect, request, session, flash
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
hardcoded_login_bp = Blueprint('hardcoded_login', __name__)

# Test user credentials for emergency use
TEST_USER_EMAIL = "teddy.leon@alumni.uwi.edu"
TEST_USER_PASSWORD = "Teddy1973"  # Already publicly known test password

@hardcoded_login_bp.route('/test-login', methods=['GET', 'POST'])
def test_login():
    """
    Emergency test login that uses hardcoded test credentials
    to bypass database issues completely.
    """
    if current_user.is_authenticated:
        return redirect('/dashboard')
        
    from app import db
    from models import User
    
    # Check if the test user exists
    test_user = None
    try:
        logger.info("Attempting to find test user...")
        test_user = User.query.filter(User.email.ilike(TEST_USER_EMAIL)).first()
    except Exception as e:
        logger.error(f"Error finding test user: {str(e)}")
    
    # If user doesn't exist in the database, create them
    if not test_user:
        try:
            logger.info("Test user not found, creating...")
            # Create user differently based on what fields the model has
            test_user = User()
            test_user.email = TEST_USER_EMAIL
            test_user.username = TEST_USER_EMAIL.split('@')[0]
            test_user.password_hash = generate_password_hash(TEST_USER_PASSWORD)
            db.session.add(test_user)
            db.session.commit()
            logger.info(f"Created test user with ID: {test_user.id}")
        except Exception as e:
            logger.error(f"Error creating test user: {str(e)}")
            return f"""
            <html>
            <head><title>Error</title></head>
            <body>
                <h1>Database Error</h1>
                <p>Unable to create test user: {str(e)}</p>
                <p><a href="/">Return to Home</a></p>
            </body>
            </html>
            """
    
    if request.method == 'POST':
        # Use hardcoded credentials
        entered_email = request.form.get('email', '').strip().lower() 
        entered_password = request.form.get('password', '')
        
        logger.info(f"Test login attempt with email: {entered_email}")
        
        # Check if this matches our test user
        if entered_email.lower() == TEST_USER_EMAIL.lower() and entered_password == TEST_USER_PASSWORD:
            try:
                # Force login the user
                login_user(test_user, remember=True)
                
                # Set super-durable session
                session.permanent = True
                session['authenticated_user_id'] = test_user.id
                session['admin_impersonation'] = False
                session['test_login'] = True
                session.modified = True
                
                logger.info(f"Test login successful for {TEST_USER_EMAIL}")
                
                # Redirect to dashboard
                return redirect('/dashboard?auth=emergency')
            except Exception as e:
                logger.error(f"Error during login: {str(e)}")
                flash(f"Login error: {str(e)}")
        else:
            logger.error("Invalid test credentials")
            flash("Invalid test credentials")
    
    # Simple inline HTML for the login form
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Login - Dear Teddy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f7f7f7; margin: 0; padding: 20px; }}
            .container {{ max-width: 400px; margin: 40px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1, h2 {{ text-align: center; color: #A05C2C; }}
            form {{ margin-top: 20px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input[type="email"], input[type="password"] {{ width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
            button {{ background-color: #A05C2C; color: white; border: none; padding: 12px 15px; width: 100%; border-radius: 4px; cursor: pointer; font-size: 16px; }}
            .alert {{ background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin-bottom: 15px; }}
            .note {{ font-size: 12px; color: #666; margin-top: 15px; text-align: center; }}
            .badge {{ display: inline-block; background-color: #dc3545; color: white; font-size: 11px; padding: 3px 7px; border-radius: 10px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Dear Teddy</h2>
            <h3>Emergency Test Login</h3>
            
            <p style="text-align:center;color:#721c24;background-color:#f8d7da;padding:10px;border-radius:5px;">
                This is an emergency test login. Use these credentials:
                <br><strong>Email:</strong> {TEST_USER_EMAIL}
                <br><strong>Password:</strong> {TEST_USER_PASSWORD}
            </p>
            
            <form method="POST" action="/test-login" novalidate>
                <div>
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" value="{TEST_USER_EMAIL}" required>
                </div>
                <div>
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" value="{TEST_USER_PASSWORD}" required>
                </div>
                <button type="submit">Log In</button>
            </form>
            
            <div style="text-align:center;margin-top:20px;">
                <a href="/emergency-login" style="color:#A05C2C;text-decoration:none;">Try Emergency Login</a>
                <div>
                    <span class="badge">EMERGENCY TEST LOGIN</span>
                </div>
                <p class="note">This page bypasses authentication for test purposes only.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def register_hardcoded_login(app):
    """Register the hardcoded login blueprint with the application."""
    # Register blueprint
    app.register_blueprint(hardcoded_login_bp)
    
    # Add shortcut route
    @app.route('/hc-login')
    def hc_login_shortcut():
        """Shortcut to hardcoded login"""
        return redirect('/test-login')
    
    # Exempt from CSRF
    if hasattr(app, 'csrf'):
        app.csrf.exempt(hardcoded_login_bp)
        app.csrf.exempt(hc_login_shortcut)
    
    logger.info("Hardcoded test login registered")
    return app
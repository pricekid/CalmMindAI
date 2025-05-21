"""
Ultra-simplified direct login for Render.com

This completely bypasses all security checks including CSRF
for emergency use on Render.com only.
"""

import os
import logging
from flask import Blueprint, render_template, redirect, request, session, current_app
from flask_login import login_user, current_user, UserMixin
from sqlalchemy import or_, func
from sqlalchemy.exc import NoResultFound

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint that completely avoids CSRF
emergency_render_bp = Blueprint('emergency_render', __name__, template_folder='templates')

@emergency_render_bp.route('/emergency-login', methods=['GET', 'POST'])
def emergency_login():
    """
    Ultra-simplified emergency login for Render.com deployments
    that completely bypasses all security protections.
    """
    from models import User
    from app import db
    
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    error = None
    
    if request.method == 'POST':
        try:
            # Get email and password from form
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            logger.info(f"Emergency login attempt for: {email}")
            
            # Find user without regard to case
            user = db.session.query(User).filter(
                func.lower(User.email) == func.lower(email)
            ).first()
            
            if user and user.check_password(password):
                # Login the user bypassing all protections
                login_user(user, remember=True)
                
                # Set super-durable session
                session.permanent = True
                session['authenticated_user_id'] = user.id
                session['emergency_auth'] = True
                session['render_session'] = True
                session.modified = True
                
                logger.info(f"Emergency login SUCCESSFUL for user {user.id}")
                
                # Redirect with special flags
                return redirect('/dashboard?auth=true&emergency=true&ts=' + str(os.urandom(4).hex()))
            else:
                error = "Invalid email or password."
                logger.warning(f"Emergency login FAILED for email: {email}")
        except Exception as e:
            logger.error(f"Error in emergency login: {str(e)}")
            error = "An unexpected error occurred."
    
    # Simple hardcoded HTML to avoid template issues
    if error:
        error_html = f'<div style="color:white;background-color:#dc3545;padding:10px;margin-bottom:20px;border-radius:5px;">{error}</div>'
    else:
        error_html = ''
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Login - Dear Teddy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background-color: #f8f9fa; font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            .container {{ max-width: 400px; margin: 50px auto; padding: 20px; }}
            .login-form {{ background-color: white; border-radius: 10px; padding: 30px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            h1, h2 {{ text-align: center; color: #333; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input[type="email"], input[type="password"] {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .btn {{ display: block; width: 100%; padding: 12px; background-color: #A05C2C; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }}
            .alert {{ padding: 10px; background-color: #f44336; color: white; margin-bottom: 20px; border-radius: 5px; }}
            .emergency-badge {{ display: inline-block; background-color: #ff9800; color: white; font-size: 12px; padding: 3px 8px; border-radius: 10px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="login-form">
                <h2>Dear Teddy</h2>
                <h3>Emergency Login</h3>
                
                {error_html}
                
                <form method="POST" action="/emergency-login" novalidate>
                    <div class="form-group">
                        <label for="email">Email Address</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                
                <div style="text-align:center;margin-top:20px;">
                    <a href="/r-login" style="color:#A05C2C;text-decoration:none;">Return to Regular Login</a>
                    <div>
                        <span class="emergency-badge">Emergency Override Login</span>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def register_emergency_render_routes(app):
    """Register the emergency Render-specific routes with the app."""
    # Register blueprint
    app.register_blueprint(emergency_render_bp)
    
    # Add a route to the root
    @app.route('/er-login')
    def er_login_shortcut():
        """Shortcut to emergency login"""
        return redirect('/emergency-login')
    
    # Exempt from CSRF
    if hasattr(app, 'csrf'):
        app.csrf.exempt(emergency_render_bp)
        app.csrf.exempt(er_login_shortcut)
    
    logger.info("Emergency Render login routes registered successfully")
    return app
"""
Emergency fix to address login issues related to the Reflective Pause feature.
This file provides a clean implementation without dependencies on the problematic code.
"""
import os
import logging
from flask import Blueprint, render_template_string, redirect, request, flash, session
from flask_login import login_user, login_required, current_user
from models import User
from app import db

# Set up logger
logger = logging.getLogger(__name__)

emergency_fix_bp = Blueprint('emergency_fix', __name__)

# Super simple login template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Emergency Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; max-width: 500px; margin: 40px auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #4a5568; margin-top: 0; }
        input[type="email"], input[type="password"] { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #e2e8f0; border-radius: 4px; }
        button { background: #4299e1; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #3182ce; }
        .error { color: #e53e3e; margin-bottom: 15px; }
        .checkbox { margin-bottom: 15px; }
        .footer { text-align: center; margin-top: 20px; font-size: 0.9em; color: #718096; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Emergency Login</h1>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <div>
                <input type="email" name="email" placeholder="Email" required>
            </div>
            <div>
                <input type="password" name="password" placeholder="Password" required>
            </div>
            <div class="checkbox">
                <label>
                    <input type="checkbox" name="remember"> Remember me
                </label>
            </div>
            <button type="submit">Login</button>
        </form>
    </div>
    <div class="footer">
        <p>This is an emergency login page to bypass the regular login system.</p>
    </div>
</body>
</html>
"""

# Simple dashboard template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Emergency Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #4a5568; }
        a { color: #4299e1; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .button { 
            display: inline-block; 
            background: #4299e1; 
            color: white; 
            padding: 10px 15px; 
            border-radius: 4px; 
            text-decoration: none;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        .button:hover { background: #3182ce; text-decoration: none; }
        .journal-entry { 
            border-left: 4px solid #4299e1; 
            padding-left: 15px; 
            margin-bottom: 15px;
        }
        .date { color: #718096; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome, {{ user.username }}</h1>
        <a href="/emergency-logout" class="button">Logout</a>
    </div>
    
    <div class="card">
        <h2>Emergency Navigation</h2>
        <p>Use these links to navigate to key features:</p>
        <div>
            <a href="/journal" class="button">Journal List</a>
            <a href="/emergency-simple-dashboard" class="button">Simple Dashboard</a>
            <a href="/dashboard" class="button">Try Regular Dashboard</a>
        </div>
    </div>
    
    <div class="card">
        <h2>Recent Entries</h2>
        {% if entries %}
            {% for entry in entries %}
                <div class="journal-entry">
                    <h3><a href="/journal/{{ entry.id }}">{{ entry.title }}</a></h3>
                    <div class="date">{{ entry.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
                </div>
            {% endfor %}
        {% else %}
            <p>No journal entries found.</p>
        {% endif %}
    </div>
    
    <div class="card">
        <h2>User Information</h2>
        <p>User ID: {{ user.id }}</p>
        <p>Email: {{ user.email }}</p>
    </div>
</body>
</html>
"""

# Simple user list template for direct login
USER_LIST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>User List</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; max-width: 800px; margin: 40px auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #4a5568; margin-top: 0; }
        .user-list { list-style: none; padding: 0; }
        .user-item { padding: 10px; border-bottom: 1px solid #e2e8f0; }
        .user-item:last-child { border-bottom: none; }
        .user-item a { display: block; color: #4299e1; text-decoration: none; }
        .user-item a:hover { color: #3182ce; }
        .footer { text-align: center; margin-top: 20px; font-size: 0.9em; color: #718096; }
        .button { 
            display: inline-block; 
            background: #4299e1; 
            color: white; 
            padding: 10px 15px; 
            border-radius: 4px; 
            text-decoration: none;
        }
        .button:hover { background: #3182ce; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <h1>User List</h1>
        <p>Click on a user to login without password:</p>
        <ul class="user-list">
            {% for user in users %}
                <li class="user-item">
                    <a href="/emergency-login-with-id/{{ user.id }}">
                        {{ user.username }} ({{ user.email }})
                    </a>
                </li>
            {% endfor %}
        </ul>
        <div style="margin-top: 20px;">
            <a href="/emergency-login" class="button">Regular Login</a>
        </div>
    </div>
    <div class="footer">
        <p>This is an emergency login system to bypass the regular login system.</p>
    </div>
</body>
</html>
"""

@emergency_fix_bp.route('/emfix-login', methods=['GET', 'POST'])
def emergency_login():
    """
    Clean login implementation without dependencies on the problematic code.
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect('/emfix-dashboard')
    
    error = None
    
    # Handle login form submission
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = 'remember' in request.form
        
        if not email or not password:
            error = "Email and password are required."
        else:
            # Find user and validate password
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                # Login successful
                login_user(user, remember=remember)
                logger.info(f"Emergency login successful for user: {email}")
                
                # Redirect to next parameter or dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect('/emfix-dashboard')
            else:
                error = "Invalid email or password."
                logger.warning(f"Emergency login failed for email: {email}")
    
    # Generate a CSRF token
    csrf_token = ""
    try:
        from flask_wtf.csrf import generate_csrf
        csrf_token = generate_csrf()
    except Exception as e:
        logger.error(f"CSRF generation error: {str(e)}")
    
    return render_template_string(
        LOGIN_TEMPLATE,
        csrf_token=csrf_token,
        error=error
    )

@emergency_fix_bp.route('/emergency-dashboard')
@login_required
def emergency_dashboard():
    """Simple emergency dashboard."""
    try:
        # Get a few recent journal entries with minimal fields
        from models import JournalEntry
        from sqlalchemy import desc
        
        entries = db.session.query(
            JournalEntry.id,
            JournalEntry.title,
            JournalEntry.created_at
        ).filter(
            JournalEntry.user_id == current_user.id
        ).order_by(
            desc(JournalEntry.created_at)
        ).limit(5).all()
        
        return render_template_string(
            DASHBOARD_TEMPLATE,
            user=current_user,
            entries=entries
        )
    except Exception as e:
        logger.error(f"Emergency dashboard error: {str(e)}")
        return f"Dashboard error: {str(e)}"

@emergency_fix_bp.route('/emergency-login-list')
def emergency_login_list():
    """Show a list of all users for direct login."""
    try:
        users = User.query.all()
        return render_template_string(
            USER_LIST_TEMPLATE,
            users=users
        )
    except Exception as e:
        logger.error(f"Emergency user list error: {str(e)}")
        return f"Error loading user list: {str(e)}"

@emergency_fix_bp.route('/emergency-login-with-id/<int:user_id>')
def emergency_login_with_id(user_id):
    """Login directly with user ID without password."""
    try:
        user = User.query.get(user_id)
        
        if user:
            login_user(user, remember=True)
            logger.info(f"Direct login successful for user ID: {user_id}")
            return redirect('/emergency-dashboard')
        else:
            logger.error(f"Direct login failed - user ID not found: {user_id}")
            return "User not found. Check the ID and try again."
    except Exception as e:
        logger.error(f"Direct login error: {str(e)}")
        return f"Login error: {str(e)}"

@emergency_fix_bp.route('/emergency-logout')
def emergency_logout():
    """Logout route without dependencies."""
    from flask_login import logout_user
    logout_user()
    session.clear()
    return redirect('/emergency-login')
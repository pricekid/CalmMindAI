"""
A special standalone login page that doesn't depend on any other routes or files.
This is for emergency access when the main login system is broken.
"""
import os
import logging
from flask import Blueprint, request, redirect, render_template_string, session, jsonify
from sqlalchemy import create_engine, text
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
special_login_bp = Blueprint('special_login', __name__)

# HTML template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Emergency Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2 { color: #bb86fc; }
        a { color: #03dac6; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .button { 
            display: inline-block; 
            background: #bb86fc; 
            color: #121212; 
            padding: 10px 15px; 
            border-radius: 4px; 
            font-weight: bold;
            text-decoration: none;
            margin: 5px;
        }
        .button:hover { background: #a370e3; text-decoration: none; }
        .error { color: #cf6679; font-weight: bold; }
        .success { color: #03dac6; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Emergency Access System</h1>
    
    <div class="card">
        <h2>Direct User Access</h2>
        <p>Click a user to login directly:</p>
        
        {% for user in users %}
        <a href="/special-login/{{ user.id }}" class="button">Login as {{ user.email }}</a>
        {% endfor %}
        
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
        
        {% if message %}
        <p class="success">{{ message }}</p>
        {% endif %}
    </div>
    
    <div class="card">
        <h2>What Happened?</h2>
        <p>The regular login system is experiencing issues. This emergency access page provides a temporary way to access the system.</p>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Emergency Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2, h3 { color: #bb86fc; }
        a { color: #03dac6; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .button { 
            display: inline-block; 
            background: #bb86fc; 
            color: #121212; 
            padding: 10px 15px; 
            border-radius: 4px; 
            font-weight: bold;
            text-decoration: none;
            margin: 5px;
        }
        .button:hover { background: #a370e3; text-decoration: none; }
        .journal-entry { 
            border-left: 4px solid #03dac6; 
            padding-left: 15px; 
            margin-bottom: 15px;
        }
        .date { color: #78909c; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>Emergency Dashboard</h1>
    <p>User: {{ user.email }} (ID: {{ user.id }})</p>
    
    <div class="card">
        <h2>Emergency Navigation</h2>
        <a href="/special-logout" class="button">Logout</a>
        <a href="/special-entries" class="button">Journal Entries</a>
        <a href="/test-reflection" class="button">Test Reflection</a>
    </div>
    
    <div class="card">
        <h2>Recent Journal Entries</h2>
        {% if entries %}
            {% for entry in entries %}
                <div class="journal-entry">
                    <h3><a href="/special-entry/{{ entry.id }}">{{ entry.title }}</a></h3>
                    <div class="date">{{ entry.created_at }}</div>
                </div>
            {% endfor %}
        {% else %}
            <p>No journal entries found for this user.</p>
        {% endif %}
    </div>
    
    <div class="card">
        <h2>Help</h2>
        <p>This is a simplified emergency dashboard.</p>
        <p>Use the "Test Reflection" button to directly test the Reflective Pause feature.</p>
    </div>
</body>
</html>
"""

# Helper functions
def get_db_connection():
    """Create a direct database connection."""
    try:
        connection_string = os.environ.get('DATABASE_URL')
        engine = create_engine(connection_string)
        return engine.connect()
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

# Routes
@special_login_bp.route('/special-login-page')
def special_login_page():
    """Display the emergency login page."""
    users = []
    error = request.args.get('error')
    message = request.args.get('message')
    
    # Get users from the database
    conn = get_db_connection()
    if conn:
        try:
            result = conn.execute(text("SELECT id, email FROM \"user\" ORDER BY id LIMIT 10"))
            for row in result:
                users.append({
                    "id": row[0],
                    "email": row[1]
                })
        except Exception as e:
            logger.error(f"Error querying users: {str(e)}")
            error = f"Database error: {str(e)}"
        finally:
            conn.close()
    else:
        error = "Could not connect to database."
    
    return render_template_string(
        LOGIN_TEMPLATE,
        users=users,
        error=error,
        message=message
    )

@special_login_bp.route('/special-login/<int:user_id>')
def special_login(user_id):
    """Login a user directly by ID."""
    conn = get_db_connection()
    if conn:
        try:
            # Get user
            result = conn.execute(text("SELECT id, email FROM \"user\" WHERE id = :id"), {"id": user_id})
            user = None
            for row in result:
                user = {
                    "id": row[0],
                    "email": row[1]
                }
                break
            
            if user:
                # Store user in session
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['is_authenticated'] = True
                session['login_time'] = datetime.now().isoformat()
                
                # Redirect to dashboard
                return redirect(f'/special-dashboard')
            else:
                return redirect(f'/special-login-page?error=User+not+found')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return redirect(f'/special-login-page?error={str(e)}')
        finally:
            conn.close()
    else:
        return redirect(f'/special-login-page?error=Database+connection+failed')

@special_login_bp.route('/special-dashboard')
def special_dashboard():
    """Display the emergency dashboard."""
    # Check if user is logged in
    if not session.get('is_authenticated'):
        return redirect('/special-login-page?error=Not+logged+in')
    
    user = {
        "id": session.get('user_id'),
        "email": session.get('user_email')
    }
    
    # Get recent entries
    entries = []
    conn = get_db_connection()
    if conn:
        try:
            result = conn.execute(text("""
                SELECT id, title, created_at 
                FROM journal_entry 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC 
                LIMIT 5
            """), {"user_id": user['id']})
            
            for row in result:
                entries.append({
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2]
                })
        except Exception as e:
            logger.error(f"Error fetching entries: {str(e)}")
        finally:
            conn.close()
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        user=user,
        entries=entries
    )

@special_login_bp.route('/special-logout')
def special_logout():
    """Logout user by clearing session."""
    session.clear()
    return redirect('/special-login-page?message=Successfully+logged+out')

@special_login_bp.route('/special-entries')
def special_entries():
    """Display all journal entries for the user."""
    # Check if user is logged in
    if not session.get('is_authenticated'):
        return redirect('/special-login-page?error=Not+logged+in')
    
    # This is a simplified version, in reality would fetch all entries
    return redirect('/special-dashboard')

@special_login_bp.route('/special-entry/<int:entry_id>')
def special_entry(entry_id):
    """View a specific journal entry."""
    # Check if user is logged in
    if not session.get('is_authenticated'):
        return redirect('/special-login-page?error=Not+logged+in')
    
    # This is a simplified version, in reality would fetch the entry
    # For now just redirect to the test reflection page to try the reflection feature
    return redirect('/test-reflection?entry_id=' + str(entry_id))
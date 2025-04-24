"""
Simple dashboard page that avoids the complex queries
and just shows basic information without any error-prone operations.
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template_string, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models import JournalEntry

# Set up logger
logger = logging.getLogger(__name__)

simple_dashboard_bp = Blueprint('simple_dashboard', __name__)

# Simple template with minimal data and no complex queries
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #181818; color: #e0e0e0; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .card { background: #2d2d30; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
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
    <div class="header">
        <h1>Welcome, {{ user.username }}</h1>
        <a href="/account" class="button">Account Settings</a>
    </div>
    
    <div class="card">
        <h2>Emergency Navigation 🚨</h2>
        <p>Use these links to navigate to key features:</p>
        <p>
            <a href="/new-journal-entry" class="button">New Journal Entry</a>
            <a href="/journal-list" class="button">Journal List</a>
            <a href="/logout" class="button">Logout</a>
            <a href="/test-reflection" class="button">Test Reflection Feature</a>
        </p>
    </div>
    
    <div class="card">
        <h2>Recent Journal Entries</h2>
        {% if journal_entries %}
            {% for entry in journal_entries %}
                <div class="journal-entry">
                    <h3><a href="/journal/{{ entry.id }}">{{ entry.title }}</a></h3>
                    <div class="date">{{ entry.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
                </div>
            {% endfor %}
        {% else %}
            <p>No journal entries yet. <a href="/new-journal-entry">Create your first entry</a>.</p>
        {% endif %}
    </div>
    
    <div class="card">
        <h2>Debug Information</h2>
        <p>User ID: {{ user.id }}</p>
        <p>Email: {{ user.email }}</p>
        <p>Last Login: {{ last_login }}</p>
    </div>
</body>
</html>
"""

@simple_dashboard_bp.route('/simple-dashboard')
@login_required
def simple_dashboard():
    """
    Simplified dashboard with minimal queries to avoid errors.
    """
    try:
        # Get a few recent journal entries, just the minimal fields
        journal_entries = db.session.query(
            JournalEntry.id, 
            JournalEntry.title, 
            JournalEntry.created_at
        ).filter(
            JournalEntry.user_id == current_user.id
        ).order_by(
            JournalEntry.created_at.desc()
        ).limit(5).all()
        
        # Format last login time
        last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log successful dashboard access
        logger.info(f"User {current_user.id} accessed simple dashboard")
        
        return render_template_string(
            DASHBOARD_TEMPLATE,
            user=current_user,
            journal_entries=journal_entries,
            last_login=last_login
        )
    except Exception as e:
        logger.error(f"Error in simple dashboard: {str(e)}")
        return f"Dashboard error: {str(e)}"

# Add a fallback route that redirects to the simple dashboard
@simple_dashboard_bp.route('/dashboard')
@login_required
def dashboard_redirect():
    """
    Redirect from the regular dashboard to the simple one to avoid errors.
    """
    return redirect('/simple-dashboard')
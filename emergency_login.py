"""
Super simplified emergency login and dashboard with no dependencies on other routes.
This is a standalone system to regain access when the main system is broken.
"""
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, select
from sqlalchemy.orm import Session
from flask import Blueprint, request, render_template_string, redirect

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
emergency_bp = Blueprint('emergency', __name__)

# Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Emergency Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #2d2d30; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
        h1, h2 { color: #bb86fc; }
        input[type="text"], input[type="password"] { 
            width: 100%; 
            padding: 10px; 
            margin: 10px 0; 
            border-radius: 4px;
            border: none;
            background: #121212;
            color: #e0e0e0;
        }
        button { 
            background: #bb86fc; 
            color: #121212; 
            padding: 10px 15px; 
            border: none;
            border-radius: 4px; 
            font-weight: bold;
            cursor: pointer;
        }
        button:hover { background: #a370e3; }
        .error { color: #cf6679; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Emergency Access System</h1>
    
    <div class="card">
        <h2>Direct User ID Login</h2>
        <p>Enter a user ID to login directly:</p>
        
        <form method="GET" action="/emergency/login">
            <input type="text" name="user_id" placeholder="User ID (e.g., 1, 2, 3)" required>
            <button type="submit">Login</button>
        </form>
        
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
    </div>
    
    <div class="card">
        <h2>Available User IDs</h2>
        <ul>
        {% for user in users %}
            <li>ID: {{ user.id }} - {{ user.email }}</li>
        {% endfor %}
        </ul>
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
        .card { background: #2d2d30; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
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
        .error { color: #cf6679; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Emergency Dashboard</h1>
    <p>User: {{ user.email }} (ID: {{ user.id }})</p>
    
    <div class="card">
        <h2>Navigation</h2>
        <a href="/emergency/dashboard" class="button">Dashboard</a>
        <a href="/emergency/journals" class="button">Journal Entries</a>
        <a href="/emergency/logout" class="button">Logout</a>
        <a href="/emergency/test-reflection" class="button">Test Reflection</a>
    </div>
    
    <div class="card">
        <h2>Recent Journal Entries</h2>
        {% if entries %}
            {% for entry in entries %}
                <div class="journal-entry">
                    <h3><a href="/emergency/journal/{{ entry.id }}">{{ entry.title }}</a></h3>
                    <div class="date">{{ entry.created_at }}</div>
                </div>
            {% endfor %}
        {% else %}
            <p>No journal entries found for this user.</p>
        {% endif %}
    </div>
    
    {% if error %}
    <div class="card">
        <h2 class="error">Error</h2>
        <p>{{ error }}</p>
    </div>
    {% endif %}
</body>
</html>
"""

JOURNAL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Journal Entry</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #2d2d30; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
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
        }
        .button:hover { background: #a370e3; text-decoration: none; }
        .date { color: #78909c; font-size: 0.9em; margin-bottom: 15px; }
        .content { white-space: pre-line; }
        .reflection { 
            background: #1e3c45; 
            border-radius: 4px;
            padding: 15px; 
            margin: 20px 0;
            border-left: 4px solid #03dac6;
        }
        form { margin-top: 20px; }
        textarea { 
            width: 100%; 
            min-height: 100px; 
            background: #121212;
            color: #e0e0e0;
            border: 1px solid #666;
            padding: 10px;
            border-radius: 4px;
        }
        .error { color: #cf6679; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Journal Entry</h1>
    
    <div class="card">
        <a href="/emergency/dashboard" class="button">Back to Dashboard</a>
    </div>
    
    {% if entry %}
    <div class="card">
        <h2>{{ entry.title }}</h2>
        <div class="date">Created: {{ entry.created_at }}</div>
        
        <div class="content">{{ entry.content }}</div>
        
        {% if entry.user_reflection %}
        <h3>Your Reflection</h3>
        <div class="reflection">{{ entry.user_reflection }}</div>
        {% else %}
        <h3>Add Your Reflection</h3>
        <form method="POST" action="/emergency/reflection/{{ entry.id }}">
            <textarea name="reflection" placeholder="Add your thoughts here..."></textarea>
            <button type="submit" class="button">Save Reflection</button>
        </form>
        {% endif %}
    </div>
    {% else %}
    <div class="card">
        <h2 class="error">Entry Not Found</h2>
        <p>The requested journal entry could not be found.</p>
    </div>
    {% endif %}
    
    {% if error %}
    <div class="card">
        <h2 class="error">Error</h2>
        <p>{{ error }}</p>
    </div>
    {% endif %}
</body>
</html>
"""

# Get database connection
def get_db_connection():
    """Get a database connection using SQLAlchemy directly."""
    try:
        connection_string = os.environ.get('DATABASE_URL')
        engine = create_engine(connection_string)
        return engine.connect()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

# Define tables
def get_tables():
    """Get tables for direct access."""
    metadata = MetaData()
    
    users = Table(
        'user', metadata,
        Column('id', Integer, primary_key=True),
        Column('username', String),
        Column('email', String)
    )
    
    journal_entries = Table(
        'journal_entry', metadata,
        Column('id', Integer, primary_key=True),
        Column('user_id', Integer),
        Column('title', String),
        Column('content', Text),
        Column('created_at', String),
        Column('user_reflection', Text)
    )
    
    return users, journal_entries

# Emergency endpoints
@emergency_bp.route('/emergency')
def emergency_login_page():
    """Emergency login page."""
    error = request.args.get('error')
    
    # Get all users for selection
    users = []
    try:
        users_table, _ = get_tables()
        conn = get_db_connection()
        if conn:
            result = conn.execute(select(users_table.c.id, users_table.c.email))
            users = [{"id": row[0], "email": row[1]} for row in result]
            conn.close()
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
    
    return render_template_string(
        LOGIN_TEMPLATE,
        users=users,
        error=error
    )

@emergency_bp.route('/emergency/login')
def emergency_login():
    """Direct login with user ID."""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return redirect('/emergency?error=No+user+ID+provided')
    
    try:
        users_table, _ = get_tables()
        conn = get_db_connection()
        if conn:
            result = conn.execute(
                select(users_table.c.id, users_table.c.email)
                .where(users_table.c.id == user_id)
            ).first()
            
            if result:
                # Store in session (this is a simplified approach without session)
                # We'll pass user ID in URL parameters
                conn.close()
                return redirect(f'/emergency/dashboard?user_id={user_id}')
            else:
                conn.close()
                return redirect(f'/emergency?error=User+ID+{user_id}+not+found')
        else:
            return redirect('/emergency?error=Database+connection+failed')
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return redirect(f'/emergency?error={str(e)}')

@emergency_bp.route('/emergency/dashboard')
def emergency_dashboard():
    """Emergency dashboard."""
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect('/emergency?error=No+user+ID+provided')
    
    try:
        users_table, journal_entries_table = get_tables()
        conn = get_db_connection()
        
        if conn:
            # Get user
            user = conn.execute(
                select(users_table.c.id, users_table.c.email)
                .where(users_table.c.id == user_id)
            ).first()
            
            if not user:
                conn.close()
                return redirect('/emergency?error=User+not+found')
            
            # Get recent entries
            entries = conn.execute(
                select(
                    journal_entries_table.c.id,
                    journal_entries_table.c.title,
                    journal_entries_table.c.created_at
                )
                .where(journal_entries_table.c.user_id == user_id)
                .order_by(journal_entries_table.c.created_at.desc())
                .limit(5)
            ).fetchall()
            
            user_obj = {"id": user[0], "email": user[1]}
            entries_list = [
                {"id": entry[0], "title": entry[1], "created_at": entry[2]}
                for entry in entries
            ]
            
            conn.close()
            return render_template_string(
                DASHBOARD_TEMPLATE,
                user=user_obj,
                entries=entries_list,
                error=None
            )
        else:
            return redirect('/emergency?error=Database+connection+failed')
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return redirect(f'/emergency?error={str(e)}')

@emergency_bp.route('/emergency/journal/<int:entry_id>')
def view_journal_entry(entry_id):
    """View a specific journal entry."""
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect('/emergency?error=No+user+ID+provided')
    
    try:
        _, journal_entries_table = get_tables()
        conn = get_db_connection()
        
        if conn:
            entry = conn.execute(
                select(
                    journal_entries_table.c.id,
                    journal_entries_table.c.title,
                    journal_entries_table.c.content,
                    journal_entries_table.c.created_at,
                    journal_entries_table.c.user_reflection
                )
                .where(
                    (journal_entries_table.c.id == entry_id) &
                    (journal_entries_table.c.user_id == user_id)
                )
            ).first()
            
            conn.close()
            
            if entry:
                entry_obj = {
                    "id": entry[0],
                    "title": entry[1],
                    "content": entry[2],
                    "created_at": entry[3],
                    "user_reflection": entry[4]
                }
                return render_template_string(
                    JOURNAL_TEMPLATE,
                    entry=entry_obj,
                    error=None
                )
            else:
                return render_template_string(
                    JOURNAL_TEMPLATE,
                    entry=None,
                    error="Entry not found or does not belong to you"
                )
        else:
            return redirect('/emergency?error=Database+connection+failed')
    except Exception as e:
        logger.error(f"View journal error: {str(e)}")
        return render_template_string(
            JOURNAL_TEMPLATE,
            entry=None,
            error=f"Error: {str(e)}"
        )

@emergency_bp.route('/emergency/reflection/<int:entry_id>', methods=['POST'])
def save_reflection(entry_id):
    """Save a reflection for a journal entry."""
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect('/emergency?error=No+user+ID+provided')
    
    reflection = request.form.get('reflection')
    if not reflection:
        return redirect(f'/emergency/journal/{entry_id}?user_id={user_id}&error=No+reflection+provided')
    
    try:
        _, journal_entries_table = get_tables()
        conn = get_db_connection()
        
        if conn:
            # Update the entry with reflection
            conn.execute(
                journal_entries_table.update()
                .where(
                    (journal_entries_table.c.id == entry_id) &
                    (journal_entries_table.c.user_id == user_id)
                )
                .values(user_reflection=reflection)
            )
            
            conn.close()
            return redirect(f'/emergency/journal/{entry_id}?user_id={user_id}')
        else:
            return redirect(f'/emergency/journal/{entry_id}?user_id={user_id}&error=Database+connection+failed')
    except Exception as e:
        logger.error(f"Save reflection error: {str(e)}")
        return redirect(f'/emergency/journal/{entry_id}?user_id={user_id}&error={str(e)}')

@emergency_bp.route('/emergency/journals')
def journal_list():
    """List all journal entries for the user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect('/emergency?error=No+user+ID+provided')
    
    try:
        users_table, journal_entries_table = get_tables()
        conn = get_db_connection()
        
        if conn:
            # Get user
            user = conn.execute(
                select(users_table.c.id, users_table.c.email)
                .where(users_table.c.id == user_id)
            ).first()
            
            if not user:
                conn.close()
                return redirect('/emergency?error=User+not+found')
            
            # Get all entries
            entries = conn.execute(
                select(
                    journal_entries_table.c.id,
                    journal_entries_table.c.title,
                    journal_entries_table.c.created_at
                )
                .where(journal_entries_table.c.user_id == user_id)
                .order_by(journal_entries_table.c.created_at.desc())
            ).fetchall()
            
            user_obj = {"id": user[0], "email": user[1]}
            entries_list = [
                {"id": entry[0], "title": entry[1], "created_at": entry[2]}
                for entry in entries
            ]
            
            conn.close()
            return render_template_string(
                DASHBOARD_TEMPLATE,
                user=user_obj,
                entries=entries_list,
                error=None
            )
        else:
            return redirect('/emergency?error=Database+connection+failed')
    except Exception as e:
        logger.error(f"Journal list error: {str(e)}")
        return redirect(f'/emergency?error={str(e)}')

@emergency_bp.route('/emergency/logout')
def emergency_logout():
    """Logout."""
    return redirect('/emergency')
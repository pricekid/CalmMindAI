"""
Completely standalone script to test journal entry reflections.
This script connects directly to the database and performs operations
without any dependencies on Flask or other complex parts of the system.
"""
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, request, render_template_string

# Create a minimal Flask application
app = Flask(__name__)
app.secret_key = "standalone_test_key"

# Database connection
def get_db_connection():
    """Get a database connection using psycopg2."""
    try:
        connection_string = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(connection_string)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None

# HTML template
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Standalone Reflection Test</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2, h3 { color: #bb86fc; }
        .content { white-space: pre-line; }
        .meta { color: #78909c; font-size: 0.9em; margin-bottom: 15px; }
        .reflection { background: #263238; border-left: 4px solid #bb86fc; padding: 15px; margin: 20px 0; }
        .reflection-form { margin-top: 20px; }
        textarea { 
            width: 100%; 
            padding: 10px; 
            background: #2d2d30; 
            color: #e0e0e0; 
            border: 1px solid #444; 
            border-radius: 4px;
            min-height: 100px;
        }
        .button {
            display: inline-block;
            background: #bb86fc;
            color: #121212;
            padding: 10px 15px;
            margin-top: 10px;
            border: none;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
        }
        .button:hover { background: #a370e3; }
        .error { color: #cf6679; font-weight: bold; }
        .success { color: #03dac6; font-weight: bold; }
        .nav { margin-bottom: 20px; }
        .nav a { 
            color: #03dac6; 
            text-decoration: none;
            margin-right: 15px;
        }
        .nav a:hover { text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; }
        table th, table td { padding: 8px; text-align: left; border-bottom: 1px solid #333; }
        table th { color: #bb86fc; }
    </style>
</head>
<body>
    <h1>Standalone Reflection Test</h1>
    
    <div class="nav">
        <a href="/standalone">Home</a>
        <a href="/standalone/users">Users</a>
        <a href="/standalone/entries">All Entries</a>
    </div>
    
    {% if message %}
    <div class="card">
        <p class="{% if success %}success{% else %}error{% endif %}">{{ message }}</p>
    </div>
    {% endif %}
    
    {% if section == 'home' %}
    <div class="card">
        <h2>Test Environment</h2>
        <p>This is a standalone test environment for journal entry reflections.</p>
        <p>Use the links above to navigate and test reflection functionality directly.</p>
    </div>
    
    <div class="card">
        <h2>Database Connection</h2>
        <p>Status: <span class="{% if db_connected %}success{% else %}error{% endif %}">
            {{ 'Connected' if db_connected else 'Not connected' }}
        </span></p>
        {% if db_error %}
        <p class="error">{{ db_error }}</p>
        {% endif %}
    </div>
    {% endif %}
    
    {% if section == 'users' %}
    <div class="card">
        <h2>Users</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Email</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <td>{{ user.id }}</td>
                    <td>{{ user.email }}</td>
                    <td><a href="/standalone/entries?user_id={{ user.id }}">View Entries</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}
    
    {% if section == 'entries' %}
    <div class="card">
        <h2>Journal Entries{% if user %} for {{ user.email }}{% endif %}</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Created</th>
                    <th>Has Reflection</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for entry in entries %}
                <tr>
                    <td>{{ entry.id }}</td>
                    <td>{{ entry.title }}</td>
                    <td>{{ entry.created_at }}</td>
                    <td>
                        {% if entry.has_reflection %}
                        <span class="success">Yes</span>
                        {% else %}
                        <span class="error">No</span>
                        {% endif %}
                    </td>
                    <td><a href="/standalone/entry/{{ entry.id }}">View</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}
    
    {% if section == 'entry' and entry %}
    <div class="card">
        <h2>{{ entry.title }}</h2>
        <div class="meta">
            Created: {{ entry.created_at }}<br>
            User: {{ user.email if user else 'Unknown' }} (ID: {{ entry.user_id }})
        </div>
        
        <h3>Content</h3>
        <div class="content">{{ entry.content }}</div>
        
        {% if entry.user_reflection %}
        <h3>User Reflection</h3>
        <div class="reflection">{{ entry.user_reflection }}</div>
        {% else %}
        <h3>Add Reflection</h3>
        <form class="reflection-form" method="POST" action="/standalone/save-reflection/{{ entry.id }}">
            <textarea name="reflection" placeholder="Enter your reflection here..." required></textarea>
            <button type="submit" class="button">Save Reflection</button>
        </form>
        {% endif %}
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/standalone')
def home():
    """Home page for standalone testing."""
    # Test database connection
    conn = get_db_connection()
    db_connected = conn is not None
    db_error = None
    
    if conn:
        conn.close()
    else:
        db_error = "Could not connect to database. Check DATABASE_URL environment variable."
    
    return render_template_string(
        TEMPLATE,
        section='home',
        db_connected=db_connected,
        db_error=db_error,
        message=request.args.get('message'),
        success=request.args.get('success') == 'true'
    )

@app.route('/standalone/users')
def list_users():
    """List all users."""
    conn = get_db_connection()
    users = []
    message = None
    success = False
    
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT id, email FROM \"user\" ORDER BY id")
                users = [dict(row) for row in cur.fetchall()]
        except Exception as e:
            message = f"Error loading users: {str(e)}"
        finally:
            conn.close()
    else:
        message = "Database connection failed"
    
    return render_template_string(
        TEMPLATE,
        section='users',
        users=users,
        message=message,
        success=success
    )

@app.route('/standalone/entries')
def list_entries():
    """List journal entries, optionally filtered by user."""
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    entries = []
    user = None
    message = None
    success = False
    
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get user if user_id provided
                if user_id:
                    cur.execute("SELECT id, email FROM \"user\" WHERE id = %s", (user_id,))
                    user = dict(cur.fetchone()) if cur.rowcount > 0 else None
                
                # Query for entries
                if user_id:
                    query = """
                        SELECT 
                            id, title, created_at, user_id, 
                            CASE WHEN user_reflection IS NOT NULL THEN true ELSE false END as has_reflection
                        FROM journal_entry 
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                    """
                    cur.execute(query, (user_id,))
                else:
                    query = """
                        SELECT 
                            id, title, created_at, user_id,
                            CASE WHEN user_reflection IS NOT NULL THEN true ELSE false END as has_reflection
                        FROM journal_entry 
                        ORDER BY created_at DESC
                        LIMIT 100
                    """
                    cur.execute(query)
                
                entries = [dict(row) for row in cur.fetchall()]
        except Exception as e:
            message = f"Error loading entries: {str(e)}"
        finally:
            conn.close()
    else:
        message = "Database connection failed"
    
    return render_template_string(
        TEMPLATE,
        section='entries',
        entries=entries,
        user=user,
        message=message,
        success=success
    )

@app.route('/standalone/entry/<int:entry_id>')
def view_entry(entry_id):
    """View a specific journal entry."""
    conn = get_db_connection()
    entry = None
    user = None
    message = None
    success = False
    
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT id, title, content, created_at, user_id, user_reflection
                    FROM journal_entry
                    WHERE id = %s
                """, (entry_id,))
                
                if cur.rowcount > 0:
                    entry = dict(cur.fetchone())
                    
                    # Get user info
                    cur.execute("SELECT id, email FROM \"user\" WHERE id = %s", (entry['user_id'],))
                    if cur.rowcount > 0:
                        user = dict(cur.fetchone())
                else:
                    message = f"Entry with ID {entry_id} not found"
        except Exception as e:
            message = f"Error loading entry: {str(e)}"
        finally:
            conn.close()
    else:
        message = "Database connection failed"
    
    return render_template_string(
        TEMPLATE,
        section='entry',
        entry=entry,
        user=user,
        message=message,
        success=success
    )

@app.route('/standalone/save-reflection/<int:entry_id>', methods=['POST'])
def save_reflection(entry_id):
    """Save a reflection for a journal entry."""
    conn = get_db_connection()
    reflection = request.form.get('reflection')
    message = None
    success = False
    
    if not reflection:
        message = "No reflection provided"
        return render_template_string(
            TEMPLATE,
            section='entry',
            entry=None,
            user=None,
            message=message,
            success=success
        )
    
    if conn:
        try:
            with conn.cursor() as cur:
                # First check if entry exists
                cur.execute("SELECT id FROM journal_entry WHERE id = %s", (entry_id,))
                if cur.rowcount == 0:
                    message = f"Entry with ID {entry_id} not found"
                else:
                    # Update the entry with the reflection
                    cur.execute(
                        "UPDATE journal_entry SET user_reflection = %s WHERE id = %s",
                        (reflection, entry_id)
                    )
                    message = "Reflection saved successfully"
                    success = True
        except Exception as e:
            message = f"Error saving reflection: {str(e)}"
        finally:
            conn.close()
            
        return f"<script>window.location.href = '/standalone/entry/{entry_id}?message={message}&success={'true' if success else 'false'}';</script>"
    else:
        message = "Database connection failed"
        return render_template_string(
            TEMPLATE,
            section='entry',
            entry=None,
            user=None,
            message=message,
            success=success
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
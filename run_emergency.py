"""
Completely standalone emergency application with no dependencies on the main app.
This can be run separately to access the system when the main app is broken.
"""
import os
import logging
import json
from datetime import datetime
from flask import Flask, request, session, redirect, render_template_string, flash
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML templates
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
        <a href="/emergency/login/{{ user.id }}" class="button">Login as {{ user.email }}</a>
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
        <a href="/emergency/logout" class="button">Logout</a>
        <a href="/emergency/entries" class="button">Journal Entries</a>
        <a href="/emergency/reflection-test" class="button">Test Reflection</a>
    </div>
    
    <div class="card">
        <h2>Recent Journal Entries</h2>
        {% if entries %}
            {% for entry in entries %}
                <div class="journal-entry">
                    <h3><a href="/emergency/entry/{{ entry.id }}">{{ entry.title }}</a></h3>
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

ENTRY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Journal Entry</title>
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
        .textarea {
            width: 100%;
            background: #2d2d2d;
            color: #fff;
            border: 1px solid #444;
            border-radius: 4px;
            padding: 10px;
            font-family: inherit;
            min-height: 120px;
            margin: 10px 0;
        }
        .reflection-box {
            background: #333;
            border-left: 4px solid #bb86fc;
            padding: 15px;
            margin: 20px 0;
        }
        .error { color: #cf6679; font-weight: bold; }
        .success { color: #03dac6; font-weight: bold; }
        .insight-box {
            background: #272727;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #03dac6;
        }
        form { margin: 20px 0; }
        input[type="submit"] {
            background: #03dac6;
            color: #121212;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background: #00b5a0;
        }
    </style>
</head>
<body>
    <h1>Journal Entry</h1>
    <div>
        <a href="/emergency/dashboard" class="button">Back to Dashboard</a>
        <a href="/emergency/logout" class="button">Logout</a>
    </div>
    
    {% if error %}
    <div class="card">
        <h2 class="error">Error</h2>
        <p>{{ error }}</p>
    </div>
    {% endif %}
    
    {% if success %}
    <div class="card">
        <h2 class="success">Success</h2>
        <p>{{ success }}</p>
    </div>
    {% endif %}
    
    {% if entry %}
    <div class="card">
        <h2>{{ entry.title }}</h2>
        <div class="date">{{ entry.created_at }}</div>
        <div class="journal-entry">
            <p>{{ entry.content|safe }}</p>
        </div>
        
        {% if entry.analysis_html %}
        <div class="insight-box">
            <h3>Mira's Insight</h3>
            <div>{{ entry.analysis_html|safe }}</div>
        </div>
        {% endif %}
        
        {% if entry.user_reflection %}
        <div class="reflection-box">
            <h3>Your Reflection</h3>
            <p>{{ entry.user_reflection }}</p>
        </div>
        {% endif %}
        
        {% if not entry.user_reflection %}
        <form method="POST" action="/emergency/save-reflection/{{ entry.id }}">
            <h3>Add Your Reflection</h3>
            <p>Take a moment to reflect on Mira's insight. What resonates with you?</p>
            <textarea name="reflection" class="textarea" placeholder="Share your thoughts..."></textarea>
            <input type="submit" value="Save Reflection">
        </form>
        {% else %}
        <form method="POST" action="/emergency/save-reflection/{{ entry.id }}">
            <h3>Update Your Reflection</h3>
            <textarea name="reflection" class="textarea">{{ entry.user_reflection }}</textarea>
            <input type="submit" value="Update Reflection">
        </form>
        {% endif %}
    </div>
    {% else %}
    <div class="card">
        <h2>No Entry Found</h2>
        <p>The journal entry was not found or there was an error loading it.</p>
    </div>
    {% endif %}
    
    <div class="card">
        <h3>Database Info</h3>
        <p>Reflection Column: {% if has_user_reflection %}Found{% else %}Not Found{% endif %}</p>
    </div>
</body>
</html>
"""

REFLECTION_TEST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Reflection Feature</title>
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
        .textarea {
            width: 100%;
            background: #2d2d2d;
            color: #fff;
            border: 1px solid #444;
            border-radius: 4px;
            padding: 10px;
            font-family: inherit;
            min-height: 120px;
            margin: 10px 0;
        }
        .reflection-box {
            background: #333;
            border-left: 4px solid #bb86fc;
            padding: 15px;
            margin: 20px 0;
        }
        .error { color: #cf6679; font-weight: bold; }
        .success { color: #03dac6; font-weight: bold; }
        .insight-box {
            background: #272727;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #03dac6;
        }
        form { margin: 20px 0; }
        input[type="submit"] {
            background: #03dac6;
            color: #121212;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background: #00b5a0;
        }
        pre {
            background: #222;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1>Test Reflection Feature</h1>
    <p>
        <a href="/emergency/dashboard" class="button">Return to Dashboard</a>
        <a href="/emergency/logout" class="button">Logout</a>
    </p>
    
    {% if error %}
    <div class="card">
        <h2 class="error">Error</h2>
        <p>{{ error }}</p>
    </div>
    {% endif %}
    
    {% if success %}
    <div class="card">
        <h2 class="success">Success</h2>
        <p>{{ success }}</p>
    </div>
    {% endif %}
    
    {% if entry %}
    <div class="card">
        <h2>Journal Entry</h2>
        <h3>{{ entry.title }}</h3>
        <div class="date">{{ entry.created_at }}</div>
        <div class="journal-entry">
            <p>{{ entry.content|safe }}</p>
        </div>
        
        {% if entry.analysis_html %}
        <div class="insight-box">
            <h3>Mira's Insight</h3>
            <div>{{ entry.analysis_html|safe }}</div>
        </div>
        {% endif %}
        
        {% if entry.user_reflection %}
        <div class="reflection-box">
            <h3>Your Reflection</h3>
            <p>{{ entry.user_reflection }}</p>
        </div>
        {% endif %}
        
        {% if not entry.user_reflection %}
        <form method="POST" action="/emergency/save-reflection/{{ entry.id }}">
            <h3>Add Your Reflection</h3>
            <p>Take a moment to reflect on Mira's insight. What resonates with you?</p>
            <textarea name="reflection" class="textarea" placeholder="Share your thoughts..."></textarea>
            <input type="submit" value="Save Reflection">
        </form>
        {% else %}
        <form method="POST" action="/emergency/save-reflection/{{ entry.id }}">
            <h3>Update Your Reflection</h3>
            <textarea name="reflection" class="textarea">{{ entry.user_reflection }}</textarea>
            <input type="submit" value="Update Reflection">
        </form>
        {% endif %}
    </div>
    {% else %}
    <div class="card">
        <h2>No Entry Found</h2>
        <p>The journal entry was not found or there was an error loading it.</p>
    </div>
    {% endif %}
    
    <div class="card">
        <h2>Database Schema</h2>
        <pre>{{ db_schema|default('No schema info available') }}</pre>
    </div>
</body>
</html>
"""

ENTRY_LIST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Journal Entries</title>
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
        .error { color: #cf6679; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Journal Entries</h1>
    <p>
        <a href="/emergency/dashboard" class="button">Return to Dashboard</a>
        <a href="/emergency/logout" class="button">Logout</a>
    </p>
    
    {% if error %}
    <div class="card">
        <h2 class="error">Error</h2>
        <p>{{ error }}</p>
    </div>
    {% endif %}
    
    <div class="card">
        <h2>All Journal Entries</h2>
        {% if entries %}
            {% for entry in entries %}
                <div class="journal-entry">
                    <h3><a href="/emergency/entry/{{ entry.id }}">{{ entry.title }}</a></h3>
                    <div class="date">{{ entry.created_at }}</div>
                    {% if entry.has_reflection %}
                    <div>Reflection: Yes</div>
                    {% else %}
                    <div>Reflection: No</div>
                    {% endif %}
                </div>
            {% endfor %}
        {% else %}
            <p>No journal entries found for this user.</p>
        {% endif %}
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

def html_from_newlines(text):
    """Convert newlines to HTML paragraph breaks."""
    if not text:
        return ""
    paragraphs = text.split('\n\n')
    result = ""
    for p in paragraphs:
        p_with_breaks = p.replace('\n', '<br>')
        result += f'<p>{p_with_breaks}</p>'
    return result

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "emergency_secret_key"

# Routes
@app.route('/')
def index():
    """Redirect to the emergency login page."""
    return redirect('/emergency/login')

@app.route('/emergency/login')
def emergency_login():
    """Display the emergency login page."""
    users = []
    error = request.args.get('error')
    message = request.args.get('message')
    
    # Get users from the database
    conn = get_db_connection()
    if conn:
        try:
            result = conn.execute(text("SELECT id, email FROM \"user\" ORDER BY id LIMIT 15"))
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

@app.route('/emergency/login/<int:user_id>')
def emergency_login_user(user_id):
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
                return redirect('/emergency/dashboard')
            else:
                return redirect('/emergency/login?error=User+not+found')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return redirect(f'/emergency/login?error={str(e)}')
        finally:
            conn.close()
    else:
        return redirect('/emergency/login?error=Database+connection+failed')

@app.route('/emergency/dashboard')
def emergency_dashboard():
    """Display the emergency dashboard."""
    # Check if user is logged in
    if not session.get('is_authenticated'):
        return redirect('/emergency/login?error=Not+logged+in')
    
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
                SELECT id, title, created_at, user_reflection IS NOT NULL as has_reflection 
                FROM journal_entry 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC 
                LIMIT 5
            """), {"user_id": user['id']})
            
            for row in result:
                entries.append({
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2],
                    "has_reflection": row[3]
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

@app.route('/emergency/logout')
def emergency_logout():
    """Logout user by clearing session."""
    session.clear()
    return redirect('/emergency/login?message=Successfully+logged+out')

@app.route('/emergency/entries')
def emergency_entries():
    """Display all journal entries for the user."""
    # Check if user is logged in
    if not session.get('is_authenticated'):
        return redirect('/emergency/login?error=Not+logged+in')
    
    user_id = session.get('user_id')
    entries = []
    error = None
    
    # Get all entries
    conn = get_db_connection()
    if conn:
        try:
            result = conn.execute(text("""
                SELECT id, title, created_at, user_reflection IS NOT NULL as has_reflection
                FROM journal_entry 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC
            """), {"user_id": user_id})
            
            for row in result:
                entries.append({
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2],
                    "has_reflection": row[3]
                })
        except Exception as e:
            logger.error(f"Error fetching all entries: {str(e)}")
            error = f"Database error: {str(e)}"
        finally:
            conn.close()
    else:
        error = "Could not connect to database."
    
    return render_template_string(
        ENTRY_LIST_TEMPLATE,
        entries=entries,
        error=error
    )

@app.route('/emergency/entry/<int:entry_id>')
def emergency_entry(entry_id):
    """View a specific journal entry."""
    # Check if user is logged in
    if not session.get('is_authenticated'):
        return redirect('/emergency/login?error=Not+logged+in')
    
    user_id = session.get('user_id')
    entry = None
    error = None
    has_user_reflection = False
    
    # Get the entry
    conn = get_db_connection()
    if conn:
        try:
            # First check if the journal_entry table has user_reflection column
            schema_result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'journal_entry' AND column_name = 'user_reflection'
            """))
            
            for row in schema_result:
                has_user_reflection = True
                break
            
            # Get the entry with or without user_reflection based on schema
            if has_user_reflection:
                query = """
                    SELECT id, title, content, created_at, 
                           analysis_text, analysis_html, user_reflection
                    FROM journal_entry 
                    WHERE id = :entry_id AND user_id = :user_id
                """
            else:
                query = """
                    SELECT id, title, content, created_at, 
                           analysis_text, analysis_html
                    FROM journal_entry 
                    WHERE id = :entry_id AND user_id = :user_id
                """
            
            result = conn.execute(text(query), {
                "entry_id": entry_id,
                "user_id": user_id
            })
            
            for row in result:
                entry = {
                    "id": row[0],
                    "title": row[1],
                    "content": html_from_newlines(row[2]),
                    "created_at": row[3],
                    "analysis_text": row[4],
                    "analysis_html": row[5]
                }
                if has_user_reflection:
                    entry["user_reflection"] = row[6]
                break
            
            if not entry:
                error = "Entry not found or you don't have permission to view it."
        except Exception as e:
            logger.error(f"Error fetching entry: {str(e)}")
            error = f"Database error: {str(e)}"
        finally:
            conn.close()
    else:
        error = "Could not connect to database."
    
    return render_template_string(
        ENTRY_TEMPLATE,
        entry=entry,
        error=error,
        has_user_reflection=has_user_reflection
    )

@app.route('/emergency/save-reflection/<int:entry_id>', methods=['POST'])
def emergency_save_reflection(entry_id):
    """Save a reflection for an entry."""
    # Check if user is logged in
    if not session.get('is_authenticated'):
        return redirect('/emergency/login?error=Not+logged+in')
    
    user_id = session.get('user_id')
    reflection = request.form.get('reflection', '').strip()
    
    if not reflection:
        return redirect(f'/emergency/entry/{entry_id}?error=Reflection+cannot+be+empty')
    
    # Save the reflection
    conn = get_db_connection()
    if conn:
        try:
            # First verify the entry belongs to this user
            check_query = """
                SELECT id FROM journal_entry 
                WHERE id = :entry_id AND user_id = :user_id
            """
            check_result = conn.execute(text(check_query), {
                "entry_id": entry_id,
                "user_id": user_id
            })
            
            valid_entry = False
            for row in check_result:
                valid_entry = True
                break
            
            if not valid_entry:
                return redirect(f'/emergency/entry/{entry_id}?error=Entry+not+found+or+access+denied')
            
            # Update the reflection
            update_query = """
                UPDATE journal_entry 
                SET user_reflection = :reflection,
                    updated_at = NOW()
                WHERE id = :entry_id AND user_id = :user_id
            """
            
            conn.execute(text(update_query), {
                "reflection": reflection,
                "entry_id": entry_id,
                "user_id": user_id
            })
            
            return redirect(f'/emergency/entry/{entry_id}?success=Reflection+saved+successfully')
        except Exception as e:
            logger.error(f"Error saving reflection: {str(e)}")
            return redirect(f'/emergency/entry/{entry_id}?error=Error+saving+reflection:+{str(e)}')
        finally:
            conn.close()
    else:
        return redirect(f'/emergency/entry/{entry_id}?error=Could+not+connect+to+database')

@app.route('/emergency/reflection-test')
def emergency_reflection_test():
    """Test the reflection feature."""
    # Check if user is logged in
    if not session.get('is_authenticated'):
        return redirect('/emergency/login?error=Not+logged+in')
    
    user_id = session.get('user_id')
    entry_id = request.args.get('entry_id')
    error = request.args.get('error')
    success = request.args.get('success')
    entry = None
    db_schema = None
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        return render_template_string(
            REFLECTION_TEST_TEMPLATE,
            error="Could not connect to database."
        )
    
    try:
        # Check if journal_entry table has user_reflection column
        schema_result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'journal_entry'
            ORDER BY ordinal_position
        """))
        
        columns = []
        has_user_reflection = False
        for row in schema_result:
            columns.append(f"{row[0]} ({row[1]})")
            if row[0] == 'user_reflection':
                has_user_reflection = True
        
        db_schema = "Journal Entry Table Columns:\n" + "\n".join(columns)
        
        if not has_user_reflection:
            db_schema += "\n\nWARNING: user_reflection column missing!"
        else:
            db_schema += "\n\nColumn user_reflection exists! ✓"
        
        # Get specific entry or latest entry
        query = """
            SELECT id, title, content, created_at, 
                   analysis_text, analysis_html
        """
        
        if has_user_reflection:
            query += ", user_reflection"
            
        query += """
            FROM journal_entry 
            WHERE user_id = :user_id
        """
        
        params = {"user_id": user_id}
        
        if entry_id:
            query += " AND id = :entry_id"
            params["entry_id"] = entry_id
        
        query += " ORDER BY created_at DESC LIMIT 1"
        
        result = conn.execute(text(query), params)
        
        for row in result:
            entry = {
                "id": row[0],
                "title": row[1],
                "content": html_from_newlines(row[2]),
                "created_at": row[3],
                "analysis_text": row[4],
                "analysis_html": row[5]
            }
            if has_user_reflection:
                entry["user_reflection"] = row[6]
            break
            
        if not entry:
            error = f"No journal entry found for user {user_id}"
    except Exception as e:
        logger.error(f"Error in reflection test: {str(e)}")
        error = f"Database error: {str(e)}"
    finally:
        conn.close()
    
    return render_template_string(
        REFLECTION_TEST_TEMPLATE,
        entry=entry,
        error=error,
        success=success,
        db_schema=db_schema
    )

if __name__ == '__main__':
    # Run the app
    app.run(host='0.0.0.0', port=5001, debug=True)
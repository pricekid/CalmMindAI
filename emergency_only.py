"""
A completely standalone emergency script that runs independently of the main application.
Run with: python emergency_only.py
"""
import os
import logging
from flask import Flask, request, redirect, render_template_string, session
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = "emergency_secret_key"

# Templates
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Emergency Access</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2 { color: #bb86fc; }
        a.button { 
            display: inline-block; 
            background: #bb86fc; 
            color: #121212; 
            padding: 10px 15px; 
            border-radius: 4px; 
            font-weight: bold;
            text-decoration: none;
            margin: 5px;
        }
        a.button:hover { background: #a370e3; }
        .error { color: #cf6679; font-weight: bold; }
        .success { color: #03dac6; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Emergency Access</h1>
    
    <div class="card">
        <h2>Login Directory</h2>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
        
        {% if message %}
        <p class="success">{{ message }}</p>
        {% endif %}
        
        {% if users %}
            {% for user in users %}
            <a href="/login/{{ user.id }}" class="button">{{ user.email }}</a>
            {% endfor %}
        {% else %}
            <p>No users found. Database connection error.</p>
        {% endif %}
    </div>
    
    <div class="card">
        <h2>What's Happening?</h2>
        <p>The main application is experiencing login issues. This is an emergency access page.</p>
    </div>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Emergency Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2, h3 { color: #bb86fc; }
        a.button { 
            display: inline-block; 
            background: #bb86fc; 
            color: #121212; 
            padding: 10px 15px; 
            border-radius: 4px; 
            font-weight: bold;
            text-decoration: none;
            margin: 5px;
        }
        a.button:hover { background: #a370e3; }
        .entry { 
            border-left: 4px solid #03dac6; 
            padding-left: 15px; 
            margin-bottom: 15px;
        }
        .date { color: #78909c; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>Emergency Dashboard</h1>
    
    <div class="card">
        <p>Logged in as: <strong>{{ user.email }}</strong> (ID: {{ user.id }})</p>
        <a href="/logout" class="button">Logout</a>
        <a href="/entries" class="button">View All Journal Entries</a>
        <a href="/test-reflection" class="button">Test Reflection Feature</a>
    </div>
    
    <div class="card">
        <h2>Recent Journal Entries</h2>
        {% if entries %}
            {% for entry in entries %}
            <div class="entry">
                <h3><a href="/entry/{{ entry.id }}">{{ entry.title }}</a></h3>
                <p class="date">{{ entry.created_at }}</p>
                {% if entry.has_reflection %}
                <p><strong>Has reflection: Yes</strong></p>
                {% else %}
                <p><strong>Has reflection: No</strong></p>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <p>No entries found.</p>
        {% endif %}
    </div>
</body>
</html>
"""

ENTRIES_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>All Journal Entries</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2, h3 { color: #bb86fc; }
        a.button { 
            display: inline-block; 
            background: #bb86fc; 
            color: #121212; 
            padding: 10px 15px; 
            border-radius: 4px; 
            font-weight: bold;
            text-decoration: none;
            margin: 5px;
        }
        a.button:hover { background: #a370e3; }
        .entry { 
            border-left: 4px solid #03dac6; 
            padding-left: 15px; 
            margin-bottom: 15px;
        }
        .date { color: #78909c; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>All Journal Entries</h1>
    
    <div>
        <a href="/dashboard" class="button">Back to Dashboard</a>
        <a href="/logout" class="button">Logout</a>
    </div>
    
    <div class="card">
        <h2>Journal Entries</h2>
        {% if entries %}
            {% for entry in entries %}
            <div class="entry">
                <h3><a href="/entry/{{ entry.id }}">{{ entry.title }}</a></h3>
                <p class="date">{{ entry.created_at }}</p>
                {% if entry.has_reflection %}
                <p><strong>Has reflection: Yes</strong></p>
                {% else %}
                <p><strong>Has reflection: No</strong></p>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <p>No entries found.</p>
        {% endif %}
    </div>
</body>
</html>
"""

ENTRY_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Journal Entry</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2, h3 { color: #bb86fc; }
        a.button { 
            display: inline-block; 
            background: #bb86fc; 
            color: #121212; 
            padding: 10px 15px; 
            border-radius: 4px; 
            font-weight: bold;
            text-decoration: none;
            margin: 5px;
        }
        a.button:hover { background: #a370e3; }
        .entry-content { 
            border-left: 4px solid #03dac6; 
            padding-left: 15px; 
            margin: 15px 0;
        }
        .insight {
            border-left: 4px solid #bb86fc;
            padding-left: 15px;
            margin: 15px 0;
            background: #2d2d2d;
            padding: 15px;
            border-radius: 0 8px 8px 0;
        }
        .reflection {
            border-left: 4px solid #03dac6;
            padding-left: 15px;
            margin: 15px 0;
            background: #2d2d2d;
            padding: 15px;
            border-radius: 0 8px 8px 0;
        }
        .date { color: #78909c; font-size: 0.9em; }
        form { margin: 20px 0; }
        textarea {
            width: 100%;
            min-height: 120px;
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #444;
            padding: 10px;
            border-radius: 4px;
            font-family: inherit;
        }
        input[type="submit"] {
            background: #03dac6;
            color: #121212;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
        }
        input[type="submit"]:hover {
            background: #00b8a5;
        }
        .error { color: #cf6679; font-weight: bold; }
        .success { color: #03dac6; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Journal Entry</h1>
    
    <div>
        <a href="/dashboard" class="button">Back to Dashboard</a>
        <a href="/entries" class="button">All Entries</a>
        <a href="/logout" class="button">Logout</a>
    </div>
    
    {% if error %}
    <div class="card">
        <p class="error">{{ error }}</p>
    </div>
    {% endif %}
    
    {% if success %}
    <div class="card">
        <p class="success">{{ success }}</p>
    </div>
    {% endif %}
    
    {% if entry %}
    <div class="card">
        <h2>{{ entry.title }}</h2>
        <p class="date">{{ entry.created_at }}</p>
        
        <div class="entry-content">
            {{ entry.content|safe }}
        </div>
        
        {% if entry.analysis_html %}
        <h3>Mira's Insight</h3>
        <div class="insight">
            {{ entry.analysis_html|safe }}
        </div>
        {% endif %}
        
        {% if entry.user_reflection %}
        <h3>Your Reflection</h3>
        <div class="reflection">
            {{ entry.user_reflection }}
        </div>
        
        <form method="POST" action="/save-reflection/{{ entry.id }}">
            <h3>Update Your Reflection</h3>
            <textarea name="reflection">{{ entry.user_reflection }}</textarea>
            <div><input type="submit" value="Update Reflection"></div>
        </form>
        {% else %}
        <form method="POST" action="/save-reflection/{{ entry.id }}">
            <h3>Add Your Reflection</h3>
            <p>Take a moment to reflect on Mira's insight. What resonates with you?</p>
            <textarea name="reflection" placeholder="Your thoughts..."></textarea>
            <div><input type="submit" value="Save Reflection"></div>
        </form>
        {% endif %}
    </div>
    {% else %}
    <div class="card">
        <p>Entry not found or access denied.</p>
    </div>
    {% endif %}
    
    <div class="card">
        <h3>Database Information</h3>
        <p>User reflection column exists: {{ has_reflection_column and "Yes" or "No" }}</p>
    </div>
</body>
</html>
"""

TEST_REFLECTION_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Reflection Feature</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2, h3 { color: #bb86fc; }
        a.button { 
            display: inline-block; 
            background: #bb86fc; 
            color: #121212; 
            padding: 10px 15px; 
            border-radius: 4px; 
            font-weight: bold;
            text-decoration: none;
            margin: 5px;
        }
        a.button:hover { background: #a370e3; }
        pre { 
            background: #2d2d2d; 
            padding: 15px; 
            border-radius: 4px; 
            overflow-x: auto;
            font-family: monospace;
        }
        .insight {
            border-left: 4px solid #bb86fc;
            padding-left: 15px;
            margin: 15px 0;
            background: #2d2d2d;
            padding: 15px;
            border-radius: 0 8px 8px 0;
        }
        .reflection {
            border-left: 4px solid #03dac6;
            padding-left: 15px;
            margin: 15px 0;
            background: #2d2d2d;
            padding: 15px;
            border-radius: 0 8px 8px 0;
        }
        .error { color: #cf6679; font-weight: bold; }
        .success { color: #03dac6; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Test Reflection Feature</h1>
    
    <div>
        <a href="/dashboard" class="button">Back to Dashboard</a>
        <a href="/logout" class="button">Logout</a>
    </div>
    
    {% if error %}
    <div class="card">
        <p class="error">{{ error }}</p>
    </div>
    {% endif %}
    
    {% if success %}
    <div class="card">
        <p class="success">{{ success }}</p>
    </div>
    {% endif %}
    
    <div class="card">
        <h2>Database Schema</h2>
        <pre>{{ schema_info }}</pre>
    </div>
    
    {% if latest_entry %}
    <div class="card">
        <h2>Latest Journal Entry</h2>
        <h3>{{ latest_entry.title }}</h3>
        
        {% if latest_entry.analysis_html %}
        <h3>Mira's Insight</h3>
        <div class="insight">
            {{ latest_entry.analysis_html|safe }}
        </div>
        {% endif %}
        
        {% if latest_entry.user_reflection %}
        <h3>User Reflection</h3>
        <div class="reflection">
            {{ latest_entry.user_reflection }}
        </div>
        {% else %}
        <p>No reflection added yet. <a href="/entry/{{ latest_entry.id }}">Add one here</a>.</p>
        {% endif %}
    </div>
    {% endif %}
    
    <div class="card">
        <h2>Testing Instructions</h2>
        <p>1. Go to a journal entry by clicking on one from the dashboard</p>
        <p>2. Add a reflection in the form at the bottom</p>
        <p>3. Submit to test if reflections can be saved</p>
        <p>4. Return to the entry to verify if the reflection was saved correctly</p>
    </div>
</body>
</html>
"""

# Helper functions
def get_db_connection():
    """Create a database connection using the environment variable."""
    try:
        connection_string = os.environ.get('DATABASE_URL')
        engine = create_engine(connection_string)
        return engine.connect()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def format_content(text):
    """Format text content with HTML paragraphs."""
    if not text:
        return ""
    paragraphs = text.split('\n\n')
    result = ""
    for p in paragraphs:
        p_with_breaks = p.replace('\n', '<br>')
        result += f'<p>{p_with_breaks}</p>'
    return result

def has_user_reflection_column():
    """Check if the user_reflection column exists in the journal_entry table."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'journal_entry' AND column_name = 'user_reflection'
        """))
        
        for row in result:
            conn.close()
            return True
        
        conn.close()
        return False
    except Exception as e:
        logger.error(f"Error checking for user_reflection column: {e}")
        if conn:
            conn.close()
        return False

# Routes
@app.route('/')
def index():
    """Redirect to login."""
    return redirect('/login')

@app.route('/login')
def login():
    """Show login page with list of users."""
    error = request.args.get('error')
    message = request.args.get('message')
    users = []
    
    conn = get_db_connection()
    if conn:
        try:
            result = conn.execute(text("SELECT id, email FROM \"user\" ORDER BY id LIMIT 20"))
            for row in result:
                users.append({
                    "id": row[0],
                    "email": row[1]
                })
        except Exception as e:
            error = f"Database error: {e}"
        finally:
            conn.close()
    else:
        error = "Could not connect to database"
    
    return render_template_string(
        LOGIN_PAGE,
        users=users,
        error=error,
        message=message
    )

@app.route('/login/<int:user_id>')
def login_user(user_id):
    """Log in as a specific user."""
    conn = get_db_connection()
    if not conn:
        return redirect('/login?error=Database+connection+failed')
    
    try:
        result = conn.execute(text("SELECT id, email FROM \"user\" WHERE id = :id"), {"id": user_id})
        user = None
        for row in result:
            user = {
                "id": row[0],
                "email": row[1]
            }
            break
        
        if not user:
            return redirect('/login?error=User+not+found')
        
        # Save user info in session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['is_authenticated'] = True
        
        return redirect('/dashboard')
    except Exception as e:
        return redirect(f'/login?error=Login+error:+{e}')
    finally:
        conn.close()

@app.route('/logout')
def logout():
    """Log out the current user."""
    session.clear()
    return redirect('/login?message=Successfully+logged+out')

@app.route('/dashboard')
def dashboard():
    """Show user dashboard."""
    if not session.get('is_authenticated'):
        return redirect('/login?error=Not+logged+in')
    
    user = {
        "id": session.get('user_id'),
        "email": session.get('user_email')
    }
    
    # Get recent entries
    entries = []
    conn = get_db_connection()
    if conn:
        try:
            # Try to include user_reflection status if the column exists
            has_reflection = has_user_reflection_column()
            
            if has_reflection:
                query = """
                    SELECT id, title, created_at, user_reflection IS NOT NULL as has_reflection
                    FROM journal_entry
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 5
                """
            else:
                query = """
                    SELECT id, title, created_at, FALSE as has_reflection
                    FROM journal_entry
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 5
                """
            
            result = conn.execute(text(query), {"user_id": user["id"]})
            
            for row in result:
                entries.append({
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2],
                    "has_reflection": row[3]
                })
        except Exception as e:
            logger.error(f"Error fetching entries: {e}")
        finally:
            conn.close()
    
    return render_template_string(
        DASHBOARD_PAGE,
        user=user,
        entries=entries
    )

@app.route('/entries')
def entries():
    """Show all journal entries."""
    if not session.get('is_authenticated'):
        return redirect('/login?error=Not+logged+in')
    
    user_id = session.get('user_id')
    entries = []
    
    conn = get_db_connection()
    if conn:
        try:
            # Try to include user_reflection status if the column exists
            has_reflection = has_user_reflection_column()
            
            if has_reflection:
                query = """
                    SELECT id, title, created_at, user_reflection IS NOT NULL as has_reflection
                    FROM journal_entry
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """
            else:
                query = """
                    SELECT id, title, created_at, FALSE as has_reflection
                    FROM journal_entry
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """
            
            result = conn.execute(text(query), {"user_id": user_id})
            
            for row in result:
                entries.append({
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2],
                    "has_reflection": row[3]
                })
        except Exception as e:
            logger.error(f"Error fetching all entries: {e}")
        finally:
            conn.close()
    
    return render_template_string(
        ENTRIES_PAGE,
        entries=entries
    )

@app.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    """View a specific journal entry."""
    if not session.get('is_authenticated'):
        return redirect('/login?error=Not+logged+in')
    
    user_id = session.get('user_id')
    error = request.args.get('error')
    success = request.args.get('success')
    
    conn = get_db_connection()
    if not conn:
        return render_template_string(
            ENTRY_PAGE,
            error="Database connection failed",
            has_reflection_column=False
        )
    
    try:
        # Check if user_reflection column exists
        has_reflection = has_user_reflection_column()
        
        # Get the entry with appropriate columns
        if has_reflection:
            query = """
                SELECT id, title, content, created_at, analysis_html, user_reflection
                FROM journal_entry
                WHERE id = :entry_id AND user_id = :user_id
            """
        else:
            query = """
                SELECT id, title, content, created_at, analysis_html
                FROM journal_entry
                WHERE id = :entry_id AND user_id = :user_id
            """
        
        result = conn.execute(text(query), {
            "entry_id": entry_id,
            "user_id": user_id
        })
        
        entry = None
        for row in result:
            if has_reflection:
                entry = {
                    "id": row[0],
                    "title": row[1],
                    "content": format_content(row[2]),
                    "created_at": row[3],
                    "analysis_html": row[4],
                    "user_reflection": row[5]
                }
            else:
                entry = {
                    "id": row[0],
                    "title": row[1],
                    "content": format_content(row[2]),
                    "created_at": row[3],
                    "analysis_html": row[4]
                }
            break
        
        if not entry:
            return render_template_string(
                ENTRY_PAGE,
                error="Entry not found or access denied",
                has_reflection_column=has_reflection
            )
        
        return render_template_string(
            ENTRY_PAGE,
            entry=entry,
            error=error,
            success=success,
            has_reflection_column=has_reflection
        )
    except Exception as e:
        logger.error(f"Error viewing entry: {e}")
        return render_template_string(
            ENTRY_PAGE,
            error=f"Error: {e}",
            has_reflection_column=False
        )
    finally:
        conn.close()

@app.route('/save-reflection/<int:entry_id>', methods=['POST'])
def save_reflection(entry_id):
    """Save a reflection for an entry."""
    if not session.get('is_authenticated'):
        return redirect('/login?error=Not+logged+in')
    
    user_id = session.get('user_id')
    reflection = request.form.get('reflection', '').strip()
    
    if not reflection:
        return redirect(f'/entry/{entry_id}?error=Reflection+cannot+be+empty')
    
    # Check if user_reflection column exists
    if not has_user_reflection_column():
        return redirect(f'/entry/{entry_id}?error=User+reflection+column+does+not+exist')
    
    conn = get_db_connection()
    if not conn:
        return redirect(f'/entry/{entry_id}?error=Database+connection+failed')
    
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
        
        entry_exists = False
        for row in check_result:
            entry_exists = True
            break
        
        if not entry_exists:
            return redirect(f'/entry/{entry_id}?error=Entry+not+found+or+access+denied')
        
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
        
        return redirect(f'/entry/{entry_id}?success=Reflection+saved+successfully')
    except Exception as e:
        logger.error(f"Error saving reflection: {e}")
        return redirect(f'/entry/{entry_id}?error=Error+saving+reflection:+{e}')
    finally:
        conn.close()

@app.route('/test-reflection')
def test_reflection():
    """Test the reflection feature."""
    if not session.get('is_authenticated'):
        return redirect('/login?error=Not+logged+in')
    
    user_id = session.get('user_id')
    
    # Get database schema information
    schema_info = "Checking database schema...\n"
    conn = get_db_connection()
    if not conn:
        return render_template_string(
            TEST_REFLECTION_PAGE,
            error="Database connection failed",
            schema_info="Could not connect to database"
        )
    
    try:
        # Check if user_reflection column exists
        schema_result = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'journal_entry'
            ORDER BY ordinal_position
        """))
        
        columns = []
        has_reflection = False
        for row in schema_result:
            columns.append(f"{row[0]} ({row[1]})")
            if row[0] == 'user_reflection':
                has_reflection = True
        
        schema_info += "Journal Entry Table Columns:\n" + "\n".join(columns)
        
        if has_reflection:
            schema_info += "\n\nuser_reflection column exists ✓"
        else:
            schema_info += "\n\nWARNING: user_reflection column does not exist!"
        
        # Get latest entry with reflection if available
        latest_entry = None
        if has_reflection:
            entry_result = conn.execute(text("""
                SELECT id, title, analysis_html, user_reflection
                FROM journal_entry
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """), {"user_id": user_id})
        else:
            entry_result = conn.execute(text("""
                SELECT id, title, analysis_html
                FROM journal_entry
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """), {"user_id": user_id})
        
        for row in entry_result:
            if has_reflection:
                latest_entry = {
                    "id": row[0],
                    "title": row[1],
                    "analysis_html": row[2],
                    "user_reflection": row[3]
                }
            else:
                latest_entry = {
                    "id": row[0],
                    "title": row[1],
                    "analysis_html": row[2]
                }
            break
        
        return render_template_string(
            TEST_REFLECTION_PAGE,
            schema_info=schema_info,
            latest_entry=latest_entry
        )
    except Exception as e:
        logger.error(f"Error in test reflection: {e}")
        return render_template_string(
            TEST_REFLECTION_PAGE,
            error=f"Error: {e}",
            schema_info=f"Error getting schema: {e}"
        )
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
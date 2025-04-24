"""
Standalone test page for directly testing the reflective pause feature.
This page allows viewing and testing a single journal entry's reflection without any other dependencies.
"""
import os
import logging
from flask import Blueprint, request, redirect, render_template_string, session, jsonify, flash
from sqlalchemy import create_engine, text
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
reflection_test_bp = Blueprint('reflection_test', __name__)

# HTML template for testing the reflection feature
REFLECTION_TEMPLATE = """
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
    </style>
</head>
<body>
    <h1>Test Reflection Feature</h1>
    <p>
        <a href="/special-dashboard" class="button">Return to Dashboard</a>
        <a href="/special-logout" class="button">Logout</a>
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
            <p>{{ entry.content }}</p>
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
        <form method="POST" action="/save-reflection/{{ entry.id }}">
            <h3>Add Your Reflection</h3>
            <p>Take a moment to reflect on Mira's insight. What resonates with you?</p>
            <textarea name="reflection" class="textarea" placeholder="Share your thoughts..."></textarea>
            <input type="submit" value="Save Reflection">
        </form>
        {% else %}
        <form method="POST" action="/save-reflection/{{ entry.id }}">
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
        <h2>Direct Database Query</h2>
        <p>Database schema report:</p>
        <pre>{{ db_schema|default('No schema info available') }}</pre>
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
    """Convert newlines to HTML breaks."""
    if not text:
        return ""
    return text.replace('\n', '<br>')

# Routes
@reflection_test_bp.route('/test-reflection')
def test_reflection():
    """Display a test page for the reflection feature."""
    entry_id = request.args.get('entry_id')
    error = None
    success = None
    entry = None
    db_schema = None
    
    # Check if user is logged in (via any method)
    user_id = session.get('user_id')
    if not user_id:
        error = "Not logged in. Please login first."
        return render_template_string(
            REFLECTION_TEMPLATE,
            error=error
        )
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        error = "Could not connect to database."
        return render_template_string(
            REFLECTION_TEMPLATE,
            error=error
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
                   analysis_text, analysis_html, user_reflection
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
                "analysis_html": row[5],
                "user_reflection": row[6]
            }
            break
            
        if not entry:
            error = f"No journal entry found for user {user_id}"
    except Exception as e:
        logger.error(f"Error in test_reflection: {str(e)}")
        error = f"Database error: {str(e)}"
    finally:
        conn.close()
    
    return render_template_string(
        REFLECTION_TEMPLATE,
        entry=entry,
        error=error,
        success=success,
        db_schema=db_schema
    )

@reflection_test_bp.route('/save-reflection/<int:entry_id>', methods=['POST'])
def save_reflection(entry_id):
    """Save a reflection for an entry."""
    reflection = request.form.get('reflection', '').strip()
    error = None
    success = None
    
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/test-reflection?error=Not+logged+in')
    
    if not reflection:
        return redirect(f'/test-reflection?entry_id={entry_id}&error=Reflection+cannot+be+empty')
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        return redirect(f'/test-reflection?entry_id={entry_id}&error=Could+not+connect+to+database')
    
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
            return redirect(f'/test-reflection?error=Entry+not+found+or+access+denied')
        
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
        
        success = "Reflection saved successfully!"
        
    except Exception as e:
        logger.error(f"Error saving reflection: {str(e)}")
        error = f"Error saving reflection: {str(e)}"
    finally:
        conn.close()
    
    if error:
        return redirect(f'/test-reflection?entry_id={entry_id}&error={error}')
    else:
        return redirect(f'/test-reflection?entry_id={entry_id}&success={success}')
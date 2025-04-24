"""
A very simple test script to view a journal entry with its user reflection directly from the database.
This bypasses all of the complex Flask routes and templates to directly check if the data is correctly stored.
"""
import os
import logging
from flask import Blueprint, render_template_string, request
from app import db
from models import JournalEntry, User

# Set up logging
logger = logging.getLogger(__name__)
test_reflection_bp = Blueprint('test_reflection', __name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Journal Entry Test</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        h1, h2, h3 { color: #bb86fc; }
        .reflection { background: #263238; border-left: 4px solid #bb86fc; padding: 15px; margin: 20px 0; }
        .content { white-space: pre-line; }
        .meta { color: #78909c; font-size: 0.9em; margin-bottom: 15px; }
        .error { color: #cf6679; font-weight: bold; }
        .success { color: #03dac6; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Journal Entry Test</h1>
    
    <div class="card">
        <h2>Data Verification</h2>
        
        <form method="GET" action="">
            <label for="entry_id">Journal Entry ID:</label>
            <input type="number" name="entry_id" id="entry_id" value="{{ entry_id or '' }}">
            <button type="submit">View Entry</button>
        </form>
    </div>
    
    {% if error %}
    <div class="card">
        <h3 class="error">Error</h3>
        <p>{{ error }}</p>
    </div>
    {% endif %}
    
    {% if entry %}
    <div class="card">
        <h3>Journal Entry #{{ entry.id }}</h3>
        <div class="meta">
            Created: {{ entry.created_at.strftime('%Y-%m-%d %H:%M') if entry.created_at else 'Unknown' }}<br>
            By User: {{ user_email or 'Unknown' }} (ID: {{ entry.user_id }})
        </div>
        
        <h4>{{ entry.title }}</h4>
        <div class="content">{{ entry.content }}</div>
        
        <h3>Data Check</h3>
        <ul>
            <li>Has user_reflection column: <span class="{% if has_reflection_column %}success{% else %}error{% endif %}">{{ has_reflection_column }}</span></li>
            <li>user_reflection value exists: <span class="{% if entry.user_reflection %}success{% else %}error{% endif %}">{{ entry.user_reflection is not none }}</span></li>
        </ul>
        
        {% if entry.user_reflection %}
        <h3>User Reflection</h3>
        <div class="reflection">
            {{ entry.user_reflection }}
        </div>
        {% else %}
        <h3 class="error">No User Reflection Data</h3>
        <p>This entry does not have any user reflection data.</p>
        {% endif %}
    </div>
    {% endif %}
</body>
</html>
"""

@test_reflection_bp.route('/test-reflection')
def test_reflection():
    """Simple test route to view a journal entry with reflection data."""
    entry_id = request.args.get('entry_id', type=int)
    error = None
    entry = None
    user_email = None
    has_reflection_column = True
    
    if entry_id:
        try:
            # Try to directly query the entry with all columns
            entry = db.session.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
            
            if entry:
                # Try to get the user's email
                user = db.session.query(User).filter(User.id == entry.user_id).first()
                if user:
                    user_email = user.email
                    
                # Check if the user_reflection attribute exists
                has_reflection_column = hasattr(entry, 'user_reflection')
                
                logger.info(f"Successfully loaded entry {entry_id} with reflection? {has_reflection_column}")
                if has_reflection_column:
                    logger.info(f"Reflection content: {entry.user_reflection[:50] if entry.user_reflection else 'None'}")
            else:
                error = f"No entry found with ID {entry_id}"
                
        except Exception as e:
            error = f"Error loading entry: {str(e)}"
            logger.error(f"Error in test-reflection route: {str(e)}")
            has_reflection_column = False
    
    return render_template_string(
        TEMPLATE, 
        entry_id=entry_id,
        entry=entry,
        user_email=user_email,
        has_reflection_column=has_reflection_column,
        error=error
    )
"""
Dedicated emergency login system that avoids all problematic code paths.
Run directly with: python emergency_login_main.py
"""

import os
import logging
from flask import Flask, render_template, request, redirect, session, flash, jsonify, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app with minimal configuration
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "emergency_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///calm_journey.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy without any model relationships
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def check_password(self, password):
        if self.password_hash is None or self.password_hash == "":
            return False
        return check_password_hash(self.password_hash, password)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow)
    analysis = db.Column(db.Text)
    reflection = db.Column(db.Text)
    user_reflection = db.Column(db.Text)
    
    user = db.relationship('User', backref=db.backref('journal_entries', lazy=True))

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/emergency/login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Simple emergency routes
@app.route('/emergency')
def emergency_index():
    """Redirect to login."""
    return redirect('/emergency/login')

@app.route('/emergency/login', methods=['GET', 'POST'])
def emergency_login():
    """Emergency login page."""
    if current_user.is_authenticated:
        return redirect('/emergency/dashboard')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect('/emergency/dashboard')
        
        flash('Invalid email or password', 'danger')
    
    # Get all users for direct login in emergency mode
    users = User.query.all()
    return render_template('emergency_login.html', users=users)

@app.route('/emergency/direct_login/<int:user_id>')
def emergency_direct_login(user_id):
    """Direct login with user ID for emergency recovery."""
    user = User.query.get(user_id)
    if user:
        login_user(user)
        flash(f'Emergency login successful as {user.username}', 'success')
        return redirect('/emergency/dashboard')
    
    flash('User not found', 'danger')
    return redirect('/emergency/login')

@app.route('/emergency/dashboard')
@login_required
def emergency_dashboard():
    """Emergency dashboard."""
    # Fetch user's recent journal entries
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).limit(5).all()
    return render_template('emergency_dashboard.html', user=current_user, entries=entries)

@app.route('/emergency/journal')
@login_required
def emergency_journal_list():
    """List all journal entries."""
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).all()
    return render_template('emergency_journal_list.html', entries=entries)

@app.route('/emergency/journal/<int:entry_id>')
@login_required
def emergency_journal_view(entry_id):
    """View a journal entry."""
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Security check - ensure user can only view their own entries
    if entry.user_id != current_user.id:
        flash('You do not have permission to view this entry', 'danger')
        return redirect('/emergency/journal')
    
    return render_template('emergency_journal_view.html', entry=entry)

@app.route('/emergency/journal/<int:entry_id>/reflection', methods=['GET', 'POST'])
@login_required
def emergency_save_reflection(entry_id):
    """Save a user reflection for a journal entry."""
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Security check - ensure user can only modify their own entries
    if entry.user_id != current_user.id:
        flash('You do not have permission to modify this entry', 'danger')
        return redirect('/emergency/journal')
    
    if request.method == 'POST':
        reflection = request.form.get('reflection')
        
        # Update the entry with user's reflection
        entry.user_reflection = reflection
        db.session.commit()
        
        flash('Your reflection has been saved', 'success')
        return redirect(f'/emergency/journal/{entry_id}')
    
    return render_template('emergency_reflection.html', entry=entry)

@app.route('/emergency/logout')
def emergency_logout():
    """Logout user."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect('/emergency/login')

@app.route('/emergency/template/<name>')
def emergency_template(name):
    """Debug endpoint to view a template directly."""
    try:
        return render_template(f'{name}.html')
    except Exception as e:
        return f"Error loading template: {str(e)}"

# Error handlers disabled to prevent interference with main application routing
# @app.errorhandler(404)
def page_not_found_disabled(e):
    return render_template('emergency_error.html', error_title="Page Not Found", 
                          error_message="The page you're looking for doesn't exist."), 404

# @app.errorhandler(500)
def server_error_disabled(e):
    return render_template('emergency_error.html', error_title="Server Error", 
                          error_message="Something went wrong on our end. Please try again later."), 500

# Create necessary emergency templates
@app.route('/emergency/create_templates')
def create_emergency_templates():
    """Create the necessary templates for the emergency system."""
    templates_dir = os.path.join(app.root_path, 'templates')
    created = []
    
    # Ensure templates directory exists
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Create emergency login template
    login_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Login - Calm Journey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; background-color: #1a1a1a; color: #f8f9fa; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
            h1 { color: #0d6efd; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input[type="email"], input[type="password"], input[type="text"] { 
                width: 100%; padding: 8px; border: 1px solid #495057; border-radius: 4px; background-color: #343a40; color: #f8f9fa; 
            }
            .btn { display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 10px; cursor: pointer; }
            .btn-primary { background-color: #0d6efd; color: white; border: none; }
            .btn-light { background-color: #f8f9fa; color: #212529; }
            .alert { padding: 10px; margin-bottom: 15px; border-radius: 4px; }
            .alert-danger { background-color: #dc3545; color: white; }
            .alert-success { background-color: #198754; color: white; }
            .alert-info { background-color: #0dcaf0; color: white; }
            .user-list { margin-top: 30px; }
            .user-list h2 { color: #0dcaf0; }
            .user-item { margin-bottom: 5px; }
            .user-item a { color: #0dcaf0; text-decoration: none; }
            .user-item a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Emergency Login</h1>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" action="/emergency/login">
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary">Login</button>
            </form>
            
            <div class="user-list">
                <h2>Emergency Direct Login</h2>
                <p>For system recovery, you can log in directly without a password:</p>
                {% if users %}
                    {% for user in users %}
                        <div class="user-item">
                            <a href="/emergency/direct_login/{{ user.id }}">{{ user.username }} ({{ user.email }})</a>
                        </div>
                    {% endfor %}
                {% else %}
                    <p>No users found in the system.</p>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create emergency dashboard template
    dashboard_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Dashboard - Calm Journey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; background-color: #1a1a1a; color: #f8f9fa; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
            h1 { color: #0d6efd; }
            h2 { color: #0dcaf0; }
            .nav { margin-bottom: 20px; }
            .nav a { color: #0dcaf0; text-decoration: none; margin-right: 15px; }
            .nav a:hover { text-decoration: underline; }
            .alert { padding: 10px; margin-bottom: 15px; border-radius: 4px; }
            .alert-danger { background-color: #dc3545; color: white; }
            .alert-success { background-color: #198754; color: white; }
            .alert-info { background-color: #0dcaf0; color: white; }
            .journal-entry { margin-bottom: 20px; padding: 15px; background-color: #343a40; border-radius: 4px; }
            .journal-title { font-size: 1.2em; margin-bottom: 5px; color: #0dcaf0; }
            .journal-date { font-size: 0.8em; color: #adb5bd; margin-bottom: 10px; }
            .journal-content { margin-bottom: 10px; }
            .btn { display: inline-block; padding: 6px 12px; text-decoration: none; border-radius: 4px; }
            .btn-primary { background-color: #0d6efd; color: white; }
            .warning-box { background-color: #dc3545; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="warning-box">
                <h3>Emergency Recovery Mode</h3>
                <p>You are in the emergency system. This is a simplified interface for recovery purposes.</p>
            </div>
            
            <div class="nav">
                <a href="/emergency/dashboard">Dashboard</a>
                <a href="/emergency/journal">Journal Entries</a>
                <a href="/emergency/logout">Logout</a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <h1>Emergency Dashboard</h1>
            <p>Welcome, {{ user.username }}!</p>
            
            <h2>Recent Journal Entries</h2>
            {% if entries %}
                {% for entry in entries %}
                    <div class="journal-entry">
                        <div class="journal-title">{{ entry.title }}</div>
                        <div class="journal-date">{{ entry.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
                        <div class="journal-content">{{ entry.content[:150] }}{% if entry.content|length > 150 %}...{% endif %}</div>
                        <a href="/emergency/journal/{{ entry.id }}" class="btn btn-primary">View Full Entry</a>
                    </div>
                {% endfor %}
                <a href="/emergency/journal" class="btn btn-primary">View All Entries</a>
            {% else %}
                <p>No journal entries found.</p>
            {% endif %}
        </div>
    </body>
    </html>
    """
    
    # Create emergency journal list template
    journal_list_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Journal Entries - Calm Journey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; background-color: #1a1a1a; color: #f8f9fa; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
            h1 { color: #0d6efd; }
            .nav { margin-bottom: 20px; }
            .nav a { color: #0dcaf0; text-decoration: none; margin-right: 15px; }
            .nav a:hover { text-decoration: underline; }
            .alert { padding: 10px; margin-bottom: 15px; border-radius: 4px; }
            .alert-danger { background-color: #dc3545; color: white; }
            .alert-success { background-color: #198754; color: white; }
            .alert-info { background-color: #0dcaf0; color: white; }
            .journal-entry { margin-bottom: 20px; padding: 15px; background-color: #343a40; border-radius: 4px; }
            .journal-title { font-size: 1.2em; margin-bottom: 5px; color: #0dcaf0; }
            .journal-date { font-size: 0.8em; color: #adb5bd; margin-bottom: 10px; }
            .journal-content { margin-bottom: 10px; }
            .btn { display: inline-block; padding: 6px 12px; text-decoration: none; border-radius: 4px; }
            .btn-primary { background-color: #0d6efd; color: white; }
            .warning-box { background-color: #dc3545; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="warning-box">
                <h3>Emergency Recovery Mode</h3>
                <p>You are in the emergency system. This is a simplified interface for recovery purposes.</p>
            </div>
            
            <div class="nav">
                <a href="/emergency/dashboard">Dashboard</a>
                <a href="/emergency/journal">Journal Entries</a>
                <a href="/emergency/logout">Logout</a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <h1>Journal Entries</h1>
            
            {% if entries %}
                {% for entry in entries %}
                    <div class="journal-entry">
                        <div class="journal-title">{{ entry.title }}</div>
                        <div class="journal-date">{{ entry.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
                        <div class="journal-content">{{ entry.content[:150] }}{% if entry.content|length > 150 %}...{% endif %}</div>
                        <a href="/emergency/journal/{{ entry.id }}" class="btn btn-primary">View Full Entry</a>
                    </div>
                {% endfor %}
            {% else %}
                <p>No journal entries found.</p>
            {% endif %}
        </div>
    </body>
    </html>
    """
    
    # Create emergency journal view template
    journal_view_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Journal Entry - Calm Journey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; background-color: #1a1a1a; color: #f8f9fa; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
            h1 { color: #0d6efd; }
            h2 { color: #0dcaf0; margin-top: 30px; }
            .nav { margin-bottom: 20px; }
            .nav a { color: #0dcaf0; text-decoration: none; margin-right: 15px; }
            .nav a:hover { text-decoration: underline; }
            .alert { padding: 10px; margin-bottom: 15px; border-radius: 4px; }
            .alert-danger { background-color: #dc3545; color: white; }
            .alert-success { background-color: #198754; color: white; }
            .alert-info { background-color: #0dcaf0; color: white; }
            .journal-date { font-size: 0.8em; color: #adb5bd; margin-bottom: 15px; }
            .journal-section { margin-bottom: 30px; padding: 15px; background-color: #343a40; border-radius: 4px; }
            .btn { display: inline-block; padding: 6px 12px; text-decoration: none; border-radius: 4px; }
            .btn-primary { background-color: #0d6efd; color: white; }
            .btn-secondary { background-color: #6c757d; color: white; }
            .warning-box { background-color: #dc3545; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
            pre { white-space: pre-wrap; font-family: inherit; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="warning-box">
                <h3>Emergency Recovery Mode</h3>
                <p>You are in the emergency system. This is a simplified interface for recovery purposes.</p>
            </div>
            
            <div class="nav">
                <a href="/emergency/dashboard">Dashboard</a>
                <a href="/emergency/journal">Journal Entries</a>
                <a href="/emergency/logout">Logout</a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <h1>{{ entry.title }}</h1>
            <div class="journal-date">{{ entry.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
            
            <div class="journal-section">
                <h2>Your Journal Entry</h2>
                <pre>{{ entry.content }}</pre>
            </div>
            
            {% if entry.analysis %}
            <div class="journal-section">
                <h2>Initial Insight</h2>
                <pre>{{ entry.analysis }}</pre>
            </div>
            {% endif %}
            
            {% if entry.user_reflection %}
            <div class="journal-section">
                <h2>Your Reflection</h2>
                <pre>{{ entry.user_reflection }}</pre>
            </div>
            {% elif entry.analysis %}
            <div class="journal-section">
                <h2>Reflective Pause</h2>
                <p>Take a moment to reflect on the insights above. What resonates with you?</p>
                <a href="/emergency/journal/{{ entry.id }}/reflection" class="btn btn-primary">Add Your Reflection</a>
            </div>
            {% endif %}
            
            {% if entry.reflection and entry.user_reflection %}
            <div class="journal-section">
                <h2>Follow-up Response</h2>
                <pre>{{ entry.reflection }}</pre>
            </div>
            {% endif %}
            
            <a href="/emergency/journal" class="btn btn-secondary">Back to Journal Entries</a>
        </div>
    </body>
    </html>
    """
    
    # Create emergency reflection template
    reflection_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Reflection - Calm Journey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; background-color: #1a1a1a; color: #f8f9fa; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
            h1 { color: #0d6efd; }
            h2 { color: #0dcaf0; margin-top: 30px; }
            .nav { margin-bottom: 20px; }
            .nav a { color: #0dcaf0; text-decoration: none; margin-right: 15px; }
            .nav a:hover { text-decoration: underline; }
            .alert { padding: 10px; margin-bottom: 15px; border-radius: 4px; }
            .alert-danger { background-color: #dc3545; color: white; }
            .alert-success { background-color: #198754; color: white; }
            .alert-info { background-color: #0dcaf0; color: white; }
            .journal-section { margin-bottom: 30px; padding: 15px; background-color: #343a40; border-radius: 4px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            textarea { 
                width: 100%; height: 150px; padding: 8px; border: 1px solid #495057; 
                border-radius: 4px; background-color: #343a40; color: #f8f9fa; 
                resize: vertical;
            }
            .btn { display: inline-block; padding: 6px 12px; text-decoration: none; border-radius: 4px; cursor: pointer; }
            .btn-primary { background-color: #0d6efd; color: white; border: none; }
            .btn-secondary { background-color: #6c757d; color: white; }
            .warning-box { background-color: #dc3545; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
            pre { white-space: pre-wrap; font-family: inherit; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="warning-box">
                <h3>Emergency Recovery Mode</h3>
                <p>You are in the emergency system. This is a simplified interface for recovery purposes.</p>
            </div>
            
            <div class="nav">
                <a href="/emergency/dashboard">Dashboard</a>
                <a href="/emergency/journal">Journal Entries</a>
                <a href="/emergency/logout">Logout</a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <h1>Add Your Reflection</h1>
            
            <div class="journal-section">
                <h2>Initial Insight</h2>
                <pre>{{ entry.analysis }}</pre>
            </div>
            
            <form method="POST" action="/emergency/journal/{{ entry.id }}/reflection">
                <div class="form-group">
                    <label for="reflection">Your Reflection:</label>
                    <textarea id="reflection" name="reflection" required placeholder="Share your thoughts on how these insights resonate with you..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Save Reflection</button>
                <a href="/emergency/journal/{{ entry.id }}" class="btn btn-secondary">Cancel</a>
            </form>
        </div>
    </body>
    </html>
    """
    
    # Create emergency error template
    error_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error - Calm Journey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; background-color: #1a1a1a; color: #f8f9fa; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
            h1 { color: #dc3545; }
            .btn { display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
            .btn-primary { background-color: #0d6efd; color: white; }
            .btn-light { background-color: #f8f9fa; color: #212529; }
            .warning-box { background-color: #dc3545; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="warning-box">
                <h3>Emergency Recovery Mode</h3>
                <p>You are in the emergency system. This is a simplified interface for recovery purposes.</p>
            </div>
            
            <h1>{{ error_title }}</h1>
            <p>{{ error_message }}</p>
            <p><a href="/emergency/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="javascript:history.back()" class="btn btn-light">Go Back</a></p>
        </div>
    </body>
    </html>
    """
    
    # Write templates to files
    templates = {
        'emergency_login.html': login_template,
        'emergency_dashboard.html': dashboard_template,
        'emergency_journal_list.html': journal_list_template,
        'emergency_journal_view.html': journal_view_template,
        'emergency_reflection.html': reflection_template,
        'emergency_error.html': error_template
    }
    
    for name, content in templates.items():
        file_path = os.path.join(templates_dir, name)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(content)
            created.append(name)
    
    return jsonify({
        'success': True,
        'message': 'Created emergency templates',
        'templates_created': created
    })

if __name__ == "__main__":
    # Create all tables
    with app.app_context():
        db.create_all()
    
    # Run the app on a different port to avoid conflicts
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
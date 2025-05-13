"""
Add functionality for administrators to log in as any user.
This is useful for troubleshooting user issues and helping users access their accounts.
"""
import logging
import os
from flask import Blueprint, redirect, url_for, flash, render_template, request, session
from flask_login import login_user, current_user
from app import app, db
from models import User
from admin_models import Admin
from functools import wraps
from admin_routes import admin_required

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create Blueprint for admin login-as-user functionality
admin_login_as_user_bp = Blueprint('admin_login_as_user', __name__, url_prefix='/admin')

def setup_routes(app):
    """Setup admin login-as-user routes"""
    app.register_blueprint(admin_login_as_user_bp)
    logging.info("Admin login-as-user routes registered successfully")

@admin_login_as_user_bp.route('/users/login-as', methods=['GET'])
@admin_required
def users_login_as_form():
    """Show form to login as another user"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/login_as_user.html', users=users)

@admin_login_as_user_bp.route('/users/login-as', methods=['POST'])
@admin_required
def users_login_as():
    """Login as another user"""
    user_id = request.form.get('user_id')
    if not user_id:
        flash('No user selected', 'error')
        return redirect(url_for('admin_login_as_user.users_login_as_form'))
    
    # Store admin session info to return later
    session['admin_id'] = current_user.id
    session['is_admin_impersonating'] = True
    
    # Find the user
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin_login_as_user.users_login_as_form'))
    
    # Log in as user
    login_user(user)
    flash(f'You are now logged in as {user.username or user.email or user.id}', 'warning')
    logging.info(f"Admin {session['admin_id']} is now impersonating user {user.id}")
    
    # Redirect to the user's dashboard
    return redirect(url_for('dashboard'))

@admin_login_as_user_bp.route('/return-to-admin', methods=['GET'])
def return_to_admin():
    """Return to admin account after impersonating a user"""
    if 'admin_id' in session and session.get('is_admin_impersonating'):
        admin_id = session['admin_id']
        admin = Admin.query.get(admin_id)
        
        if admin:
            # Log back in as admin
            login_user(admin)
            flash('Returned to admin account', 'info')
            logging.info(f"Admin {admin_id} returned from impersonating a user")
            
            # Clean up session
            session.pop('admin_id', None)
            session.pop('is_admin_impersonating', None)
            
            return redirect(url_for('admin.dashboard'))
    
    # If not impersonating or admin not found, redirect to homepage
    flash('Not currently impersonating a user', 'error')
    return redirect(url_for('index'))

# Function to check if this is an admin impersonating a user
def is_admin_impersonating():
    """Check if the current session is an admin impersonating a user"""
    return 'admin_id' in session and session.get('is_admin_impersonating', False)

# Create admin login-as-user template
def create_template():
    """Create the admin login-as-user template"""
    template_path = 'templates/admin/login_as_user.html'
    import os
    
    if not os.path.exists('templates/admin'):
        os.makedirs('templates/admin')
    
    template_content = """{% extends "admin/base.html" %}

{% block title %}Login As User{% endblock %}

{% block content %}
<div class="container mt-4">
  <div class="row">
    <div class="col-md-12">
      <div class="card">
        <div class="card-header">
          <h5 class="card-title mb-0">Login As User</h5>
        </div>
        <div class="card-body">
          <div class="alert alert-warning">
            <strong>Warning:</strong> This will log you in as the selected user. You will have full access to their account.
            A banner will be shown at the top of the page to remind you that you're impersonating a user.
          </div>
          
          <form method="POST" action="{{ url_for('admin_login_as_user.users_login_as') }}">
            <div class="mb-3">
              <label for="user_id" class="form-label">Select User</label>
              <select name="user_id" id="user_id" class="form-select" required>
                <option value="">-- Select a user --</option>
                {% for user in users %}
                <option value="{{ user.id }}">
                  {{ user.username or user.email or user.id }} 
                  {% if user.email %}({{ user.email }}){% endif %}
                  - Created: {{ user.created_at.strftime('%Y-%m-%d') }}
                </option>
                {% endfor %}
              </select>
            </div>
            <button type="submit" class="btn btn-primary">Login As Selected User</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}"""
    
    with open(template_path, 'w') as f:
        f.write(template_content)
    
    return template_path

# Create a banner for impersonation mode
def add_impersonation_banner():
    """Add impersonation banner to layout.html"""
    template_path = 'templates/layout.html'
    
    if not os.path.exists(template_path):
        logging.error(f"Template {template_path} not found")
        return False
    
    # Read the template
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Check if the banner is already there
    if '{% if session.get("is_admin_impersonating") %}' in content:
        logging.info("Impersonation banner already exists in layout.html")
        return False
    
    # Find the best place to insert the banner (after body tag or before main content)
    insertion_point = '<body>' if '<body>' in content else '<main'
    
    # Banner HTML
    banner_html = """
{% if session.get("is_admin_impersonating") %}
<div class="alert alert-warning mb-0 text-center" style="border-radius: 0;">
  <strong>ADMIN MODE:</strong> You are currently viewing this page as a user. 
  <a href="{{ url_for('admin_login_as_user.return_to_admin') }}" class="alert-link">Return to admin account</a>
</div>
{% endif %}
"""
    
    # Insert the banner
    new_content = content.replace(insertion_point, insertion_point + banner_html)
    
    # Write back to the file
    with open(template_path, 'w') as f:
        f.write(new_content)
    
    logging.info("Added impersonation banner to layout.html")
    return True

if __name__ == "__main__":
    import os
    
    # Create template if it doesn't exist
    template_path = create_template()
    print(f"Created template: {template_path}")
    
    # Add impersonation banner
    print("To add the impersonation banner to layout.html, run this with app context.")
    print("Use: flask shell")
    print("Then: from admin_login_as_user import add_impersonation_banner; add_impersonation_banner()")
    
    # Add to app startup
    print("\nTo enable these routes, add this to your app.py:")
    print("from admin_login_as_user import setup_routes")
    print("setup_routes(app)")
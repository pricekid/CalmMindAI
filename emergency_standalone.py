"""
Super simple standalone admin access script.
This is a completely independent script with minimal dependencies.
"""

from flask import Blueprint, render_template, Response
from admin_models import Admin
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("emergency_standalone")

# Create blueprint
standalone_admin_bp = Blueprint('standalone_admin', __name__, url_prefix='/super-admin')

@standalone_admin_bp.route('/')
def standalone_admin():
    """
    Single route that directly displays admin information without requiring login.
    For emergency access only.
    """
    # Get admin info directly without authentication
    try:
        # Try to get the admin from the database
        admin = Admin.get("1")
        
        # If admin is not found, create a fallback admin object
        if not admin:
            # Create placeholder admin info
            admin_info = {
                "id": "1",
                "username": "admin (not found in database)"
            }
        else:
            admin_info = {
                "id": admin.id,
                "username": admin.username
            }
    except Exception as e:
        logger.error(f"Error getting admin: {e}")
        admin_info = {
            "id": "error",
            "username": f"Error: {str(e)}"
        }
    
    # Custom HTML response
    html_response = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Standalone Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ padding: 20px; background-color: #f8f9fa; }}
            .card {{ margin-top: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
            .action-card {{ margin-top: 30px; }}
            h1 {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-danger text-white">
                            <h2>Emergency Admin Access</h2>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-warning">
                                <strong>Warning:</strong> This is a completely isolated admin access page for emergency use only.
                            </div>
                            
                            <h4>Admin Information:</h4>
                            <ul class="list-group mb-4">
                                <li class="list-group-item"><strong>Admin ID:</strong> {admin_info['id']}</li>
                                <li class="list-group-item"><strong>Username:</strong> {admin_info['username']}</li>
                            </ul>
                            
                            <div class="d-grid gap-2">
                                <a href="/" class="btn btn-outline-secondary">Return to Home</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card action-card">
                        <div class="card-header bg-dark text-white">
                            <h4>Admin Access Paths</h4>
                        </div>
                        <div class="card-body">
                            <div class="list-group">
                                <a href="/admin/login" class="list-group-item list-group-item-action">Regular Admin Login</a>
                                <a href="/emergency/admin-login" class="list-group-item list-group-item-action">Emergency Admin Login</a>
                                <a href="/emergency/dashboard" class="list-group-item list-group-item-action">Emergency Admin Dashboard</a>
                                <a href="/emergency/status" class="list-group-item list-group-item-action">Login Status Check</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Return direct HTML response
    return Response(html_response, content_type='text/html')
"""
Emergency dashboard route to bypass all potential issues
"""
from flask import Blueprint, render_template_string
from flask_login import current_user, login_required
from app import app

emergency_dashboard_bp = Blueprint('emergency_dashboard', __name__)

@emergency_dashboard_bp.route('/emergency-dashboard')
@login_required
def emergency_dashboard():
    """Ultra-simple dashboard that should always work"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Dear Teddy</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #1a1a1a; color: white; }
            .card { background-color: #2d2d2d; border: none; }
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <div class="row">
                <div class="col-12">
                    <h1>Welcome, {{ username }}</h1>
                    <div class="card mt-4">
                        <div class="card-body">
                            <h5 class="card-title">Your Dashboard</h5>
                            <p class="card-text">Welcome to your personal wellness space.</p>
                            <a href="/journal" class="btn btn-primary">Start Journaling</a>
                            <a href="/logout" class="btn btn-secondary">Logout</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, username=current_user.username)

# Register the blueprint
app.register_blueprint(emergency_dashboard_bp)
"""
Emergency dashboard route that bypasses all error handling and complex logic.
This ensures users always have access to their dashboard even when other systems fail.
"""

from flask import Blueprint, render_template, redirect, request
from flask_login import login_required, current_user
import logging

# Create emergency dashboard blueprint
emergency_dashboard_bp = Blueprint('emergency_dashboard', __name__)

@emergency_dashboard_bp.route('/emergency-dashboard')
@login_required
def emergency_dashboard():
    """
    Ultra-simplified emergency dashboard that always works.
    This bypasses all complex logic and just shows basic dashboard.
    """
    try:
        # Check if user needs onboarding
        if not current_user.welcome_message_shown:
            logging.info(f"Emergency dashboard: New user {current_user.id} needs onboarding")
            return redirect('/onboarding/step1')
        
        # Very simple template rendering with minimal data
        return render_template('emergency_dashboard.html', 
                              title='Dashboard',
                              user=current_user)
    except Exception as e:
        logging.error(f"Emergency dashboard error: {str(e)}")
        # If even the emergency template fails, show ultra-basic HTML
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dear Teddy - Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-body text-center">
                                <h2>Welcome to Dear Teddy</h2>
                                <p>Your dashboard is temporarily unavailable, but you can still access your journal.</p>
                                <a href="/journal" class="btn btn-primary">Go to Journal</a>
                                <a href="/logout" class="btn btn-secondary ms-2">Logout</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

@emergency_dashboard_bp.route('/dashboard-fallback')
@login_required  
def dashboard_fallback():
    """
    Alternative dashboard route that users can be redirected to when main dashboard fails.
    """
    return emergency_dashboard()
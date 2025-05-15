"""
Simple notification test routes to help diagnose browser notification issues.
"""
from flask import Blueprint, render_template, jsonify
from app import app
from flask_login import login_required

notifications_test_bp = Blueprint('notifications_test', __name__)

@notifications_test_bp.route('/notifications-test')
@login_required
def notifications_test():
    """Test page for browser notifications"""
    return render_template('notifications_test.html')

def register_routes():
    """Register the notification test routes with the app"""
    app.register_blueprint(notifications_test_bp)
    app.logger.info('Notification test routes registered successfully')

# Register the routes
register_routes()
"""
Routes for handling notification-related requests.
This replaces the Flask-Mail implementation with a direct SMTP implementation
to solve environment variable access issues.
"""
import os
import logging
from flask import Blueprint, request, jsonify, current_app
from notification_service import send_test_email, send_immediate_notification_to_all_users

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a blueprint for notification routes
notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/api/notifications/test', methods=['POST'])
def test_notification():
    """
    Send a test notification to the specified email address.
    
    Request JSON format:
    {
        "email": "user@example.com"
    }
    
    Returns JSON with success flag and error message if applicable.
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'Email address is required'
            }), 400
        
        email = data['email']
        
        # Send a test email
        success = send_test_email(email)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Test notification sent to {email}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send test notification'
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500

@notification_bp.route('/api/notifications/send_all', methods=['POST'])
def send_all_notifications():
    """
    Send a notification to all users who have enabled notifications.
    
    This is an admin-only endpoint that requires an admin token.
    
    Request JSON format:
    {
        "admin_token": "your_admin_token_here"
    }
    
    Returns JSON with statistics about the notification sending process.
    """
    try:
        data = request.get_json()
        
        # Check admin token
        admin_token = data.get('admin_token')
        expected_token = os.environ.get('ADMIN_TOKEN')
        
        if not admin_token or admin_token != expected_token:
            return jsonify({
                'success': False,
                'error': 'Unauthorized: Invalid admin token'
            }), 401
            
        # Send notifications to all eligible users
        stats = send_immediate_notification_to_all_users()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
            
    except Exception as e:
        logger.error(f"Error sending notifications to all users: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500
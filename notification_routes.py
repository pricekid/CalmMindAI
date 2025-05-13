"""
Routes for handling notification-related requests.
This replaces the Flask-Mail implementation with a direct SMTP implementation
to solve environment variable access issues.
"""
import os
import logging
from flask import Blueprint, request, jsonify, current_app, redirect, url_for, flash, render_template
from notification_service import send_test_email, send_immediate_notification_to_all_users
from notification_service import send_test_sms
from app import login_required

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a blueprint for notification routes
notification_bp = Blueprint('notification', __name__)

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

@notification_bp.route('/send_immediate_notification', methods=['POST'])
@login_required
def send_immediate_notification():
    """
    Send an immediate notification to all users with notifications enabled.
    This is an admin-only route that can be used to send reminders manually.
    """
    try:
        # Send notifications to all eligible users
        stats = send_immediate_notification_to_all_users()
        
        # Log statistics
        logger.info(f"Immediate notification sent to {stats.get('success_count', 0)} users")
        
        flash(f"Successfully sent notifications to {stats.get('success_count', 0)} users. Failed: {stats.get('failure_count', 0)}", 'success')
        return redirect(url_for('admin.settings'))
            
    except Exception as e:
        logger.error(f"Error sending notifications to all users: {str(e)}", exc_info=True)
        flash(f"Error sending notifications: {str(e)}", 'danger')
        return redirect(url_for('admin.settings'))

@notification_bp.route('/test_email_notification', methods=['POST'])
@login_required
def test_email_notification():
    """Send a test email notification to the provided email address"""
    try:
        email_address = request.form.get('email_address')
        
        if not email_address:
            flash('Email address is required', 'danger')
            return redirect(url_for('admin.settings'))
        
        # Send test email
        success = send_test_email(email_address)
        
        if success:
            flash(f'Test email sent to {email_address}', 'success')
        else:
            flash('Failed to send test email. Check server logs for details.', 'danger')
            
        return redirect(url_for('admin.settings'))
        
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}", exc_info=True)
        flash(f'Error sending test email: {str(e)}', 'danger')
        return redirect(url_for('admin.settings'))

@notification_bp.route('/test_sms_notification', methods=['POST'])
@login_required
def test_sms_notification():
    """Send a test SMS notification to the provided phone number"""
    try:
        phone_number = request.form.get('phone_number')
        
        if not phone_number:
            flash('Phone number is required', 'danger')
            return redirect(url_for('admin.settings'))
        
        # Send test SMS
        success = send_test_sms(phone_number)
        
        if success:
            flash(f'Test SMS sent to {phone_number}', 'success')
        else:
            flash('Failed to send test SMS. Check server logs for details.', 'danger')
            
        return redirect(url_for('admin.settings'))
        
    except Exception as e:
        logger.error(f"Error sending test SMS: {str(e)}", exc_info=True)
        flash(f'Error sending test SMS: {str(e)}', 'danger')
        return redirect(url_for('admin.settings'))

@notification_bp.route('/send_immediate_sms_notification', methods=['POST'])
@login_required
def send_immediate_sms_notification():
    """Send an immediate SMS notification to all users with SMS notifications enabled"""
    try:
        # Import here to avoid circular imports
        from notification_service import send_immediate_sms_to_all_users
        
        # Send SMS to all eligible users
        stats = send_immediate_sms_to_all_users()
        
        # Log statistics
        logger.info(f"Immediate SMS sent to {stats.get('success_count', 0)} users")
        
        flash(f"Successfully sent SMS to {stats.get('success_count', 0)} users. Failed: {stats.get('failure_count', 0)}", 'success')
        return redirect(url_for('admin.settings'))
            
    except Exception as e:
        logger.error(f"Error sending SMS to all users: {str(e)}", exc_info=True)
        flash(f"Error sending SMS notifications: {str(e)}", 'danger')
        return redirect(url_for('admin.settings'))
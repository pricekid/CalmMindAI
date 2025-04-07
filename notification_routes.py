from flask import Blueprint, redirect, url_for, flash, request, render_template
from flask_login import current_user, login_required
import logging
import os
import traceback
from send_immediate_notification import send_immediate_notification_to_all_users, send_test_email
from send_immediate_sms import test_sms, send_immediate_sms_to_all
from admin_utils import load_twilio_config
from admin_routes import admin_required

# Set up logging
logger = logging.getLogger(__name__)

# Create a blueprint for notification routes
# Use a unique name to avoid conflicts in registration
notification_bp = Blueprint('notification_routes', __name__, url_prefix='/notification')

@notification_bp.route('/send-immediate', methods=['POST'])
@login_required
@admin_required
def send_immediate_notification():
    """Send an immediate email notification to all users with notifications enabled"""
    try:
        result = send_immediate_notification_to_all_users()
        
        if result and 'success' in result:
            flash(f'Successfully sent {result["success"]} email notifications.', 'success')
            
            # Log any failures
            if 'errors' in result and result['errors'] > 0:
                flash(f'Failed to send {result["errors"]} email notifications.', 'warning')
        else:
            flash('No email notifications were sent. Check mail configuration or ensure users have notifications enabled.', 'warning')
            
    except Exception as e:
        logger.error(f"Error sending email notifications: {str(e)}")
        flash(f'Error sending email notifications: {str(e)}', 'danger')
    
    return redirect(url_for('admin.scheduler_logs'))

@notification_bp.route('/test-email', methods=['POST'])
@login_required
@admin_required
def test_email_notification():
    """Send a test email to a specific email address"""
    if request.method == 'POST':
        email = request.form.get('email_address')
        
        if not email:
            flash('Email address is required', 'danger')
            return redirect(url_for('admin.settings'))
        
        try:
            success = send_test_email(email)
            
            if success:
                flash(f'Test email sent successfully to {email}', 'success')
            else:
                flash(f'Failed to send test email to {email}. Check mail configuration.', 'danger')
        except Exception as e:
            flash(f'Error sending test email: {str(e)}', 'danger')
            
        return redirect(url_for('admin.settings'))

@notification_bp.route('/test-sms', methods=['POST'])
@login_required
@admin_required
def test_sms_notification():
    """Send a test SMS to a specific phone number"""
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        
        if not phone_number:
            flash('Phone number is required', 'danger')
            return redirect(url_for('admin.settings'))
        
        try:
            # Load Twilio config from environment or file
            twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
            twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
            twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
            
            # If not in environment, try to load from file
            if not all([twilio_sid, twilio_token, twilio_phone]):
                twilio_config = load_twilio_config()
                if twilio_config:
                    if not twilio_sid and 'account_sid' in twilio_config:
                        os.environ["TWILIO_ACCOUNT_SID"] = twilio_config['account_sid']
                    if not twilio_token and 'auth_token' in twilio_config:
                        os.environ["TWILIO_AUTH_TOKEN"] = twilio_config['auth_token']
                    if not twilio_phone and 'phone_number' in twilio_config:
                        os.environ["TWILIO_PHONE_NUMBER"] = twilio_config['phone_number']
            
            # Send the test SMS
            result = test_sms(phone_number)
            
            if result.get('success', False):
                flash(f'Test SMS sent successfully to {phone_number}', 'success')
            else:
                error_msg = result.get('error', 'Unknown error')
                flash(f'Failed to send test SMS: {error_msg}', 'danger')
        except Exception as e:
            logger.error(f"Error sending test SMS: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f'Error sending test SMS: {str(e)}', 'danger')
            
        return redirect(url_for('admin.settings'))

@notification_bp.route('/send-immediate-sms', methods=['POST'])
@login_required
@admin_required
def send_immediate_sms_notification():
    """Send an immediate SMS notification to all users with SMS notifications enabled"""
    try:
        # Send SMS notifications to all eligible users
        from sms_notification_service import send_immediate_sms_to_all_users
        result = send_immediate_sms_to_all_users()
        
        if result['success_count'] > 0:
            flash(f'Successfully sent {result["success_count"]} SMS notifications.', 'success')
        else:
            flash('No SMS notifications were sent. Check Twilio configuration or ensure users have SMS notifications enabled.', 'warning')
        
        # Log any failures
        if result['failure_count'] > 0:
            flash(f'Failed to send {result["failure_count"]} SMS notifications.', 'warning')
            
    except Exception as e:
        logger.error(f"Error sending SMS notifications: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'Error sending SMS notifications: {str(e)}', 'danger')
    
    return redirect(url_for('admin.scheduler_logs'))
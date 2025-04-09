from flask import Blueprint, redirect, url_for, flash, request, render_template, current_app as app
from flask_login import current_user, login_required
import logging
import os
import traceback
from models import User
from send_immediate_sms import test_sms, send_immediate_sms_to_all
from admin_utils import load_twilio_config
from admin_routes import admin_required

# Set up logging
logger = logging.getLogger(__name__)

# Create a blueprint for notification routes
# Use a unique name to avoid conflicts in registration
notification_bp = Blueprint('notification', __name__, url_prefix='/notification')

@notification_bp.route('/send-immediate', methods=['POST'])
@login_required
@admin_required
def send_immediate_notification():
    """Send an immediate email notification to all users with notifications enabled"""
    try:
        # Use the improved email service
        from improved_email_service import send_immediate_notification_to_all_users
        
        # Count users with notifications enabled
        notification_users_count = User.query.filter_by(notifications_enabled=True).count()
        
        if notification_users_count == 0:
            flash('No users have email notifications enabled. Please enable notifications for at least one user.', 'warning')
            return redirect(url_for('admin.scheduler_logs'))
            
        # Log detailed email configuration for debugging
        logger.info(f"Mail configuration for immediate notification:")
        logger.info(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        logger.info(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        logger.info(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        logger.info(f"MAIL_USERNAME: {'Set' if app.config.get('MAIL_USERNAME') else 'Not set'}")
        logger.info(f"MAIL_PASSWORD: {'Set' if app.config.get('MAIL_PASSWORD') else 'Not set'}")
        logger.info(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        logger.info(f"Number of users with notifications enabled: {notification_users_count}")
        
        # Check for missing email configuration
        if not all([
            app.config.get('MAIL_SERVER'),
            app.config.get('MAIL_PORT'),
            app.config.get('MAIL_USERNAME'),
            app.config.get('MAIL_PASSWORD'),
            app.config.get('MAIL_DEFAULT_SENDER')
        ]):
            missing = []
            if not app.config.get('MAIL_SERVER'): missing.append("MAIL_SERVER")
            if not app.config.get('MAIL_PORT'): missing.append("MAIL_PORT")
            if not app.config.get('MAIL_USERNAME'): missing.append("MAIL_USERNAME")
            if not app.config.get('MAIL_PASSWORD'): missing.append("MAIL_PASSWORD")
            if not app.config.get('MAIL_DEFAULT_SENDER'): missing.append("MAIL_DEFAULT_SENDER")
            
            error_msg = f"Missing email configuration: {', '.join(missing)}"
            logger.error(error_msg)
            flash(f"Cannot send emails: {error_msg}", 'danger')
            flash("Please check your email settings in the .env file or environment variables.", 'danger')
            return redirect(url_for('admin.scheduler_logs'))
        
        # All checks passed, send the notifications
        result = send_immediate_notification_to_all_users()
        
        if result and 'success' in result:
            flash(f'Successfully sent {result["success"]} email notifications.', 'success')
            
            # Log any failures
            if 'errors' in result and result['errors'] > 0:
                flash(f'Failed to send {result["errors"]} email notifications.', 'warning')
                logger.error(f"Email notification failures: {result.get('errors', 0)}")
                
                # Add troubleshooting options
                flash('To diagnose email issues, run the "python diagnose_notification_issue.py" script from the command line.', 'info')
        else:
            flash('No email notifications were sent. This could be due to missing email configuration or no enabled users.', 'warning')
            flash('Please run "python diagnose_notification_issue.py" to diagnose the issue.', 'info')
            
    except Exception as e:
        logger.error(f"Error sending email notifications: {str(e)}")
        logger.exception("Detailed error when sending email notifications")
        flash(f'Error sending email notifications: {str(e)}', 'danger')
        flash('For detailed diagnosis, run the "python diagnose_notification_issue.py" script.', 'info')
    
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
            # Use the improved email service
            from improved_email_service import send_test_email
            
            # Log the email configuration
            logger.info(f"Testing email with configuration:")
            logger.info(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
            logger.info(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
            logger.info(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
            logger.info(f"MAIL_USERNAME: {'Set' if app.config.get('MAIL_USERNAME') else 'Not set'}")
            logger.info(f"MAIL_PASSWORD: {'Set' if app.config.get('MAIL_PASSWORD') else 'Not set'}")
            logger.info(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
            
            success = send_test_email(email)
            
            if success:
                flash(f'Test email sent successfully to {email}', 'success')
            else:
                flash(f'Failed to send test email to {email}. Check mail configuration.', 'danger')
                
                # Add more detailed diagnostics
                if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
                    flash('Email credentials may be missing or incorrect. Check your mail configuration in the admin settings.', 'danger')
                elif not app.config.get('MAIL_DEFAULT_SENDER'):
                    flash('Default sender email is missing. Check your mail configuration.', 'danger')
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            logger.exception("Detailed error when sending test email")
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
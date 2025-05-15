"""
Preview email templates directly in the browser.
This is a helpful tool for testing email templates without sending actual emails.
"""

from datetime import datetime
from flask import Blueprint, render_template

preview_email_bp = Blueprint('preview_email', __name__)

@preview_email_bp.route('/preview/app_update_notification')
def preview_app_update():
    """Preview the app update notification email"""
    return render_template('emails/app_update_notification.html')

@preview_email_bp.route('/preview/password_reset')
def preview_password_reset():
    """Preview the password reset email"""
    reset_url = "https://calm-mind-ai-naturalarts.replit.app/reset-password/example_token_for_preview"
    return render_template('emails/password_reset.html', reset_url=reset_url)

@preview_email_bp.route('/preview/test_email')
def preview_test_email():
    """Preview the test email"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template(
        'emails/standard_notification.html',
        title="Email System Test",
        message=f"This is a test email sent from the Dear Teddy application. If you're seeing this, the email notification system is working correctly! Time sent: {timestamp}",
        highlight="<p><strong>Note:</strong> This is an automated message sent to verify the email delivery system. No action is required.</p>",
        action_url="https://calm-mind-ai-naturalarts.replit.app",
        action_text="Visit Dear Teddy"
    )

@preview_email_bp.route('/preview/standard_notification')
def preview_standard_notification():
    """Preview the standard notification email template"""
    return render_template(
        'emails/standard_notification.html',
        title="Daily Journal Reminder",
        message="Your wellbeing matters to us. Take a moment today to reflect on your thoughts and feelings with Dear Teddy.",
        highlight="<p>Regular journaling can help reduce anxiety and improve mental clarity. Just a few minutes each day can make a big difference.</p>",
        action_url="https://calm-mind-ai-naturalarts.replit.app/journal",
        action_text="Start Journaling"
    )
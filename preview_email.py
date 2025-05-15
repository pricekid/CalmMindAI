"""
Preview email templates directly in the browser.
This is a helpful tool for testing email templates without sending actual emails.
"""

from flask import Blueprint, render_template

preview_email_bp = Blueprint('preview_email', __name__)

@preview_email_bp.route('/preview/app_update_notification')
def preview_app_update():
    """Preview the app update notification email"""
    return render_template('emails/app_update_notification.html')

@preview_email_bp.route('/preview/password_reset')
def preview_password_reset():
    """Preview the password reset email"""
    reset_url = "https://dearteddy-app.replit.app/reset-password/example_token_for_preview"
    return render_template('emails/password_reset.html', reset_url=reset_url)
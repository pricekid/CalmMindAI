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
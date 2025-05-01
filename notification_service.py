"""
Notification service - All notifications permanently disabled
"""
import os
import smtplib
import logging
import json
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Function to check if notifications are blocked
def check_notifications_blocked():
    '''Check if notifications are blocked by the existence of a block file'''
    # Check block file
    block_file = os.path.join('data', 'notifications_blocked')
    if os.path.exists(block_file):
        logger.info("Notifications blocked by block file")
        return True

    # Check time - only allow between 5:45am and 6:15am Caribbean time
    caribbean_tz = pytz.timezone('America/Port_of_Spain')
    current_time = datetime.now(caribbean_tz)

    # Create absolute timestamps for today's window
    today = current_time.date()
    allowed_start = caribbean_tz.localize(datetime.combine(today, datetime.min.time().replace(hour=5, minute=45)))
    allowed_end = caribbean_tz.localize(datetime.combine(today, datetime.min.time().replace(hour=6, minute=15)))

    # Force block outside window
    if not (allowed_start <= current_time <= allowed_end):
        logger.warning(f"Notifications blocked - current time {current_time} is outside allowed window")
        logger.warning(f"Window: {allowed_start} to {allowed_end}")

        # Create block file
        try:
            with open(block_file, 'w') as f:
                f.write(str(datetime.now(pytz.UTC)))
            logger.info("Created notification block file")
        except Exception as e:
            logger.error(f"Error creating block file: {e}")

        return True

    return False

def ensure_data_directory():
    """Ensure the data directory exists"""

    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data'):
        os.makedirs('data')

def load_users():
    """Load users from the data/users.json file"""

    # Check if notifications are blocked
    if check_notifications_blocked():
        logger.info("Notifications are currently blocked")
        return {"success": False, "error": "Notifications are currently blocked"}
    ensure_data_directory()
    if not os.path.exists('data/users.json'):
        return []

    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Error decoding users.json file")
        return []
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def get_mail_config():
    """
    Get email configuration directly from environment variables rather than app config.

    This is a workaround for when Flask's app.config doesn't properly pick up the environment variables.
    """
    mail_config = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': True,
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', 'calmjourney7@gmail.com'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER')
    }

    return mail_config

def send_email(*args, **kwargs):
    """All email notifications are disabled"""
    logger.info("Email notifications are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}

def send_test_email(*args, **kwargs):
    """Test email function is disabled"""
    logger.info("Test email notifications are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}

def send_login_link(*args, **kwargs):
    """Login link emails are disabled"""
    logger.info("Login link emails are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}

def send_daily_reminder(*args, **kwargs):
    """Daily reminders are disabled"""
    logger.info("Daily reminder notifications are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}

def send_daily_reminder_direct(*args, **kwargs):
    """Direct daily reminders are disabled"""
    logger.info("Direct daily reminders are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}

def send_weekly_summary(user, stats):
    """
    Send a weekly summary to a user.

    Args:
        user: Dictionary containing user information
        stats: Dictionary containing weekly stats

    Returns:
        bool: True if successful, False otherwise
    """
    email = user.get('email')
    username = user.get('username', 'there')

    if not email:
        logger.error(f"Cannot send summary: No email for user {username}")
        return False

    subject = "Calm Journey - Your Weekly Wellness Summary"
    html_body = f"""
    <html>
    <body>
        <h2>Calm Journey - Your Weekly Wellness Summary</h2>
        <p>Hello {username}!</p>
        <p>Here's a summary of your wellness journey for the past week:</p>
        <ul>
            <li><strong>Journal Entries:</strong> {stats.get('entries', 0)}</li>
            <li><strong>Average Anxiety Level:</strong> {stats.get('avg_anxiety', 'N/A')}</li>
            <li><strong>Most Common Pattern:</strong> {stats.get('common_pattern', 'None identified')}</li>
        </ul>
        <p>Thank you for continuing your wellness journey with us. Remember, every step you take toward self-awareness is a step toward better mental health.</p>
        <p><a href="https://calm-mind-ai-naturalarts.replit.app/journal">View Your Journal History</a></p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
        <p style="font-size: 0.9em; color: #444; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #5f9ea0; border-radius: 3px; margin-top: 15px;">
            <strong>P.S. Know someone who could use a moment of calm?</strong><br>
            If you have a friend or loved one who might benefit from a gentle daily check-in, feel free to forward this email or share Calm Journey with them:<br>
            <a href="https://calm-mind-ai-naturalarts.replit.app">https://calm-mind-ai-naturalarts.replit.app</a><br>
            Helping one another breathe easier—one day at a time.
        </p>
        <hr>
        <p style="font-size: 0.8em; color: #666;">
            You received this email because you enabled notifications in your Calm Journey account.
            If you'd like to unsubscribe, please update your notification preferences in your account settings.
        </p>
    </body>
    </html>
    """
    text_body = f"""Calm Journey - Your Weekly Wellness Summary

Hello {username}!

Here's a summary of your wellness journey for the past week:

- Journal Entries: {stats.get('entries', 0)}
- Average Anxiety Level: {stats.get('avg_anxiety', 'N/A')}
- Most Common Pattern: {stats.get('common_pattern', 'None identified')}

Thank you for continuing your wellness journey with us. Remember, every step you take toward self-awareness is a step toward better mental health.

Visit https://calm-mind-ai-naturalarts.replit.app/journal to view your journal history.

The Calm Journey Team

P.S. Know someone who could use a moment of calm?
If you have a friend or loved one who might benefit from a gentle daily check-in, feel free to forward this email or share Calm Journey with them:
https://calm-mind-ai-naturalarts.replit.app
Helping one another breathe easier—one day at a time.

--
You received this email because you enabled notifications in your Calm Journey account.
If you'd like to unsubscribe, please update your notification preferences in your account settings.
"""

    result = send_email(email, subject, html_body, text_body)
    return result.get('success', False)

def send_immediate_notification_to_all_users():
    """
    Send an immediate notification to all users with notifications enabled.

    Returns:
        dict: Statistics about the notification sending process
    """
    users = load_users()
    sent_count = 0
    failed_count = 0
    skipped_count = 0

    for user in users:
        # Skip users who have disabled notifications
        if not user.get('notifications_enabled', False):
            skipped_count += 1
            continue

        # Get the user's email
        email = user.get('email')
        if not email:
            skipped_count += 1
            continue

        # Send a notification
        if send_daily_reminder(user):
            sent_count += 1
        else:
            failed_count += 1

    stats = {
        'total_users': len(users),
        'sent_count': sent_count,
        'failed_count': failed_count,
        'skipped_count': skipped_count,
        'timestamp': datetime.now().isoformat()
    }

    return stats

def send_daily_sms_reminder_direct(*args, **kwargs):
    """Direct daily reminders are disabled"""
    logger.info("Direct daily SMS reminders are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}
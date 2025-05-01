"""
Notification service - All notifications permanently disabled
"""
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Function to check if notifications are blocked
def check_notifications_blocked():
    """Check if notifications are blocked"""
    return True

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
        'MAIL_SERVER': None,
        'MAIL_PORT': None,
        'MAIL_USE_TLS': False,
        'MAIL_USERNAME': None,
        'MAIL_PASSWORD': None,
        'MAIL_DEFAULT_SENDER': None
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

def send_weekly_summary(*args, **kwargs):
    """Weekly summary emails are disabled"""
    logger.info("Weekly summary notifications are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}

def send_immediate_notification_to_all_users(*args, **kwargs):
    """Immediate notifications are disabled"""
    logger.info("Immediate notifications are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}

def send_daily_sms_reminder_direct(*args, **kwargs):
    """Direct daily reminders are disabled"""
    logger.info("Direct daily SMS reminders are permanently disabled")
    return {"success": False, "error": "Notifications are permanently disabled"}

import os
import json
from datetime import datetime
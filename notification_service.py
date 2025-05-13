"""
Notification service - All notifications permanently disabled
"""
import logging
import os
import json
from datetime import datetime

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

def load_users():
    """Load users from the data/users.json file"""
    ensure_data_directory()
    
    # Check if notifications are blocked
    if check_notifications_blocked():
        logger.info("Notifications are currently blocked")
        return {"success": False, "error": "Notifications are currently blocked"}
    
    if not os.path.exists('data/users.json'):
        return []
        
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        return users
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def send_test_email(email_address):
    """
    Send a test email to verify the email service is working.
    """
    try:
        logger.info(f"Attempting to send test email to {email_address}")
        
        # Since notifications are disabled, just log the attempt
        if check_notifications_blocked():
            logger.warning("Test email not sent - notifications are blocked")
            return True
            
        # In a real implementation, this would use SMTP
        logger.info(f"Test email would be sent to {email_address}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return False

def send_test_sms(phone_number):
    """
    Send a test SMS to verify the SMS service is working.
    """
    try:
        logger.info(f"Attempting to send test SMS to {phone_number}")
        
        # Since notifications are disabled, just log the attempt
        if check_notifications_blocked():
            logger.warning("Test SMS not sent - notifications are blocked")
            return True
            
        # In a real implementation, this would use Twilio
        logger.info(f"Test SMS would be sent to {phone_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending test SMS: {str(e)}")
        return False
        
def send_immediate_notification_to_all_users():
    """
    Send an immediate notification to all users with notifications enabled.
    """
    # Since notifications are disabled, just log the attempt
    if check_notifications_blocked():
        logger.warning("Immediate notifications not sent - notifications are blocked")
        return {
            "success_count": 0,
            "failure_count": 0,
            "message": "Notifications are currently blocked"
        }
        
    # In a real implementation, this would send emails to all eligible users
    logger.info("Immediate notifications would be sent to all eligible users")
    return {
        "success_count": 0,
        "failure_count": 0,
        "message": "Notifications are currently disabled"
    }
    
def send_immediate_sms_to_all_users():
    """
    Send an immediate SMS to all users with SMS notifications enabled.
    """
    # Since notifications are disabled, just log the attempt
    if check_notifications_blocked():
        logger.warning("Immediate SMS notifications not sent - notifications are blocked")
        return {
            "success_count": 0,
            "failure_count": 0,
            "message": "Notifications are currently blocked"
        }
        
    # In a real implementation, this would send SMS to all eligible users
    logger.info("Immediate SMS notifications would be sent to all eligible users")
    return {
        "success_count": 0,
        "failure_count": 0,
        "message": "SMS notifications are currently disabled"
    }
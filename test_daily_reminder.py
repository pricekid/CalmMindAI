"""
Test script to send a daily reminder email with referral link to a specific email address.
This script can be used to verify the email content and formatting before sending to all users.
"""
import sys
import logging
from notification_service import ensure_data_directory, get_user_referral_url, send_daily_reminder

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_test_daily_reminder(email):
    """
    Send a test daily reminder email to the specified email address.
    
    Args:
        email: The email address to send the test to
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Create a test user with the provided email
    test_user = {
        'id': 999,  # Use a dummy ID
        'username': 'Test User',
        'email': email,
        'notifications_enabled': True,
        'referral_code': 'TESTCODE'  # We'll use a fixed code for the test
    }
    
    # Send the daily reminder to this test user
    logger.info(f"Sending test daily reminder to {email}")
    result = send_daily_reminder(test_user)
    
    if result:
        logger.info(f"Successfully sent test daily reminder to {email}")
    else:
        logger.error(f"Failed to send test daily reminder to {email}")
    
    return result

if __name__ == "__main__":
    # Check if an email address was provided as a command-line argument
    if len(sys.argv) > 1:
        email = sys.argv[1]
        send_test_daily_reminder(email)
    else:
        print("Usage: python test_daily_reminder.py <email_address>")
        sys.exit(1)
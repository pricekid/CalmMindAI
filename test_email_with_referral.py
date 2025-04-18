"""
Test script to send an email with the updated referral message.
This will use the send_daily_reminder function to send a real test email.
"""
import os
import sys
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')

def load_users():
    """Load users from the data/users.json file"""
    ensure_data_directory()
    if not os.path.exists('data/users.json'):
        return []
    
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def get_test_user():
    """
    Get a user to test with, either by ID or email.
    Returns None if user not found.
    """
    test_email = input("Enter the email address to send the test to: ")
    
    users = load_users()
    for user in users:
        if user.get('email') == test_email:
            return user
    
    # If user not found, create a temporary user with the provided email
    print(f"No user found with email {test_email}. Creating a temporary test user.")
    username = test_email.split('@')[0]  # Use part before @ as username
    return {
        'id': 'test_user',
        'username': username,
        'email': test_email,
        'notifications_enabled': True
    }

def ensure_mail_config():
    """Ensure mail configuration is set for testing."""
    # Check for SendGrid API key
    if not os.environ.get('SENDGRID_API_KEY'):
        logger.error("SENDGRID_API_KEY environment variable not found")
        return False
    
    # Set up mail server config if needed
    if not os.environ.get('MAIL_SERVER'):
        os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
    if not os.environ.get('MAIL_PORT'):
        os.environ['MAIL_PORT'] = '587'
    
    return True

def send_test_email():
    """
    Send a test email using the daily_reminder function
    to verify the referral message is correctly included.
    """
    # First make sure mail configuration is set
    if not ensure_mail_config():
        logger.error("Mail configuration is not set properly")
        return False
    
    # Get a test user
    user = get_test_user()
    if not user:
        logger.error("Could not get a test user")
        return False
    
    # Import the send_daily_reminder function
    try:
        from notification_service import send_daily_reminder
        
        # Send the test email
        logger.info(f"Sending test email to {user['email']}...")
        result = send_daily_reminder(user)
        
        if result:
            logger.info(f"Test email sent successfully to {user['email']}")
            return True
        else:
            logger.error(f"Failed to send test email to {user['email']}")
            return False
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return False

if __name__ == "__main__":
    print("Sending test email with referral message...")
    success = send_test_email()
    if success:
        print("Test email sent successfully! Check your inbox to see the referral message.")
    else:
        print("Failed to send test email. Check the logs for more information.")
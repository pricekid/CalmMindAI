"""
Test script to send an SMS with the updated referral message.
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
    Get a user to test with, or create a temporary test user.
    """
    test_phone = input("Enter the phone number to send the test SMS to (with country code, e.g. +1234567890): ")
    
    users = load_users()
    for user in users:
        if user.get('phone') == test_phone:
            return user
    
    # If user not found, create a temporary user with the provided phone number
    print(f"No user found with phone number {test_phone}. Creating a temporary test user.")
    return {
        'id': 'test_user',
        'username': 'TestUser',
        'phone': test_phone,
        'sms_notifications_enabled': True
    }

def ensure_twilio_config():
    """Ensure Twilio configuration is set for testing."""
    missing = []
    if not os.environ.get('TWILIO_ACCOUNT_SID'):
        missing.append('TWILIO_ACCOUNT_SID')
    if not os.environ.get('TWILIO_AUTH_TOKEN'):
        missing.append('TWILIO_AUTH_TOKEN')
    if not os.environ.get('TWILIO_PHONE_NUMBER'):
        missing.append('TWILIO_PHONE_NUMBER')
    
    if missing:
        logger.error(f"Missing Twilio configuration: {', '.join(missing)}")
        print("Twilio configuration is missing. Please set the following environment variables:")
        for var in missing:
            value = input(f"Enter your {var}: ")
            os.environ[var] = value
    
    return True

def send_test_sms():
    """
    Send a test SMS using the Twilio API to verify the referral message.
    """
    # First make sure Twilio configuration is set
    if not ensure_twilio_config():
        logger.error("Twilio configuration is not set properly")
        return False
    
    # Get a test user
    user = get_test_user()
    if not user:
        logger.error("Could not get a test user")
        return False
    
    # Import Twilio client
    try:
        from twilio.rest import Client
        
        # Get Twilio credentials
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        from_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Compose message with referral text
        username = user.get('username', 'there')
        message_body = f"Hello {username}! This is your daily reminder from Calm Journey. Take a moment to check in with yourself today. Visit https://calm-mind-ai-naturalarts.replit.app/journal/new to journal. P.S. Know someone who could use a moment of calm? Share Calm Journey with them—helping one another breathe easier, one day at a time."
        
        # Send the SMS
        logger.info(f"Sending test SMS to {user['phone']}...")
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=user['phone']
        )
        
        if message.sid:
            logger.info(f"Test SMS sent successfully to {user['phone']} (SID: {message.sid})")
            return True
        else:
            logger.error(f"Failed to send test SMS to {user['phone']}")
            return False
    except Exception as e:
        logger.error(f"Error sending test SMS: {str(e)}")
        return False

if __name__ == "__main__":
    print("Sending test SMS with referral message...")
    success = send_test_sms()
    if success:
        print("Test SMS sent successfully! Check your phone to see the referral message.")
    else:
        print("Failed to send test SMS. Check the logs for more information.")
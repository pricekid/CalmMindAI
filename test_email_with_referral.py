"""
Test script to verify the enhanced email templates with the updated referral message.
"""
import os
import sys
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
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
    except json.JSONDecodeError:
        logger.error("Error decoding users.json file")
        return []
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def test_daily_email_with_referral():
    """
    Test the daily email with the enhanced referral message.
    This sends an email to the specified test recipient.
    """
    # Import notification service
    from notification_service import send_daily_reminder
    
    # Create a test user
    test_email = os.environ.get('TEST_EMAIL')
    
    if not test_email:
        logger.error("TEST_EMAIL environment variable not set.")
        test_email = input("Enter test email address: ")
    
    test_user = {
        'id': 'test-user-id',
        'username': 'Test User',
        'email': test_email,
        'notifications_enabled': True
    }
    
    # Send test email
    logger.info(f"Sending test daily email with referral message to {test_email}")
    result = send_daily_reminder(test_user)
    
    if result:
        logger.info("✅ Test email sent successfully!")
        return True
    else:
        logger.error("❌ Failed to send test email.")
        return False

def test_weekly_summary_with_referral():
    """
    Test the weekly summary email with the enhanced referral message.
    This sends an email to the specified test recipient.
    """
    # Import notification service
    from notification_service import send_weekly_summary
    
    # Create a test user
    test_email = os.environ.get('TEST_EMAIL')
    
    if not test_email:
        logger.error("TEST_EMAIL environment variable not set.")
        test_email = input("Enter test email address: ")
    
    test_user = {
        'id': 'test-user-id',
        'username': 'Test User',
        'email': test_email,
        'notifications_enabled': True
    }
    
    # Create test stats
    test_stats = {
        'entries': 5,
        'avg_anxiety': 4.2,
        'common_pattern': 'All-or-Nothing Thinking',
        'date_range': f"{datetime.now().strftime('%B %d')} - {datetime.now().strftime('%B %d, %Y')}"
    }
    
    # Send test email
    logger.info(f"Sending test weekly summary with referral message to {test_email}")
    result = send_weekly_summary(test_user, test_stats)
    
    if result:
        logger.info("✅ Test weekly summary sent successfully!")
        return True
    else:
        logger.error("❌ Failed to send test weekly summary.")
        return False

def test_sms_with_referral():
    """
    Test the SMS message with the enhanced referral message.
    This sends an SMS to the specified test phone number if Twilio is configured.
    """
    # Check Twilio configuration
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, from_number]):
        logger.error("Twilio not configured. Skipping SMS test.")
        return False
    
    # Get test phone number
    test_phone = os.environ.get('TEST_PHONE')
    
    if not test_phone:
        logger.error("TEST_PHONE environment variable not set.")
        test_phone = input("Enter test phone number with country code (e.g. +1234567890): ")
    
    # Create and send test SMS
    try:
        from twilio.rest import Client
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Compose message
        message_body = "Hello Test User! This is your daily reminder from Calm Journey. Take a moment to check in with yourself today. Visit https://calm-mind-ai-naturalarts.replit.app/journal/new to journal. P.S. Know someone who could use a moment of calm? If you have a friend or loved one who might benefit from a gentle daily check-in, share Calm Journey with them: https://calm-mind-ai-naturalarts.replit.app. Helping one another breathe easier—one day at a time."
        
        # Send SMS
        logger.info(f"Sending test SMS to {test_phone}")
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=test_phone
        )
        
        # Check if message was sent successfully
        if message.sid:
            logger.info(f"✅ Test SMS sent successfully! (SID: {message.sid})")
            return True
        else:
            logger.error("❌ Failed to send test SMS.")
            return False
            
    except ImportError:
        logger.error("Twilio library not installed. Skipping SMS test.")
        return False
    except Exception as e:
        logger.error(f"Error sending test SMS: {str(e)}")
        return False

def main():
    """Test both daily and weekly emails with the enhanced referral message."""
    # Print warning
    print("\n" + "="*80)
    print("WARNING: This script will send actual emails/SMS messages to test the referral message.")
    print("Make sure you have the correct email/SMS credentials set up.")
    print("="*80 + "\n")
    
    choice = input("Choose test type: \n1. Daily Email \n2. Weekly Summary Email \n3. SMS\n4. All\nChoice: ")
    
    try:
        choice = int(choice.strip())
    except ValueError:
        logger.error("Invalid choice. Please enter a number.")
        return
    
    results = {}
    
    if choice == 1 or choice == 4:
        results['daily_email'] = test_daily_email_with_referral()
    if choice == 2 or choice == 4:
        results['weekly_summary'] = test_weekly_summary_with_referral()
    if choice == 3 or choice == 4:
        results['sms'] = test_sms_with_referral()
    
    # Print summary
    print("\nTest Results Summary:")
    for test_name, success in results.items():
        print(f"{test_name}: {'✅ Success' if success else '❌ Failed'}")

if __name__ == "__main__":
    main()
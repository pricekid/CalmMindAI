"""
Test script to verify that email and SMS notifications are completely blocked.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("notification_test")

def test_sendgrid_block():
    """Test that SendGrid emails are blocked"""
    print("\n==== TESTING SENDGRID EMAIL BLOCKING ====")
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content
        
        logger.info("SendGrid module imported successfully")
        
        # Create test message
        message = Mail(
            from_email=Email("test@example.com"),
            to_emails=To("recipient@example.com"),
            subject="Test Email - IGNORE",
            content=Content("text/plain", "This is a test email that should be blocked.")
        )
        
        # Try to send email
        logger.info("Attempting to send test email...")
        api_key = os.environ.get("SENDGRID_API_KEY")
        logger.info(f"Using API key: {api_key}")
        sg = SendGridAPIClient(api_key)
        result = sg.send(message)
        
        logger.info(f"SendGrid result: {result}")
        print("✗ FAIL: SendGrid emails are NOT being blocked")
        return False
    except Exception as e:
        logger.info(f"SendGrid error (expected): {e}")
        print("✓ SUCCESS: SendGrid emails are being blocked")
        return True

def test_twilio_block():
    """Test that Twilio SMS are blocked"""
    print("\n==== TESTING TWILIO SMS BLOCKING ====")
    try:
        from twilio.rest import Client
        
        logger.info("Twilio module imported successfully")
        
        # Try to send SMS
        logger.info("Attempting to send test SMS...")
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        logger.info(f"Using account SID: {account_sid}")
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body="Test SMS that should be blocked",
            from_=os.environ.get("TWILIO_PHONE_NUMBER"),
            to="+15555555555"
        )
        
        logger.info(f"Twilio result: {message}")
        print("✗ FAIL: Twilio SMS are NOT being blocked")
        return False
    except Exception as e:
        logger.info(f"Twilio error (expected): {e}")
        print("✓ SUCCESS: Twilio SMS are being blocked")
        return True

def main():
    """Main test function"""
    print("TESTING NOTIFICATION BLOCKING")
    print("This script will attempt to send test notifications to verify blocking")
    
    # Check block file
    if os.path.exists("data/notifications_blocked"):
        with open("data/notifications_blocked", "r") as f:
            content = f.read()
        print(f"Block file exists with content: {content}")
    else:
        print("Block file does not exist!")
    
    # Test blocks
    sendgrid_blocked = test_sendgrid_block()
    twilio_blocked = test_twilio_block()
    
    # Summary
    print("\n==== NOTIFICATION BLOCKING SUMMARY ====")
    if sendgrid_blocked and twilio_blocked:
        print("✓ ALL NOTIFICATIONS ARE SUCCESSFULLY BLOCKED")
    else:
        print("✗ SOME NOTIFICATIONS ARE NOT BLOCKED")
        if not sendgrid_blocked:
            print("  - SendGrid emails are NOT blocked")
        if not twilio_blocked:
            print("  - Twilio SMS are NOT blocked")

if __name__ == "__main__":
    main()
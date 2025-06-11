#!/usr/bin/env python3
"""
Email deliverability test script for SendGrid integration.
Tests welcome, password reset, and notification emails.
"""

import os
import sys
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sendgrid_connection():
    """Test basic SendGrid API connection"""
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY not found in environment variables")
            return False
        
        sg = SendGridAPIClient(api_key)
        logger.info("SendGrid API key found and initialized")
        return True
    except Exception as e:
        logger.error(f"SendGrid connection failed: {e}")
        return False

def send_test_email(email_type, recipient_email="test@example.com"):
    """Send a test email and log the response"""
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        sg = SendGridAPIClient(api_key)
        
        # Email templates for different types
        templates = {
            "welcome": {
                "subject": "Welcome to Dear Teddy - Test Email",
                "content": """
                <h2>Welcome to Dear Teddy!</h2>
                <p>This is a test welcome email to verify SendGrid deliverability.</p>
                <p>Your mental wellness journey starts here.</p>
                <p>Best regards,<br>The Dear Teddy Team</p>
                """
            },
            "password_reset": {
                "subject": "Password Reset Request - Test Email",
                "content": """
                <h2>Password Reset Request</h2>
                <p>This is a test password reset email to verify SendGrid deliverability.</p>
                <p>Click the link below to reset your password:</p>
                <a href="https://dear-teddy.onrender.com/reset-password?token=test123">Reset Password</a>
                <p>If you didn't request this, please ignore this email.</p>
                """
            },
            "notification": {
                "subject": "Daily Journal Reminder - Test Email",
                "content": """
                <h2>Time for Your Daily Reflection</h2>
                <p>This is a test notification email to verify SendGrid deliverability.</p>
                <p>Take a moment to check in with yourself today.</p>
                <a href="https://dear-teddy.onrender.com/journal">Write in Your Journal</a>
                """
            }
        }
        
        if email_type not in templates:
            logger.error(f"Unknown email type: {email_type}")
            return False
        
        template = templates[email_type]
        
        message = Mail(
            from_email='noreply@dear-teddy.onrender.com',
            to_emails=recipient_email,
            subject=template["subject"],
            html_content=template["content"]
        )
        
        response = sg.send(message)
        
        logger.info(f"✓ {email_type.upper()} EMAIL TEST")
        logger.info(f"  Status Code: {response.status_code}")
        logger.info(f"  Headers: {dict(response.headers)}")
        
        if response.status_code == 202:
            logger.info(f"  Result: SUCCESS - Email accepted by SendGrid")
        else:
            logger.warning(f"  Result: UNEXPECTED STATUS - {response.status_code}")
        
        return response.status_code == 202
        
    except Exception as e:
        logger.error(f"✗ {email_type.upper()} EMAIL TEST FAILED: {e}")
        return False

def main():
    """Run comprehensive email deliverability tests"""
    logger.info("=== DEAR TEDDY EMAIL DELIVERABILITY TEST ===")
    
    # Test SendGrid connection
    if not test_sendgrid_connection():
        logger.error("Cannot proceed without valid SendGrid connection")
        sys.exit(1)
    
    # Test email types
    email_types = ["welcome", "password_reset", "notification"]
    test_email = "test@dearteddy.app"  # Use your domain for testing
    
    results = {}
    for email_type in email_types:
        logger.info(f"\nTesting {email_type} email...")
        results[email_type] = send_test_email(email_type, test_email)
    
    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    success_count = sum(results.values())
    total_count = len(results)
    
    for email_type, success in results.items():
        status = "PASS" if success else "FAIL"
        logger.info(f"{email_type}: {status}")
    
    logger.info(f"Overall: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        logger.info("✓ All email deliverability tests PASSED")
        return 0
    else:
        logger.warning(f"✗ {total_count - success_count} email tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
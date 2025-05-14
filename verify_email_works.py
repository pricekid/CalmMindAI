"""
Script to verify that email functionality is properly working.
This sends a test email to verify the SendGrid integration.
"""
import os
import sys
import logging
from notification_service import send_email, send_test_email

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_sendgrid_configuration():
    """Verify that SendGrid is properly configured."""
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    if not sendgrid_api_key:
        logger.error("SENDGRID_API_KEY environment variable is not set")
        return False
    
    logger.info(f"SendGrid API key found (first 5 chars): {sendgrid_api_key[:5]}...")
    return True

def test_specific_email(email_address):
    """Test sending an email to a specific address."""
    logger.info(f"Sending test email to {email_address}")
    
    result = send_test_email(email_address)
    if result:
        logger.info(f"✓ Successfully sent test email to {email_address}")
        return True
    else:
        logger.error(f"✗ Failed to send test email to {email_address}")
        return False

def test_direct_email(email_address):
    """Test sending an email using the direct send_email function."""
    logger.info(f"Sending direct email to {email_address}")
    
    subject = "Verification Email from Calm Journey"
    html_content = """
    <html>
        <body>
            <h1>Email Verification</h1>
            <p>This is a verification email sent directly from the Calm Journey application.</p>
            <p>If you're seeing this, email functionality has been successfully restored!</p>
        </body>
    </html>
    """
    
    result = send_email(email_address, subject, html_content)
    if result.get('success'):
        logger.info(f"✓ Successfully sent direct email to {email_address}")
        return True
    else:
        logger.error(f"✗ Failed to send direct email to {email_address}: {result.get('error')}")
        return False

def main():
    """Main function to verify email functionality."""
    if not verify_sendgrid_configuration():
        logger.error("SendGrid is not properly configured. Email functionality will not work.")
        return False
    
    if len(sys.argv) < 2:
        logger.error("Usage: python verify_email_works.py <email_address>")
        return False
    
    email_address = sys.argv[1]
    
    # Test both email methods
    test_result = test_specific_email(email_address)
    direct_result = test_direct_email(email_address)
    
    if test_result and direct_result:
        logger.info("✓ All email tests passed! Email functionality is working properly.")
        return True
    else:
        logger.error("✗ Some email tests failed. See above logs for details.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
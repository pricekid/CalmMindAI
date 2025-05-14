"""
Simpler SendGrid test to diagnose email delivery issues.
"""
import os
import logging
import argparse
import time
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SENDER_EMAILS = [
    "dearteddybb@gmail.com",
    "no-reply@dearteddy.com",
    "noreply@replit.app",
    "app-updates@replit.app"
]

def send_test_email(recipient_email, sender_email):
    """Send a test email with the given sender and recipient"""
    try:
        # Get API key
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY environment variable not set")
            return False
        
        # Log API key first characters
        logger.info(f"Using SendGrid API key: {api_key[:5]}...")
        
        # Create a timestamp to track this specific email
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create message
        message = Mail(
            from_email=sender_email,
            to_emails=recipient_email,
            subject=f"SendGrid Test at {timestamp} - From: {sender_email}",
            html_content=f"""
            <h1>SendGrid Test Email</h1>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <p><strong>From:</strong> {sender_email}</p>
            <p><strong>To:</strong> {recipient_email}</p>
            <p>This is a test email to troubleshoot delivery issues.</p>
            """
        )
        
        # Send the email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Log response
        logger.info(f"Email from {sender_email} to {recipient_email} - Status: {response.status_code}")
        
        # Return success if status code is 202 (SendGrid success)
        return response.status_code == 202
        
    except Exception as e:
        logger.error(f"Error sending from {sender_email} to {recipient_email}: {str(e)}")
        return False

def run_tests(recipient_email):
    """Run tests with multiple sender emails"""
    logger.info(f"Starting SendGrid tests for recipient: {recipient_email}")
    
    results = []
    
    for idx, sender_email in enumerate(SENDER_EMAILS):
        logger.info(f"Test {idx+1}/{len(SENDER_EMAILS)}: From {sender_email}")
        success = send_test_email(recipient_email, sender_email)
        results.append({
            "sender": sender_email,
            "success": success
        })
        
        # Add delay between sends
        if idx < len(SENDER_EMAILS) - 1:
            time.sleep(1)
    
    # Display summary
    logger.info("=" * 50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    
    success_count = 0
    for result in results:
        status = "✓ SENT" if result["success"] else "✗ FAILED"
        if result["success"]:
            success_count += 1
        logger.info(f"{status} - From: {result['sender']}")
    
    logger.info("=" * 50)
    logger.info(f"Successful: {success_count}/{len(SENDER_EMAILS)}")
    logger.info("Note: SENT means accepted by SendGrid servers, not necessarily delivered to inbox.")
    logger.info("Please check your inbox and spam folder.")
    logger.info("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SendGrid email tests')
    parser.add_argument('recipient', help='Email address to send test emails to')
    args = parser.parse_args()
    
    run_tests(args.recipient)
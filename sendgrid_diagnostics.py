"""
SendGrid diagnostics script to troubleshoot email delivery issues.
This script tests different combinations of sender emails and recipient domains.
"""
import os
import logging
import time
import argparse
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set of sender emails to test
SENDER_CONFIGS = [
    {"email": "dearteddybb@gmail.com", "name": "Dear Teddy"},
    {"email": "no-reply@dearteddy.com", "name": "Dear Teddy App"},
    {"email": "noreply@replit.app", "name": "Calm Mind App"},
    {"email": "app-updates@replit.app", "name": "Dear Teddy Updates"}
]

def send_test_email(recipient_email, sender_config, verbose=False):
    """Send a test email with a specific sender configuration"""
    try:
        # Get API key
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY environment variable not set")
            return False

        if verbose:
            logger.info(f"Using SendGrid API key: {api_key[:5]}...")
        
        # Create timestamp for tracking
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create a minimal message with the specific sender
        from_email = Email(sender_config["email"], sender_config["name"])
        to_email = To(recipient_email)
        subject = f"SendGrid Test at {timestamp} - From: {sender_config['email']}"
        
        # Create HTML content with diagnostics
        html_content = f"""
        <html>
            <body>
                <h1>SendGrid Test Email</h1>
                <p><strong>Timestamp:</strong> {timestamp}</p>
                <p><strong>From Email:</strong> {sender_config['email']}</p>
                <p><strong>From Name:</strong> {sender_config['name']}</p>
                <p><strong>To Email:</strong> {recipient_email}</p>
                <p>This is a test email to troubleshoot delivery issues. If you received this, please let us know!</p>
            </body>
        </html>
        """
        
        content = Content("text/html", html_content)
        message = Mail(from_email, to_email, subject, content)
        
        # Add category for tracking
        message.add_category("diagnostic-test")
        
        # Send message
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Log response
        logger.info(f"Test email from {sender_config['email']} to {recipient_email} - Status code: {response.status_code}")
        
        if verbose:
            logger.info(f"Response body: {response.body}")
            logger.info(f"Response headers: {response.headers}")
        
        return response.status_code == 202
        
    except Exception as e:
        logger.error(f"Error sending from {sender_config['email']} to {recipient_email}: {str(e)}")
        return False

def run_diagnostics(recipient_email, verbose=False):
    """Run diagnostics with multiple sender configurations"""
    logger.info(f"Starting SendGrid diagnostics for recipient: {recipient_email}")
    logger.info(f"Testing {len(SENDER_CONFIGS)} different sender configurations")
    
    results = []
    
    for idx, sender_config in enumerate(SENDER_CONFIGS):
        logger.info(f"Test {idx+1}/{len(SENDER_CONFIGS)}: From {sender_config['email']}")
        success = send_test_email(recipient_email, sender_config, verbose)
        results.append({
            "sender": sender_config['email'],
            "success": success
        })
        
        # Add delay between requests to avoid rate limits
        if idx < len(SENDER_CONFIGS) - 1:
            time.sleep(2)
    
    # Display summary
    logger.info("=" * 50)
    logger.info("DIAGNOSTICS SUMMARY")
    logger.info("=" * 50)
    
    for result in results:
        status = "✓ SENT" if result["success"] else "✗ FAILED"
        logger.info(f"{status} - From: {result['sender']}")
    
    logger.info("=" * 50)
    logger.info("Note: A status of 'SENT' means the email was accepted by SendGrid's servers.")
    logger.info("It does not guarantee delivery to the recipient's inbox.")
    logger.info("Please check your inbox, spam folder, and email filters.")
    logger.info("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SendGrid email diagnostics')
    parser.add_argument('recipient', help='Email address to send test emails to')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    run_diagnostics(args.recipient, args.verbose)
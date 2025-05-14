"""
Improved direct SendGrid test script with better diagnostics.
This script bypasses the application to directly test SendGrid connectivity.
"""
import os
import logging
import argparse
import time
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_api_key(api_key):
    """Validate the API key format"""
    if not api_key:
        logger.error("No API key provided")
        return False
    
    if not api_key.startswith('SG.'):
        logger.error("API key does not have the expected format (should start with 'SG.')")
        return False
    
    if len(api_key) < 50:  # Typical SendGrid API keys are longer
        logger.warning("API key seems shorter than expected")
        
    return True

def test_sendgrid_direct(recipient_email, verbose=False):
    """
    Test SendGrid directly with improved diagnostics and reporting.
    
    Args:
        recipient_email: The recipient's email address for the test
        verbose: Whether to print verbose diagnostic information
        
    Returns:
        bool: Whether the test was successful
    """
    try:
        # Get API key from environment
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not validate_api_key(api_key):
            return False
        
        logger.info(f"Using SendGrid API key: {api_key[:5]}...")
        
        if verbose:
            logger.info(f"API key length: {len(api_key)} characters")
            logger.info(f"Testing connection to SendGrid...")
        
        # Create a minimal message
        from_email = Email("dearteddybb@gmail.com", "Dear Teddy")
        to_email = To(recipient_email)
        subject = "SendGrid Direct Test"
        content = Content(
            "text/html", 
            f"""
            <html>
                <body>
                    <h1>SendGrid Test</h1>
                    <p>This is a direct test of the SendGrid API sent at {time.strftime('%Y-%m-%d %H:%M:%S')}.</p>
                    <p>If you're receiving this email, the SendGrid integration is working correctly!</p>
                </body>
            </html>
            """
        )
        message = Mail(from_email, to_email, subject, content)
        
        # Add category for tracking
        message.category = "test"
        
        # Create SendGrid client and send
        if verbose:
            logger.info(f"Creating SendGrid client...")
            
        sg = SendGridAPIClient(api_key)
        
        if verbose:
            logger.info(f"Sending test email to {recipient_email}...")
            
        # Send the email and get the response
        start_time = time.time()
        response = sg.send(message)
        end_time = time.time()
        
        # Log the response details
        logger.info(f"Email sent in {end_time - start_time:.2f} seconds")
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers if verbose else {k: response.headers[k] for k in ['X-Message-Id'] if k in response.headers}}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

def main():
    """Main function to run the test"""
    parser = argparse.ArgumentParser(description='Test SendGrid integration')
    parser.add_argument('recipient', help='Email address to send the test to')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    success = test_sendgrid_direct(args.recipient, args.verbose)
    if success:
        logger.info("✅ SendGrid test completed successfully!")
        return 0
    else:
        logger.error("❌ SendGrid test failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
"""
Direct SendGrid test to check if the API key is working properly.
This script bypasses all the application code and uses SendGrid directly.
"""
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sendgrid_direct(recipient_email="teddy.leon@alumni.uwi.edu"):
    """Test SendGrid directly with minimal code."""
    try:
        # Get API key
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY environment variable not set")
            return False
        
        logger.info(f"Using SendGrid API key: {api_key[:5]}...")
        
        # Create a minimal message
        message = Mail(
            from_email='dearteddybb@gmail.com',
            to_emails=recipient_email,
            subject='Simple SendGrid Test',
            plain_text_content='This is a direct test of the SendGrid API'
        )
        
        # Send message
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Check response
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response body: {response.body}")
        logger.info(f"Response headers: {response.headers}")
        
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_sendgrid_direct()
    print(f"Test {'succeeded' if success else 'failed'}")
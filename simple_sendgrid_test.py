"""
Simplified SendGrid test script with minimal dependencies.
"""
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_sendgrid(recipient_email):
    """
    Test SendGrid with minimal code.
    """
    try:
        # Get API key
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logging.error("No SendGrid API key found in environment")
            return False
            
        logging.info(f"Using SendGrid API key: {api_key[:5]}...")
        
        # Create a simple message
        message = Mail(
            from_email='dearteddybb@gmail.com',
            to_emails=recipient_email,
            subject='Basic SendGrid Test',
            html_content='<p>This is a simple test of the SendGrid API</p>'
        )
        
        # Send message
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        logging.info(f"Email sent with status code: {response.status_code}")
        return True
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_sendgrid_test.py <recipient_email>")
        sys.exit(1)
        
    recipient = sys.argv[1]
    success = test_sendgrid(recipient)
    
    if success:
        logging.info("✅ SendGrid test successful!")
        sys.exit(0)
    else:
        logging.error("❌ SendGrid test failed")
        sys.exit(1)
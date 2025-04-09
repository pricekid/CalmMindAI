"""
Simple test script to verify Gmail SMTP authentication without Flask dependencies.
"""
import os
import sys
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gmail_auth():
    """Test Gmail SMTP authentication with the provided credentials."""
    mail_server = 'smtp.gmail.com'
    mail_port = 587
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_sender = os.environ.get('MAIL_DEFAULT_SENDER')
    
    if not mail_username or not mail_password:
        logger.error("Missing MAIL_USERNAME or MAIL_PASSWORD environment variables")
        print("Error: Missing Gmail credentials in environment variables")
        return False
    
    logger.info(f"Testing SMTP auth for {mail_username} on {mail_server}:{mail_port}")
    logger.info(f"Mail sender: {mail_sender or 'Not set'}")
    
    try:
        # Connect to the mail server
        server = smtplib.SMTP(mail_server, mail_port)
        server.set_debuglevel(1)  # Enable debug output
        server.ehlo()  # Identify ourselves to the server
        server.starttls()  # Secure the connection
        server.ehlo()  # Re-identify ourselves over TLS connection
        
        # Attempt to log in
        logger.info("Attempting to log in...")
        server.login(mail_username, mail_password)
        
        logger.info("Login successful!")
        
        # If a test email should be sent
        if len(sys.argv) > 1:
            recipient = sys.argv[1]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = mail_sender or mail_username
            msg['To'] = recipient
            msg['Subject'] = 'Calm Journey - Gmail Auth Test'
            
            body = "This is a test email to verify Gmail SMTP authentication is working correctly."
            msg.attach(MIMEText(body, 'plain'))
            
            # Send the message
            logger.info(f"Sending test email to {recipient}")
            server.sendmail(msg['From'], recipient, msg.as_string())
            logger.info("Test email sent successfully")
        
        # Close the connection
        server.quit()
        
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {str(e)}")
        print(f"Error: Gmail authentication failed - {str(e)}")
        return False
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gmail_auth()
    if success:
        print("Gmail authentication successful")
        sys.exit(0)
    else:
        print("Gmail authentication failed")
        sys.exit(1)
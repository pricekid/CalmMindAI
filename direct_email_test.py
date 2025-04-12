"""
Test script to send email directly using environment variables.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_direct_email(recipient_email):
    """
    Send an email directly using environment variables, bypassing Flask config.
    """
    # Get email configuration directly from environment
    mail_server = "smtp.gmail.com"  # Using Gmail as server
    mail_port = 587  # TLS port for Gmail
    mail_use_tls = True
    
    # These should be available in the environment
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_sender = os.environ.get('MAIL_DEFAULT_SENDER')
    
    logger.info(f"Email Configuration:")
    logger.info(f"MAIL_SERVER: {mail_server}")
    logger.info(f"MAIL_PORT: {mail_port}")
    logger.info(f"MAIL_USERNAME: {mail_username}")
    logger.info(f"MAIL_PASSWORD: {'********' if mail_password else 'Not set'}")
    logger.info(f"MAIL_DEFAULT_SENDER: {mail_sender}")
    
    # Check if we have the necessary credentials
    if not all([mail_server, mail_port, mail_username, mail_password, mail_sender]):
        missing = []
        if not mail_server: missing.append("MAIL_SERVER")
        if not mail_port: missing.append("MAIL_PORT")
        if not mail_username: missing.append("MAIL_USERNAME")
        if not mail_password: missing.append("MAIL_PASSWORD")
        if not mail_sender: missing.append("MAIL_DEFAULT_SENDER")
        
        error_msg = f"Missing mail configuration: {', '.join(missing)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    # Create the email message
    subject = "Calm Journey - Direct Email Test"
    html_body = """
    <html>
    <body>
        <h2>Calm Journey - Direct Email Test</h2>
        <p>This is a test email using direct SMTP connection with environment variables.</p>
        <p>If you're seeing this, it means the email configuration is working correctly!</p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
    </body>
    </html>
    """
    text_body = "Calm Journey - Direct Email Test\n\nThis is a test email using direct SMTP connection with environment variables.\nIf you're seeing this, it means the email configuration is working correctly!"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_sender
    message["To"] = recipient_email
    
    # Add text and HTML parts
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))
    
    try:
        # Connect to the mail server with timeout
        logger.info(f"Connecting to mail server {mail_server}:{mail_port}...")
        server = smtplib.SMTP(mail_server, mail_port, timeout=15)  # 15 second timeout
        
        if mail_use_tls:
            server.starttls()
        
        # Log in to the mail server
        logger.info(f"Logging in to mail server as {mail_username}...")
        server.login(mail_username, mail_password)
        
        # Send the email
        logger.info(f"Sending email to {recipient_email} with subject '{subject}'...")
        server.sendmail(mail_sender, recipient_email, message.as_string())
        
        # Close the connection properly
        server.quit()
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return {"success": True}
    
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication Error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    except smtplib.SMTPException as e:
        error_msg = f"SMTP Error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error sending email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    # Get email address from input
    recipient = input("Enter email address to send test to: ")
    if recipient:
        print(f"Sending test email to {recipient}...")
        result = send_direct_email(recipient)
        
        if result["success"]:
            print("✅ Email sent successfully!")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    else:
        print("No email address provided. Exiting.")
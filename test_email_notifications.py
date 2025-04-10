"""
Simple script to test email notifications with robust error handling.
Use this to test email functionality without restarting the main app.
"""
import os
import sys
import logging
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mail_config():
    """
    Get email configuration directly from environment variables.
    """
    mail_config = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': True,
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER')
    }
    
    return mail_config

def send_test_email(recipient_email, verbose=False):
    """
    Send a test email with improved error handling.
    
    Args:
        recipient_email: The email address to send the test to
        verbose: Whether to print verbose logs
    
    Returns:
        dict: Result with success flag and error message if applicable
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    # Get email configuration from environment
    mail_config = get_mail_config()
    
    mail_server = mail_config['MAIL_SERVER']
    mail_port = mail_config['MAIL_PORT']
    mail_use_tls = mail_config['MAIL_USE_TLS']
    mail_username = mail_config['MAIL_USERNAME']
    mail_password = mail_config['MAIL_PASSWORD']
    mail_sender = mail_config['MAIL_DEFAULT_SENDER']
    
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
    
    # Log configuration
    if verbose:
        logger.info(f"Mail configuration:")
        logger.info(f"MAIL_SERVER: {mail_server}")
        logger.info(f"MAIL_PORT: {mail_port}")
        logger.info(f"MAIL_USE_TLS: {mail_use_tls}")
        logger.info(f"MAIL_USERNAME: {'Set' if mail_username else 'Not set'}")
        logger.info(f"MAIL_PASSWORD: {'Set' if mail_password else 'Not set'}")
        logger.info(f"MAIL_DEFAULT_SENDER: {mail_sender}")
    
    # Create the email message
    subject = "Calm Journey - Email Test (Direct Send)"
    html_body = """
    <html>
    <body>
        <h2>Calm Journey - Email Test (Direct Send)</h2>
        <p>This is a test email using direct SMTP connection.</p>
        <p>If you're seeing this, it means the configuration is working correctly!</p>
        <p>The URL in this email should also be correct: <a href="https://calm-mind-ai-naturalarts.replit.app/journal/new">Click here to open the journal page</a></p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
    </body>
    </html>
    """
    text_body = "Calm Journey - Email Test (Direct Send)\n\nThis is a test email using direct SMTP connection.\nIf you're seeing this, it means the configuration is working correctly!\n\nVisit https://calm-mind-ai-naturalarts.replit.app/journal/new to open the journal page."
    
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
        if mail_use_tls:
            server = smtplib.SMTP(mail_server, mail_port, timeout=15)  # 15 second timeout
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=15)  # 15 second timeout
        
        # Log in to the mail server
        logger.info(f"Logging in to mail server as {mail_username}...")
        server.login(mail_username, mail_password)
        
        # Send the email with a timeout
        logger.info(f"Sending email to {recipient_email} with subject '{subject}'...")
        try:
            server.sendmail(mail_sender, recipient_email, message.as_string())
            # Close the connection properly
            server.quit()
        except Exception as e:
            # Make sure to close the connection even if there's an error
            try:
                server.quit()
            except:
                pass
            raise e  # Re-raise the original exception
        
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

def main():
    parser = argparse.ArgumentParser(description='Test email notifications for Calm Journey')
    parser.add_argument('email', nargs='?', help='Email address to send test message to')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if not args.email:
        parser.print_help()
        return
    
    print(f"Sending test email to {args.email}...")
    result = send_test_email(args.email, args.verbose)
    
    if result.get("success"):
        print(f"\n✓ Success! Email sent successfully to {args.email}")
        print("Please check your inbox (and spam folder) for the test email.")
    else:
        print(f"\n✗ Error: Failed to send email: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
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

def send_direct_email(recipient_email, subject=None, message_content=None):
    """
    Send an email directly using environment variables, bypassing Flask config.
    
    Args:
        recipient_email: The recipient's email address
        subject: Optional custom subject for the email
        message_content: Optional custom message content
    """
    # Get email configuration directly from environment
    mail_server = "smtp.gmail.com"  # Using Gmail as server
    mail_port = 587  # TLS port for Gmail
    mail_use_tls = True
    
    # These should be available in the environment
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_sender = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Print environment variables for debugging (without showing full password)
    print(f"Environment variables:")
    print(f"  MAIL_USERNAME present: {'Yes' if mail_username else 'No'}")
    print(f"  MAIL_PASSWORD present: {'Yes' if mail_password else 'No'}")
    print(f"  MAIL_DEFAULT_SENDER present: {'Yes' if mail_sender else 'No'}")
    
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
    
    # Create the email message with custom content if provided
    email_subject = subject if subject else "Calm Journey - Direct Email Test"
    
    custom_content = ""
    if message_content:
        custom_content = f"""
        <div style="margin: 20px 0; padding: 15px; background-color: #f0f7f7; border-left: 4px solid #5f9ea0; border-radius: 3px;">
            <p>{message_content}</p>
        </div>
        """
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="color: #5f9ea0; margin: 0;">Calm Journey</h1>
            <p style="font-size: 18px; margin: 5px 0 0;">Email Test</p>
        </div>
        
        <div style="padding: 20px; background-color: #fff; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #5f9ea0; border-bottom: 1px solid #eee; padding-bottom: 10px;">Email Delivery Test</h2>
            
            {custom_content}
            
            <p>This is a test email using direct SMTP connection with environment variables.</p>
            <p>If you're seeing this, it means the email configuration is working correctly!</p>
            
            <p style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
                This is an automated test message.
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
            <p>The Calm Journey Team</p>
        </div>
    </body>
    </html>
    """
    
    custom_text = f"{message_content}\n\n" if message_content else ""
    text_body = f"Calm Journey - Email Test\n\n{custom_text}This is a test email using direct SMTP connection with environment variables.\nIf you're seeing this, it means the email configuration is working correctly!"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = email_subject
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
        logger.info(f"Sending email to {recipient_email} with subject '{email_subject}'...")
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
    import sys
    
    # Check if email was provided as command line argument
    if len(sys.argv) >= 2:
        recipient = sys.argv[1]
        
        # Custom subject and message if provided
        custom_subject = None
        custom_message = None
        
        if len(sys.argv) >= 3:
            custom_subject = sys.argv[2]
        
        if len(sys.argv) >= 4:
            custom_message = sys.argv[3]
        
        print(f"Sending test email to {recipient}...")
        if custom_subject:
            print(f"Subject: {custom_subject}")
        if custom_message:
            print(f"Message: {custom_message}")
            
        print("\nChecking email configuration...")
        result = send_direct_email(recipient, custom_subject, custom_message)
        
        if result["success"]:
            print("\n✅ Email sent successfully!")
            print("* This doesn't guarantee delivery to inbox - check spam folder if not received")
            print("* Some email providers may delay or filter messages from external services")
            print("* Gmail addresses are generally more reliable for testing")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
    else:
        print("Usage: python3 direct_email_test.py [email_address] [optional_subject] [optional_message]")
        print("Example: python3 direct_email_test.py user@example.com \"Test Subject\" \"This is a test message\"")
"""
Script to fix email notifications by creating a custom email configuration loader 
that directly reads from environment variables.
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask
from app import app, db, mail
from models import User

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mail_config():
    """
    Get email configuration directly from environment variables rather than app config.
    
    This is a workaround for when Flask's app.config doesn't properly pick up the environment variables.
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

def direct_send_email(recipient, subject, html_body, text_body=None):
    """
    Send an email bypassing Flask-Mail and working directly with SMTP.
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject
        html_body: HTML content of the email
        text_body: Plain text content of the email (optional)
    
    Returns:
        dict: Result with success flag and error message if applicable
    """
    # Get email configuration directly from environment
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
    logger.info(f"Mail configuration for direct send:")
    logger.info(f"MAIL_SERVER: {mail_server}")
    logger.info(f"MAIL_PORT: {mail_port}")
    logger.info(f"MAIL_USE_TLS: {mail_use_tls}")
    logger.info(f"MAIL_USERNAME: {'Set' if mail_username else 'Not set'}")
    logger.info(f"MAIL_PASSWORD: {'Set' if mail_password else 'Not set'}")
    logger.info(f"MAIL_DEFAULT_SENDER: {mail_sender}")
    
    # Create the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_sender
    message["To"] = recipient
    
    # Add text and HTML parts
    if text_body:
        message.attach(MIMEText(text_body, "plain"))
    if html_body:
        message.attach(MIMEText(html_body, "html"))
    
    try:
        # Connect to the mail server with timeout
        if mail_use_tls:
            server = smtplib.SMTP(mail_server, mail_port, timeout=10)  # 10 second timeout
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)  # 10 second timeout
        
        # Log in to the mail server
        logger.debug(f"Attempting to log in to mail server {mail_server}:{mail_port} as {mail_username}")
        server.login(mail_username, mail_password)
        
        # Send the email with a timeout
        logger.info(f"Sending email to {recipient} with subject '{subject}'")
        try:
            server.sendmail(mail_sender, recipient, message.as_string())
            # Close the connection properly
            server.quit()
        except Exception as e:
            # Make sure to close the connection even if there's an error
            try:
                server.quit()
            except:
                pass
            raise e  # Re-raise the original exception
        
        logger.info(f"Email sent successfully to {recipient}")
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

def send_immediate_test_email(email_address):
    """
    Send a test email to a specific email address using the direct method.
    
    Args:
        email_address: Email address to send the test to
    
    Returns:
        dict: Result with success flag and error message if applicable
    """
    subject = "Calm Journey - Email Test (Direct Send)"
    html_body = """
    <html>
    <body>
        <h2>Calm Journey - Email Test (Direct Send)</h2>
        <p>This is a test email using direct SMTP connection, bypassing Flask-Mail.</p>
        <p>If you're seeing this, it means the configuration is working!</p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
    </body>
    </html>
    """
    text_body = "Calm Journey - Email Test (Direct Send)\n\nThis is a test email using direct SMTP connection, bypassing Flask-Mail.\nIf you're seeing this, it means the configuration is working!"
    
    return direct_send_email(email_address, subject, html_body, text_body)

def send_notification_to_all_users():
    """
    Send a notification to all users with notifications enabled using the direct method.
    
    Returns:
        dict: Statistics about the notification sending process
    """
    with app.app_context():
        # Get all users with notifications enabled
        users = User.query.filter_by(notifications_enabled=True).all()
        
        if not users:
            logger.info("No users found with notifications enabled.")
            return {"success": 0, "errors": 0}
        
        logger.info(f"Sending notifications to {len(users)} users...")
        
        success_count = 0
        error_count = 0
        
        # Use the correct Replit URL
        base_url = "https://calm-mind-ai-naturalarts.replit.app"
        journal_url = f"{base_url}/journal/new"
        
        for user in users:
            subject = 'Special Reminder: Take a Moment to Journal - Calm Journey'
            html_body = f"""
            <html>
            <body>
                <h2>Hello {user.username}!</h2>
                <p>This is a special reminder to take a moment for yourself today.</p>
                <p>Writing in your journal can help you process your thoughts and feelings, reduce stress, and gain clarity.</p>
                <p>We encourage you to spend just 5 minutes today writing about what's on your mind.</p>
                <p><a href="{journal_url}" style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px;">Start Writing Now</a></p>
                <p>Regular notifications will continue at your preferred time.</p>
                <p>Wishing you a peaceful day,<br>The Calm Journey Team</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Hello {user.username}!
            
            This is a special reminder to take a moment for yourself today.
            
            Writing in your journal can help you process your thoughts and feelings, reduce stress, and gain clarity.
            
            We encourage you to spend just 5 minutes today writing about what's on your mind.
            
            Visit {journal_url} to start writing now.
            
            Regular notifications will continue at your preferred time.
            
            Wishing you a peaceful day,
            The Calm Journey Team
            """
            
            try:
                result = direct_send_email(user.email, subject, html_body, text_body)
                
                if result.get("success"):
                    success_count += 1
                    logger.info(f"Sent notification to {user.email}")
                else:
                    error_count += 1
                    logger.error(f"Failed to send notification to {user.email}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                error_count += 1
                logger.error(f"Unexpected error sending to {user.email}: {str(e)}", exc_info=True)
        
        logger.info(f"Notification sending complete. Success: {success_count}, Errors: {error_count}")
        return {"success": success_count, "errors": error_count}

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_email_notifications.py test <email>  - Send test email")
        print("  python fix_email_notifications.py send-all      - Send to all users")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "test" and len(sys.argv) > 2:
        email = sys.argv[2]
        print(f"Sending test email to {email}...")
        result = send_immediate_test_email(email)
        
        if result.get("success"):
            print(f"Email sent successfully to {email}")
        else:
            print(f"Failed to send email: {result.get('error', 'Unknown error')}")
            
    elif command == "send-all":
        print("Sending emails to all users with notifications enabled...")
        with app.app_context():
            result = send_notification_to_all_users()
            print(f"Sent {result.get('success', 0)} emails successfully")
            print(f"Failed to send {result.get('errors', 0)} emails")
    else:
        print("Unknown command")
        print("Usage:")
        print("  python fix_email_notifications.py test <email>  - Send test email")
        print("  python fix_email_notifications.py send-all      - Send to all users")
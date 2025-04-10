"""
Improved email service with better error handling and reliable delivery.
This replaces the basic email functionality with more robust error handling.
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_email(recipient, subject, html_body, text_body=None):
    """
    Send an email with robust error handling.
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject
        html_body: HTML content of the email
        text_body: Plain text content of the email (optional)
    
    Returns:
        dict: Result with success flag and error message if applicable
    """
    # Get email configuration from app config
    mail_server = current_app.config.get('MAIL_SERVER') or os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = int(current_app.config.get('MAIL_PORT') or os.environ.get('MAIL_PORT', 587))
    mail_use_tls = current_app.config.get('MAIL_USE_TLS', True)
    mail_username = current_app.config.get('MAIL_USERNAME') or os.environ.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD') or os.environ.get('MAIL_PASSWORD')
    mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_DEFAULT_SENDER')
    
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

def send_test_email(recipient_email):
    """
    Send a test email to verify the email configuration.
    
    Args:
        recipient_email: Email address to send the test to
    
    Returns:
        bool: True if successful, False otherwise
    """
    subject = "Calm Journey - Email Test"
    html_body = """
    <html>
    <body>
        <h2>Calm Journey - Email Configuration Test</h2>
        <p>This is a test email to verify that the email configuration is working correctly.</p>
        <p>If you're seeing this, it means the configuration is valid!</p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
    </body>
    </html>
    """
    text_body = "Calm Journey - Email Configuration Test\n\nThis is a test email to verify that the email configuration is working correctly.\nIf you're seeing this, it means the configuration is valid!"
    
    logger.info(f"Sending test email to {recipient_email}")
    result = send_email(recipient_email, subject, html_body, text_body)
    
    if result.get("success"):
        logger.info(f"Test email sent successfully to {recipient_email}")
        return True
    else:
        logger.error(f"Failed to send test email: {result.get('error', 'Unknown error')}")
        return False

def send_immediate_notification_to_all_users():
    """
    Send an immediate notification to all users with notifications enabled.
    
    Returns:
        dict: Statistics about the notification sending process
    """
    from app import app, db
    from models import User
    
    with app.app_context():
        # Get all users with notifications enabled
        users = User.query.filter_by(notifications_enabled=True).all()
        
        if not users:
            logger.info("No users found with notifications enabled.")
            return {"success": 0, "errors": 0}
        
        logger.info(f"Sending notifications to {len(users)} users...")
        
        success_count = 0
        error_count = 0
        
        # Get the base URL from the app configuration or use a default replit URL
        if 'BASE_URL' in current_app.config and current_app.config['BASE_URL']:
            base_url = current_app.config['BASE_URL']
            journal_url = f"{base_url}/journal/new"
        else:
            # For deployed apps, use the REPL_ID to ensure we get the correct URL
            repl_id = os.environ.get('REPL_ID', None)
            repl_owner = os.environ.get('REPL_OWNER', None)
            
            # Use the correct Replit URL
            journal_url = "https://calm-mind-ai-naturalarts.replit.app/journal/new"
        
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
                result = send_email(user.email, subject, html_body, text_body)
                
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
    from app import app
    
    if len(sys.argv) > 1:
        # If an email is provided, send a test email
        test_email = sys.argv[1]
        with app.app_context():
            send_test_email(test_email)
    else:
        # Otherwise, send notifications to all users
        with app.app_context():
            send_immediate_notification_to_all_users()
"""
Script to fix email notifications by creating a custom email configuration loader 
that directly reads from environment variables.
"""
import os
import smtplib
import logging
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')

def load_users():
    """Load users from the data/users.json file"""
    ensure_data_directory()
    if not os.path.exists('data/users.json'):
        return []
    
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Error decoding users.json file")
        return []
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

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
    
    # Create the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_sender
    message["To"] = recipient
    
    # Add text and HTML parts
    if text_body:
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
        logger.info(f"Sending email to {recipient} with subject '{subject}'...")
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
    subject = "Calm Journey - Email Test"
    html_body = """
    <html>
    <body>
        <h2>Calm Journey - Email Test</h2>
        <p>This is a test email sent using the direct method.</p>
        <p>If you're seeing this email, it means the direct email sending is working correctly!</p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
    </body>
    </html>
    """
    text_body = "Calm Journey - Email Test\n\nThis is a test email sent using the direct method.\nIf you're seeing this email, it means the direct email sending is working correctly!"
    
    return direct_send_email(
        recipient=email_address,
        subject=subject,
        html_body=html_body,
        text_body=text_body
    )

def send_notification_to_all_users():
    """
    Send a notification to all users with notifications enabled using the direct method.
    
    Returns:
        dict: Statistics about the notification sending process
    """
    users = load_users()
    sent_count = 0
    failed_count = 0
    skipped_count = 0
    
    for user in users:
        # Skip users who have disabled notifications
        if not user.get('notifications_enabled', False):
            skipped_count += 1
            continue
        
        # Get the user's email
        email = user.get('email')
        if not email:
            skipped_count += 1
            continue
        
        # Send the notification
        subject = "Calm Journey - Daily Wellness Reminder"
        html_body = f"""
        <html>
        <body>
            <h2>Calm Journey - Daily Wellness Reminder</h2>
            <p>Hello {user.get('username', 'there')}!</p>
            <p>This is your daily reminder to take a moment for yourself and check in with your mental well-being.</p>
            <p>We'd love to hear how you're doing today. Consider spending just 5 minutes journaling about your thoughts and feelings.</p>
            <p><a href="https://calm-mind-ai-naturalarts.replit.app/journal/new">Click here to create a new journal entry</a></p>
            <hr>
            <p><em>The Calm Journey Team</em></p>
            <p style="font-size: 0.8em; color: #666;">
                You received this email because you enabled notifications in your Calm Journey account.
                If you'd like to unsubscribe, please update your notification preferences in your account settings.
            </p>
        </body>
        </html>
        """
        text_body = f"""Calm Journey - Daily Wellness Reminder

Hello {user.get('username', 'there')}!

This is your daily reminder to take a moment for yourself and check in with your mental well-being.

We'd love to hear how you're doing today. Consider spending just 5 minutes journaling about your thoughts and feelings.

Visit https://calm-mind-ai-naturalarts.replit.app/journal/new to create a new journal entry.

The Calm Journey Team

--
You received this email because you enabled notifications in your Calm Journey account.
If you'd like to unsubscribe, please update your notification preferences in your account settings.
"""
        
        result = direct_send_email(
            recipient=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        
        if result.get('success', False):
            sent_count += 1
        else:
            failed_count += 1
            logger.error(f"Failed to send notification to {email}: {result.get('error', 'Unknown error')}")
    
    stats = {
        'total_users': len(users),
        'sent_count': sent_count,
        'failed_count': failed_count,
        'skipped_count': skipped_count,
        'timestamp': datetime.now().isoformat()
    }
    
    return stats

def main():
    """Main function to test email functionality"""
    print("Email Notification Fix Script")
    print("-----------------------------")
    print("1. Send a test email to a specific address")
    print("2. Send notifications to all eligible users")
    print("3. Check email configuration")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '1':
        email = input("Enter the email address to send the test to: ")
        if not email:
            print("No email address provided. Exiting.")
            return
        
        print(f"Sending test email to {email}...")
        result = send_immediate_test_email(email)
        
        if result.get('success', False):
            print(f"✅ Success! Email sent to {email}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    elif choice == '2':
        print("Sending notifications to all eligible users...")
        stats = send_notification_to_all_users()
        
        print("\nNotification Statistics:")
        print(f"Total users: {stats['total_users']}")
        print(f"Emails sent: {stats['sent_count']}")
        print(f"Emails failed: {stats['failed_count']}")
        print(f"Users skipped (notifications disabled): {stats['skipped_count']}")
    
    elif choice == '3':
        mail_config = get_mail_config()
        
        print("\nEmail Configuration:")
        print(f"MAIL_SERVER: {mail_config['MAIL_SERVER']}")
        print(f"MAIL_PORT: {mail_config['MAIL_PORT']}")
        print(f"MAIL_USE_TLS: {mail_config['MAIL_USE_TLS']}")
        print(f"MAIL_USERNAME: {'Set' if mail_config['MAIL_USERNAME'] else 'Not set'}")
        print(f"MAIL_PASSWORD: {'Set' if mail_config['MAIL_PASSWORD'] else 'Not set'}")
        print(f"MAIL_DEFAULT_SENDER: {mail_config['MAIL_DEFAULT_SENDER']}")
        
        if not all([
            mail_config['MAIL_SERVER'],
            mail_config['MAIL_PORT'],
            mail_config['MAIL_USERNAME'],
            mail_config['MAIL_PASSWORD'],
            mail_config['MAIL_DEFAULT_SENDER']
        ]):
            print("\n❌ Warning: Some required email configuration is missing!")
        else:
            print("\n✅ All required email configuration is present.")
    
    elif choice == '4':
        print("Exiting...")
        return
    
    else:
        print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
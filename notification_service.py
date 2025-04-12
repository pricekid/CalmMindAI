"""
Notification service for sending email notifications to users.
This file replaces the Flask-Mail implementation with a direct SMTP implementation
to solve environment variable access issues.
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

def send_email(recipient, subject, html_body, text_body=None):
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
    
    # Debug log the mail configuration
    logger.debug(f"Mail configuration:")
    logger.debug(f"MAIL_SERVER: {mail_server}")
    logger.debug(f"MAIL_PORT: {mail_port}")
    logger.debug(f"MAIL_USERNAME: {'Set' if mail_username else 'Not set'}")
    logger.debug(f"MAIL_PASSWORD: {'Set' if mail_password else 'Not set'}")
    logger.debug(f"MAIL_DEFAULT_SENDER: {'Set' if mail_sender else 'Not set'}")
    
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

def send_test_email(recipient_email):
    """
    Send a test email to verify the email configuration.
    
    Args:
        recipient_email: Email address to send the test to
    
    Returns:
        bool: True if successful, False otherwise
    """
    subject = "Calm Journey - Test Email"
    html_body = """
    <html>
    <body>
        <h2>Calm Journey - Test Email</h2>
        <p>This is a test email to verify that the email notification system is working correctly.</p>
        <p>If you're seeing this email, it means the notification system is configured properly!</p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
    </body>
    </html>
    """
    text_body = "Calm Journey - Test Email\n\nThis is a test email to verify that the email notification system is working correctly.\nIf you're seeing this email, it means the notification system is configured properly!"
    
    result = send_email(recipient_email, subject, html_body, text_body)
    return result.get('success', False)

def send_login_link(email, link):
    """
    Send a login link to a user.
    
    Args:
        email: The user's email address
        link: The login link
    
    Returns:
        bool: True if successful, False otherwise
    """
    subject = "Calm Journey - Your Login Link"
    html_body = f"""
    <html>
    <body>
        <h2>Calm Journey - Your Login Link</h2>
        <p>Hello!</p>
        <p>You requested a login link for Calm Journey. Click the link below to log in:</p>
        <p><a href="{link}">{link}</a></p>
        <p>This link will expire in 10 minutes.</p>
        <p>If you didn't request this link, you can safely ignore this email.</p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
    </body>
    </html>
    """
    text_body = f"""Calm Journey - Your Login Link

Hello!

You requested a login link for Calm Journey. Use the link below to log in:

{link}

This link will expire in 10 minutes.

If you didn't request this link, you can safely ignore this email.

The Calm Journey Team"""
    
    result = send_email(email, subject, html_body, text_body)
    return result.get('success', False)

def send_daily_reminder(user):
    """
    Send a daily reminder to a user.
    
    Args:
        user: Dictionary containing user information
    
    Returns:
        bool: True if successful, False otherwise
    """
    email = user.get('email')
    username = user.get('username', 'there')
    
    if not email:
        logger.error(f"Cannot send reminder: No email for user {username}")
        return False
    
    subject = "Calm Journey - Daily Wellness Reminder"
    html_body = f"""
    <html>
    <body>
        <h2>Calm Journey - Daily Wellness Reminder</h2>
        <p>Hello {username}!</p>
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

Hello {username}!

This is your daily reminder to take a moment for yourself and check in with your mental well-being.

We'd love to hear how you're doing today. Consider spending just 5 minutes journaling about your thoughts and feelings.

Visit https://calm-mind-ai-naturalarts.replit.app/journal/new to create a new journal entry.

The Calm Journey Team

--
You received this email because you enabled notifications in your Calm Journey account.
If you'd like to unsubscribe, please update your notification preferences in your account settings.
"""
    
    result = send_email(email, subject, html_body, text_body)
    return result.get('success', False)

def send_weekly_summary(user, stats):
    """
    Send a weekly summary to a user.
    
    Args:
        user: Dictionary containing user information
        stats: Dictionary containing weekly stats
    
    Returns:
        bool: True if successful, False otherwise
    """
    email = user.get('email')
    username = user.get('username', 'there')
    
    if not email:
        logger.error(f"Cannot send summary: No email for user {username}")
        return False
    
    subject = "Calm Journey - Your Weekly Wellness Summary"
    html_body = f"""
    <html>
    <body>
        <h2>Calm Journey - Your Weekly Wellness Summary</h2>
        <p>Hello {username}!</p>
        <p>Here's a summary of your wellness journey for the past week:</p>
        <ul>
            <li><strong>Journal Entries:</strong> {stats.get('entries', 0)}</li>
            <li><strong>Average Anxiety Level:</strong> {stats.get('avg_anxiety', 'N/A')}</li>
            <li><strong>Most Common Pattern:</strong> {stats.get('common_pattern', 'None identified')}</li>
        </ul>
        <p>Thank you for continuing your wellness journey with us. Remember, every step you take toward self-awareness is a step toward better mental health.</p>
        <p><a href="https://calm-mind-ai-naturalarts.replit.app/journal">View Your Journal History</a></p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
        <p style="font-size: 0.8em; color: #666;">
            You received this email because you enabled notifications in your Calm Journey account.
            If you'd like to unsubscribe, please update your notification preferences in your account settings.
        </p>
    </body>
    </html>
    """
    text_body = f"""Calm Journey - Your Weekly Wellness Summary

Hello {username}!

Here's a summary of your wellness journey for the past week:

- Journal Entries: {stats.get('entries', 0)}
- Average Anxiety Level: {stats.get('avg_anxiety', 'N/A')}
- Most Common Pattern: {stats.get('common_pattern', 'None identified')}

Thank you for continuing your wellness journey with us. Remember, every step you take toward self-awareness is a step toward better mental health.

Visit https://calm-mind-ai-naturalarts.replit.app/journal to view your journal history.

The Calm Journey Team

--
You received this email because you enabled notifications in your Calm Journey account.
If you'd like to unsubscribe, please update your notification preferences in your account settings.
"""
    
    result = send_email(email, subject, html_body, text_body)
    return result.get('success', False)

def send_immediate_notification_to_all_users():
    """
    Send an immediate notification to all users with notifications enabled.
    
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
        
        # Send a notification
        if send_daily_reminder(user):
            sent_count += 1
        else:
            failed_count += 1
    
    stats = {
        'total_users': len(users),
        'sent_count': sent_count,
        'failed_count': failed_count,
        'skipped_count': skipped_count,
        'timestamp': datetime.now().isoformat()
    }
    
    return stats
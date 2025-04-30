"""
Notification service for sending email notifications to users.
This file replaces the Flask-Mail implementation with a direct SMTP implementation
to solve environment variable access issues.
"""
import os
import smtplib
import logging
import check_notifications_blocked
import json
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Function to check if notifications are blocked
def check_notifications_blocked():
    '''Check if notifications are blocked by the existence of a block file'''
    # Check block file
    block_file = os.path.join('data', 'notifications_blocked')
    if os.path.exists(block_file):
        logger.info("Notifications blocked by block file")
        return True
        
    # Check time - only allow between 5:45am and 6:15am Caribbean time
    caribbean_tz = pytz.timezone('America/Port_of_Spain')
    current_time = datetime.now(caribbean_tz)
    allowed_start = current_time.replace(hour=5, minute=45)
    allowed_end = current_time.replace(hour=6, minute=15)
    
    if not (allowed_start <= current_time <= allowed_end):
        logger.info(f"Notifications blocked - current time {current_time} is outside allowed window (5:45am-6:15am Caribbean)")
        return True
        
    return False
def ensure_data_directory():
    """Ensure the data directory exists"""

    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data'):
        os.makedirs('data')

def load_users():
    """Load users from the data/users.json file"""

    # Check if notifications are blocked
    if check_notifications_blocked():
        logger.info("Notifications are currently blocked")
        return {"success": False, "error": "Notifications are currently blocked"}
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

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {get_mail_config}")
    return {"success": False, "error": "Notifications are permanently disabled"}
    Get email configuration directly from environment variables rather than app config.
    
    This is a workaround for when Flask's app.config doesn't properly pick up the environment variables.
    """
    mail_config = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': True,
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', 'calmjourney7@gmail.com'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER')
    }
    
    return mail_config

def send_email(recipient, subject, html_body, text_body=None):

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {send_email}")
    return {"success": False, "error": "Notifications are permanently disabled"}
    # Check if notifications are blocked
    if check_notifications_blocked.check_notifications_blocked():
        logger.info(f"Email to {recipient} blocked by notification block")
        return {"success": False, "error": "Notifications are blocked"}

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
    
    # Default sender to username if not set
    mail_sender = mail_config['MAIL_DEFAULT_SENDER']
    if not mail_sender and mail_username:
        mail_sender = mail_username
        mail_config['MAIL_DEFAULT_SENDER'] = mail_username
        os.environ['MAIL_DEFAULT_SENDER'] = mail_username
        logger.info(f"Set default mail sender to {mail_username}")
        
    # Ensure other mail settings are set as environment variables for future runs
    if not os.environ.get('MAIL_SERVER'):
        os.environ['MAIL_SERVER'] = mail_server
    if not os.environ.get('MAIL_PORT'):
        os.environ['MAIL_PORT'] = str(mail_port)
    
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

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {send_test_email}")
    return {"success": False, "error": "Notifications are permanently disabled"}
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

def send_login_link(email, link, custom_message=None):
    """

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {send_login_link}")
    return {"success": False, "error": "Notifications are permanently disabled"}
    Send a login link to a user.
    
    Args:
        email: The user's email address
        link: The login link
        custom_message: Optional custom message to include in the email
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Log the link being sent for debugging
    logger.info(f"Sending login link to {email}: {link}")
    
    # Determine expiry time from link
    expiry_str = "10 minutes"
    if "expires=" in link:
        try:
            # Extract expiry from URL parameter
            import re
            from datetime import datetime, timedelta
            
            # Try to extract expiry timestamp
            expiry_match = re.search(r'expires=(\d+)', link)
            if expiry_match:
                expiry_timestamp = int(expiry_match.group(1))
                current_time = int(datetime.now().timestamp())
                expiry_minutes = (expiry_timestamp - current_time) // 60
                
                if expiry_minutes > 60:
                    expiry_str = f"{expiry_minutes // 60} hours"
                else:
                    expiry_str = f"{expiry_minutes} minutes"
        except Exception as e:
            logger.error(f"Error parsing expiry time: {str(e)}")
    
    # Add custom message section if provided
    custom_message_html = ""
    custom_message_text = ""
    
    if custom_message and custom_message.strip():
        custom_message_html = f"""
        <div style="margin: 25px 0; padding: 15px; background-color: #f0f7f7; border-left: 4px solid #5f9ea0; border-radius: 3px;">
            <h3 style="color: #5f9ea0; margin-top: 0;">Special message from the Calm Journey team:</h3>
            <p style="white-space: pre-line;">{custom_message}</p>
        </div>
        """
        
        custom_message_text = f"""
Special message from the Calm Journey team:
{custom_message}

"""
    
    subject = "Calm Journey - Your Login Link"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="color: #5f9ea0; margin: 0;">Calm Journey</h1>
            <p style="font-size: 18px; margin: 5px 0 0;">Secure Login Link</p>
        </div>
        
        <div style="padding: 20px; background-color: #fff; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #5f9ea0; border-bottom: 1px solid #eee; padding-bottom: 10px;">Hello!</h2>
            
            {custom_message_html}
            
            <p>You requested a secure login link for Calm Journey.</p>
            
            <p>Click the button below to log in to your account:</p>
            
            <p style="text-align: center; margin: 25px 0;">
                <a href="{link}" style="display: inline-block; background-color: #5f9ea0; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Log In Securely</a>
            </p>
            
            <p>This link will expire in {expiry_str}.</p>
            
            <p><strong>Having trouble with the button?</strong> Copy and paste this link into your browser:</p>
            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all;">
                {link}
            </p>
            
            <p style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
                If you didn't request this link, you can safely ignore this email.
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
            <p>The Calm Journey Team</p>
        </div>
    </body>
    </html>
    """
    text_body = f"""Calm Journey - Your Login Link

Hello!
{custom_message_text}
You requested a secure login link for Calm Journey. Use the link below to log in:

{link}

This link will expire in {expiry_str}.

If you didn't request this link, you can safely ignore this email.

The Calm Journey Team"""
    
    result = send_email(email, subject, html_body, text_body)
    return result.get('success', False)

def send_daily_reminder(user):
    """

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {send_daily_reminder}")
    return {"success": False, "error": "Notifications are permanently disabled"}
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
        <p style="font-size: 0.9em; color: #444; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #5f9ea0; border-radius: 3px; margin-top: 15px;">
            <strong>P.S. Know someone who could use a moment of calm?</strong><br>
            If you have a friend or loved one who might benefit from a gentle daily check-in, feel free to forward this email or share Calm Journey with them:<br>
            <a href="https://calm-mind-ai-naturalarts.replit.app">https://calm-mind-ai-naturalarts.replit.app</a><br>
            Helping one another breathe easier—one day at a time.
        </p>
        <hr>
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

P.S. Know someone who could use a moment of calm?
If you have a friend or loved one who might benefit from a gentle daily check-in, feel free to forward this email or share Calm Journey with them:
https://calm-mind-ai-naturalarts.replit.app
Helping one another breathe easier—one day at a time.

--
You received this email because you enabled notifications in your Calm Journey account.
If you'd like to unsubscribe, please update your notification preferences in your account settings.
"""
    
    result = send_email(email, subject, html_body, text_body)
    return result.get('success', False)

def send_daily_reminder_direct():
    """

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {send_daily_reminder_direct}")
    return {"success": False, "error": "Notifications are permanently disabled"}
    Send daily reminders to all users using direct SMTP rather than Flask-Mail.
    This function doesn't rely on Flask models or app context.
    
    Returns:
        dict: Statistics about the notification sending process
    """
    # Load users from file
    users = load_users()
    
    # Track statistics
    stats = {
        "total_users": len(users),
        "eligible_users": 0,
        "sent_count": 0,
        "error_count": 0,
        "details": []
    }
    
    # Today's date for tracking - use UTC for consistency
    today = datetime.now(pytz.UTC).strftime("%Y-%m-%d")
    logger.info(f"Starting daily notifications for UTC date: {today}")
    
    # Get users with notifications enabled
    eligible_users = []
    for user in users:
        # Skip users without email
        if not user.get("email"):
            continue
            
        # Skip users with notifications disabled
        if not user.get("notifications_enabled", True):
            continue
            
        eligible_users.append(user)
    
    stats["eligible_users"] = len(eligible_users)
    logger.info(f"Found {stats['eligible_users']} users eligible for notifications out of {stats['total_users']} total users")
    
    # Import notification tracking here to avoid circular imports
    from notification_tracking import record_notification_sent, user_received_notification, get_notification_stats
    
    # Check if any notifications were already sent today
    notification_stats = get_notification_stats()
    today_emails = notification_stats.get("email", {}).get(today, [])
    if today_emails:
        logger.info(f"Found {len(today_emails)} notification records already sent today ({today})")
    else:
        logger.info(f"No notification records found for today ({today})")
    
    # Send emails to eligible users who haven't received notification yet today
    for user in eligible_users:
        user_id = user.get("id")
        email = user.get("email")
        
        # Skip if user already received notification today
        if user_received_notification(user_id, "email", today):
            logger.info(f"User {user_id} ({email}) already received a notification today")
            continue
        
        try:
            # Send the daily reminder
            logger.info(f"Sending daily reminder to user {user_id} ({email})")
            
            # Send the email
            result = send_daily_reminder(user)
            
            if result.get("success", False):
                logger.info(f"Successfully sent daily reminder to {email}")
                stats["sent_count"] += 1
                
                # Record successful notification
                record_notification_sent(
                    user_id=user_id,
                    notification_type="email",
                    recipient=email,
                    success=True,
                    date=today
                )
            else:
                logger.error(f"Failed to send daily reminder to {email}: {result.get('error', 'Unknown error')}")
                stats["error_count"] += 1
                stats["details"].append({
                    "user_id": user_id,
                    "email": email,
                    "error": result.get("error", "Unknown error")
                })
                
                # Record failed notification
                record_notification_sent(
                    user_id=user_id,
                    notification_type="email",
                    recipient=email,
                    success=False,
                    details={"error": result.get("error", "Unknown error")},
                    date=today
                )
        except Exception as e:
            logger.error(f"Error sending daily reminder to {email}: {str(e)}", exc_info=True)
            stats["error_count"] += 1
            stats["details"].append({
                "user_id": user_id,
                "email": email,
                "error": str(e)
            })
            
            # Record failed notification
            try:
                record_notification_sent(
                    user_id=user_id,
                    notification_type="email",
                    recipient=email,
                    success=False,
                    details={"error": str(e)},
                    date=today
                )
            except Exception as tracking_error:
                logger.error(f"Error recording notification tracking: {str(tracking_error)}")
    
    logger.info(f"Daily reminders sent. Stats: {stats}")
    return stats

def send_daily_sms_reminder_direct():
    """

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {send_daily_sms_reminder_direct}")
    return {"success": False, "error": "Notifications are permanently disabled"}
    Send daily SMS reminders to all users with SMS notifications enabled.
    This function doesn't rely on Flask models or app context.
    
    Returns:
        dict: Statistics about the notification sending process
    """
    # This requires Twilio setup, which will be handled by the scheduler's load_twilio_credentials function
    logger.info("Starting daily SMS notifications")
    
    # Import here to avoid circular imports
    try:
        from twilio.rest import Client
        from notification_tracking import record_notification_sent, user_received_notification
    except ImportError as e:
        logger.error(f"Failed to import required modules for SMS: {str(e)}")
        return {"error": f"Required modules not available: {str(e)}", "sent_count": 0, "total_users": 0}
    
    # Check Twilio configuration
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, from_number]):
        logger.error("Twilio configuration incomplete. Cannot send SMS notifications.")
        return {"error": "Twilio configuration incomplete", "sent_count": 0, "total_users": 0}
    
    # Load users from file
    users = load_users()
    today = datetime.now(pytz.UTC).strftime("%Y-%m-%d")
    
    # Initialize Twilio client
    try:
        client = Client(account_sid, auth_token)
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {str(e)}")
        return {"error": f"Twilio client initialization failed: {str(e)}", "sent_count": 0, "total_users": len(users)}
    
    # Track statistics
    stats = {
        "total_users": len(users),
        "eligible_users": 0,
        "sent_count": 0,
        "error_count": 0,
        "details": []
    }
    
    # Get users with SMS notifications enabled
    eligible_users = []
    for user in users:
        # Skip users without phone number
        if not user.get("phone"):
            continue
            
        # Skip users with SMS notifications disabled
        if not user.get("sms_notifications_enabled", False):
            continue
            
        eligible_users.append(user)
    
    stats["eligible_users"] = len(eligible_users)
    logger.info(f"Found {stats['eligible_users']} users eligible for SMS notifications")
    
    # Send SMS to eligible users who haven't received notification yet today
    for user in eligible_users:
        user_id = user.get("id")
        phone = user.get("phone")
        username = user.get("username", "there")
        
        # Skip if user already received SMS notification today
        if user_received_notification(user_id, "sms", today):
            logger.info(f"User {user_id} ({phone}) already received an SMS today")
            continue
        
        try:
            # Compose message
            message_body = f"Hello {username}! This is your daily reminder from Calm Journey. Take a moment to check in with yourself today. Visit https://calm-mind-ai-naturalarts.replit.app/journal/new to journal. P.S. Know someone who could use a moment of calm? If you have a friend or loved one who might benefit from a gentle daily check-in, share Calm Journey with them: https://calm-mind-ai-naturalarts.replit.app. Helping one another breathe easier—one day at a time."
            
            # Send SMS
            logger.info(f"Sending SMS to {phone}")
            message = client.messages.create(
                body=message_body,
                from_=from_number,
                to=phone
            )
            
            # Check if message was sent successfully
            if message.sid:
                logger.info(f"Successfully sent SMS to {phone} (SID: {message.sid})")
                stats["sent_count"] += 1
                
                # Record successful notification
                record_notification_sent(
                    user_id=user_id,
                    notification_type="sms",
                    recipient=phone,
                    success=True,
                    details={"sid": message.sid},
                    date=today
                )
            else:
                logger.error(f"Failed to send SMS to {phone}: No SID returned")
                stats["error_count"] += 1
                
                # Record failed notification
                record_notification_sent(
                    user_id=user_id,
                    notification_type="sms",
                    recipient=phone,
                    success=False,
                    details={"error": "No SID returned"},
                    date=today
                )
        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {str(e)}")
            stats["error_count"] += 1
            stats["details"].append({
                "user_id": user_id,
                "phone": phone,
                "error": str(e)
            })
            
            # Record failed notification
            record_notification_sent(
                user_id=user_id,
                notification_type="sms",
                recipient=phone,
                success=False,
                details={"error": str(e)},
                date=today
            )
    
    logger.info(f"Daily SMS notifications sent. Stats: {stats}")
    return stats

def send_weekly_summary(user, stats):
    """

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {send_weekly_summary}")
    return {"success": False, "error": "Notifications are permanently disabled"}
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
        <p style="font-size: 0.9em; color: #444; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #5f9ea0; border-radius: 3px; margin-top: 15px;">
            <strong>P.S. Know someone who could use a moment of calm?</strong><br>
            If you have a friend or loved one who might benefit from a gentle daily check-in, feel free to forward this email or share Calm Journey with them:<br>
            <a href="https://calm-mind-ai-naturalarts.replit.app">https://calm-mind-ai-naturalarts.replit.app</a><br>
            Helping one another breathe easier—one day at a time.
        </p>
        <hr>
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

P.S. Know someone who could use a moment of calm?
If you have a friend or loved one who might benefit from a gentle daily check-in, feel free to forward this email or share Calm Journey with them:
https://calm-mind-ai-naturalarts.replit.app
Helping one another breathe easier—one day at a time.

--
You received this email because you enabled notifications in your Calm Journey account.
If you'd like to unsubscribe, please update your notification preferences in your account settings.
"""
    
    result = send_email(email, subject, html_body, text_body)
    return result.get('success', False)

def send_immediate_notification_to_all_users():
    """

    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {send_immediate_notification_to_all_users}")
    return {"success": False, "error": "Notifications are permanently disabled"}
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
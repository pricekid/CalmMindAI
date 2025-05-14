"""
Notification service - Properly configured to send emails via SendGrid
"""
import logging
import os
import json
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Function to check if notifications are blocked
def check_notifications_blocked():
    """Check if notifications are blocked"""
    # We're enabling notifications, so return False
    return False

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')

def load_users():
    """Load users from the data/users.json file"""
    ensure_data_directory()
    
    # Check if notifications are blocked
    if check_notifications_blocked():
        logger.info("Notifications are currently blocked")
        return {"success": False, "error": "Notifications are currently blocked"}
    
    if not os.path.exists('data/users.json'):
        return []
        
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        return users
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def send_test_email(email_address):
    """
    Send a test email to verify the email service is working.
    """
    try:
        logger.info(f"Attempting to send test email to {email_address}")
        
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            logger.error("SendGrid API key not found in environment variables")
            return False
        
        # Create message
        from_email = Email("calmjourney7@gmail.com")
        to_email = To(email_address)
        subject = "Test Email from Calm Journey"
        html_content = """
        <html>
            <body>
                <h1>Test Email</h1>
                <p>This is a test email sent from the Calm Journey application.</p>
                <p>If you're seeing this, the email notification system is working correctly!</p>
            </body>
        </html>
        """
        content = Content("text/html", html_content)
        
        # Create and send mail
        mail = Mail(from_email, to_email, subject, content)
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(mail)
        
        logger.info(f"Test email sent to {email_address} with status code {response.status_code}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return False

def send_test_sms(phone_number):
    """
    Send a test SMS to verify the SMS service is working.
    """
    try:
        logger.info(f"Attempting to send test SMS to {phone_number}")
        
        # Check for Twilio credentials
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        if not account_sid or not auth_token or not twilio_number:
            logger.error("Twilio credentials not found in environment variables")
            return False
        
        # Import Twilio here to avoid impacting users without Twilio credentials
        from twilio.rest import Client
        
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Send test SMS
        message = client.messages.create(
            body="This is a test SMS from Calm Journey. If you're seeing this, the SMS notification system is working correctly!",
            from_=twilio_number,
            to=phone_number
        )
        
        logger.info(f"Test SMS sent to {phone_number} with SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending test SMS: {str(e)}")
        return False
        
def send_email(recipient, subject, html_content, text_content=None):
    """
    Send an email using SendGrid.
    
    Args:
        recipient: The recipient's email address
        subject: Email subject
        html_content: HTML email content
        text_content: Optional plain text content
        
    Returns:
        dict: Result with success status and any error message
    """
    try:
        logger.info(f"Attempting to send email to {recipient}")
        
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            logger.error("SendGrid API key not found in environment variables")
            return {"success": False, "error": "SendGrid API key not configured"}
        
        # Create message
        from_email = Email("calmjourney7@gmail.com")
        to_email = To(recipient)
        
        # Create mail with content
        mail = Mail(from_email, to_email, subject, Content("text/html", html_content))
        
        # Add plain text content if provided
        if text_content:
            mail.add_content(Content("text/plain", text_content))
        
        # Send email
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(mail)
        
        logger.info(f"Email sent to {recipient} with status code {response.status_code}")
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error sending email to {recipient}: {str(e)}")
        return {"success": False, "error": str(e)}

def send_immediate_notification_to_all_users():
    """
    Send an immediate notification to all users with notifications enabled.
    """
    # Load users from data store
    users = load_users()
    if not isinstance(users, list):
        return users  # Error already logged in load_users
    
    success_count = 0
    failure_count = 0
    results = []
    
    for user in users:
        # Skip users who have opted out of notifications
        if not user.get('notifications_enabled', False):
            continue
            
        # Skip users without email addresses
        if not user.get('email'):
            continue
        
        email = user.get('email')
        subject = "Calm Journey Notification"
        html_content = """
        <html>
            <body>
                <h1>Calm Journey Update</h1>
                <p>This is a notification from your Calm Journey application.</p>
                <p>Your wellbeing matters to us. Take a moment today to reflect and journal.</p>
                <p><a href="https://calmjourney.app">Visit Calm Journey</a></p>
            </body>
        </html>
        """
        
        result = send_email(email, subject, html_content)
        results.append({
            'user_id': user.get('id'),
            'email': email,
            'success': result.get('success'),
            'error': result.get('error')
        })
        
        if result.get('success'):
            success_count += 1
        else:
            failure_count += 1
    
    return {
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results,
        "message": f"Sent {success_count} notifications, {failure_count} failures"
    }
    
def send_sms(phone_number, message):
    """
    Send an SMS using Twilio.
    
    Args:
        phone_number: The recipient's phone number
        message: The message to send
        
    Returns:
        dict: Result with success status and any error message
    """
    try:
        logger.info(f"Attempting to send SMS to {phone_number}")
        
        # Check for Twilio credentials
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        if not account_sid or not auth_token or not twilio_number:
            logger.error("Twilio credentials not found in environment variables")
            return {"success": False, "error": "Twilio credentials not configured"}
        
        # Import Twilio here to avoid impacting users without Twilio credentials
        from twilio.rest import Client
        
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Send SMS
        twilio_message = client.messages.create(
            body=message,
            from_=twilio_number,
            to=phone_number
        )
        
        logger.info(f"SMS sent to {phone_number} with SID: {twilio_message.sid}")
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error sending SMS to {phone_number}: {str(e)}")
        return {"success": False, "error": str(e)}

def send_immediate_sms_to_all_users():
    """
    Send an immediate SMS to all users with SMS notifications enabled.
    """
    # Load users from data store
    users = load_users()
    if not isinstance(users, list):
        return users  # Error already logged in load_users
    
    success_count = 0
    failure_count = 0
    results = []
    
    for user in users:
        # Skip users who have opted out of SMS notifications
        if not user.get('sms_notifications_enabled', False):
            continue
            
        # Skip users without phone numbers
        if not user.get('phone_number'):
            continue
        
        phone_number = user.get('phone_number')
        message = "Calm Journey Update: Your wellbeing matters to us. Take a moment today to reflect and journal."
        
        result = send_sms(phone_number, message)
        results.append({
            'user_id': user.get('id'),
            'phone_number': phone_number,
            'success': result.get('success'),
            'error': result.get('error')
        })
        
        if result.get('success'):
            success_count += 1
        else:
            failure_count += 1
    
    return {
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results,
        "message": f"Sent {success_count} SMS notifications, {failure_count} failures"
    }
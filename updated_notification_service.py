"""
Updated notification service with working SendGrid integration.
This replaces the previous notification_service.py which had issues with SendGrid.
"""
import logging
import os
import json
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Import fallback email functionality
try:
    from fallback_email import save_fallback_email
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False
    logging.warning("Fallback email module not available")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SENDER_EMAIL = "dearteddybb@gmail.com"
SENDER_NAME = "Dear Teddy"

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
            users = json.load(f)
        return users
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def send_email(to_email, subject, html_content, text_content=None):
    """
    Send an email using SendGrid.
    
    Args:
        to_email: Recipient's email address
        subject: Email subject
        html_content: HTML content
        text_content: Optional plain text content (fallback)
        
    Returns:
        dict: Result with success status and any error message
    """
    try:
        logger.info(f"Attempting to send email to {to_email}")
        
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            logger.error("SendGrid API key not found in environment variables")
            raise ValueError("SendGrid API key not configured")
        
        # Create message with simplified approach (this avoids bugs in the more complex API)
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        # Send email
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        logger.info(f"Email sent to {to_email} with status code {response.status_code}")
        return {"success": True, "status_code": response.status_code}
    
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        
        # Use fallback email system if available
        if FALLBACK_AVAILABLE:
            try:
                fallback_file = save_fallback_email(to_email, subject, html_content, email_type="notification")
                logger.info(f"Email saved to fallback system for {to_email}: {fallback_file}")
                return {"success": True, "fallback": True, "message": "Email saved to fallback system"}
            except Exception as fallback_error:
                logger.error(f"Error using fallback email system: {str(fallback_error)}")
        
        return {"success": False, "error": str(e)}

def send_test_email(email_address):
    """
    Send a test email to verify the email service is working.
    
    Args:
        email_address: The recipient's email address
        
    Returns:
        bool: True if the email was sent successfully (or saved to fallback)
    """
    subject = "Test Email from Dear Teddy"
    html_content = """
    <html>
        <body>
            <h1>Test Email</h1>
            <p>This is a test email sent from the Dear Teddy application.</p>
            <p>If you're seeing this, the email notification system is working correctly!</p>
            <p>Time sent: {timestamp}</p>
        </body>
    </html>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    result = send_email(email_address, subject, html_content)
    return result.get('success', False)

def send_password_reset_email(email_address, reset_token, reset_url=None):
    """
    Send a password reset email using the new template.
    
    Args:
        email_address: The recipient's email address
        reset_token: The password reset token
        reset_url: Optional full reset URL
        
    Returns:
        dict: Result with success status
    """
    from flask import render_template, current_app
    
    # Create reset URL if not provided
    if not reset_url:
        reset_url = f"https://dearteddy-app.replit.app/reset-password/{reset_token}"
    
    subject = "Reset Your Dear Teddy Password"
    
    try:
        # Render the templates with the provided reset URL
        html_content = render_template('emails/password_reset.html', reset_url=reset_url)
        text_content = render_template('emails/password_reset.txt', reset_url=reset_url)
        logger.info(f"Successfully rendered password reset email templates for {email_address}")
    except Exception as e:
        logger.error(f"Error rendering password reset email templates: {str(e)}")
        # Fallback to inline HTML if template rendering fails
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #A05C2C; padding: 20px; text-align: center; color: white;">
                    <h1 style="margin: 0;">Dear Teddy</h1>
                </div>
                <div style="padding: 20px; border: 1px solid #ddd; border-top: none;">
                    <h2>Password Reset Request</h2>
                    <p>We received a request to reset your password. If you didn't make this request, you can ignore this email.</p>
                    <p>To reset your password, click the link below:</p>
                    <p><a href="{reset_url}">{reset_url}</a></p>
                    <p>This link will expire in 60 minutes for security reasons.</p>
                </div>
                <div style="text-align: center; padding: 20px; font-size: 0.8em; color: #666;">
                    <p>&copy; 2025 Dear Teddy. All rights reserved.</p>
                </div>
            </body>
        </html>
        """
        text_content = f"""
        DEAR TEDDY PASSWORD RESET
        
        We received a request to reset your password for your Dear Teddy account.
        
        Please visit the link below to set a new password:
        {reset_url}
        
        This link will expire in 60 minutes for security reasons.
        
        If you didn't request a password reset, please ignore this email.
        
        © 2025 Dear Teddy. All rights reserved.
        """
    
    # Add text content to the email for better deliverability
    return send_email(email_address, subject, html_content, text_content)

def send_immediate_notification_to_all_users():
    """
    Send an immediate notification to all users with notifications enabled.
    
    Returns:
        dict: Result with success/failure counts
    """
    # Load users from data store
    users = load_users()
    if not isinstance(users, list):
        return {"success": False, "error": "Failed to load users"}
    
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
        subject = "Dear Teddy Notification"
        html_content = """
        <html>
            <body>
                <h1>Dear Teddy Update</h1>
                <p>This is a notification from your Dear Teddy application.</p>
                <p>Your wellbeing matters to us. Take a moment today to reflect and journal.</p>
                <p><a href="https://dearteddy-app.replit.app">Visit Dear Teddy</a></p>
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

def is_email_system_working():
    """Check if the email system is working"""
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    return bool(sendgrid_api_key)
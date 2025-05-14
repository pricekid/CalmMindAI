"""
Enhanced email service using SendGrid with improved error handling and diagnostics.
This replaces the previous notification_service.py implementation.
"""
import logging
import os
import json
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization

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

def is_sendgrid_configured():
    """Check if SendGrid is properly configured"""
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        logger.warning("SENDGRID_API_KEY environment variable not set")
        return False
    
    # Check if the API key has a valid format (doesn't mean it's actually working)
    if not api_key.startswith('SG.'):
        logger.warning("SENDGRID_API_KEY does not have the expected format (should start with 'SG.')")
        return False
        
    return True

def get_sendgrid_client():
    """Get a SendGrid client instance"""
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        raise ValueError("SendGrid API key not configured")
    
    return SendGridAPIClient(api_key)

def send_email(to_email, subject, html_content, text_content=None, template_id=None, 
               dynamic_template_data=None, categories=None, from_email=None):
    """
    Enhanced email sending function that supports both direct content and templates.
    
    Args:
        to_email (str): Recipient's email address
        subject (str): Email subject (not used with templates)
        html_content (str): HTML content (not used with templates)
        text_content (str, optional): Plain text content
        template_id (str, optional): SendGrid template ID
        dynamic_template_data (dict, optional): Data for template
        categories (list, optional): List of categories for tracking
        from_email (str, optional): Override sender email
        
    Returns:
        dict: Result with success status and any error details
    """
    if not is_sendgrid_configured():
        logger.error("SendGrid is not properly configured")
        if FALLBACK_AVAILABLE:
            try:
                save_fallback_email(to_email, subject, html_content, email_type="notification")
                return {
                    "success": True,
                    "fallback": True,
                    "message": "Email saved to fallback system due to SendGrid configuration issue"
                }
            except Exception as e:
                logger.error(f"Failed to save fallback email: {str(e)}")
                return {"success": False, "error": f"SendGrid not configured and fallback failed: {str(e)}"}
        return {"success": False, "error": "SendGrid not configured and fallback not available"}

    try:
        # Start with the sender
        sender = from_email or SENDER_EMAIL
        message = Mail(from_email=sender)
        
        # Add recipient and personalization
        personalization = Personalization()
        personalization.add_to(To(to_email))
        
        if template_id:
            # Template-based email
            message.template_id = template_id
            if dynamic_template_data:
                personalization.dynamic_template_data = dynamic_template_data
        else:
            # Content-based email
            personalization.subject = subject
            message.add_content(Content("text/html", html_content))
            if text_content:
                message.add_content(Content("text/plain", text_content))
                
        message.add_personalization(personalization)
        
        # Add categories for tracking if provided
        if categories:
            for category in categories:
                message.add_category(category)
                
        # Get SendGrid client and send
        sg = get_sendgrid_client()
        response = sg.send(message)
        
        logger.info(f"Email sent to {to_email} with status code {response.status_code}")
        return {"success": True, "status_code": response.status_code}
    
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        
        # Use fallback if available
        if FALLBACK_AVAILABLE:
            try:
                logger.info(f"Saving email to fallback system for {to_email}")
                save_fallback_email(to_email, subject, html_content, email_type="notification")
                return {
                    "success": True,
                    "fallback": True,
                    "message": f"Email saved to fallback system. Error: {str(e)}"
                }
            except Exception as fallback_e:
                logger.error(f"Failed to save fallback email: {str(fallback_e)}")
                
        return {"success": False, "error": str(e)}

def send_password_reset_email(to_email, reset_token, reset_url=None):
    """
    Send a password reset email with token.
    
    Args:
        to_email (str): Recipient's email address
        reset_token (str): Password reset token
        reset_url (str, optional): Full reset URL (if token is already included)
        
    Returns:
        dict: Result with success status
    """
    subject = "Password Reset Request - Dear Teddy"
    
    # Create reset URL if not provided
    if not reset_url:
        reset_url = f"https://dearteddy-app.replit.app/reset-password/{reset_token}"
        
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1D4D4F; padding: 20px; text-align: center; color: white;">
                <h1 style="margin: 0;">Dear Teddy</h1>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd; border-top: none;">
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password. If you didn't make this request, you can ignore this email.</p>
                <p>To reset your password, click the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #1D4D4F; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Reset Password</a>
                </div>
                <p>Or copy and paste this URL into your browser:</p>
                <p style="word-break: break-all;"><a href="{reset_url}">{reset_url}</a></p>
                <p>This link will expire in 1 hour for security reasons.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="font-size: 0.8em; color: #666;">
                    If you didn't request this password reset, no action is needed on your part.<br>
                    Your password will remain unchanged.
                </p>
            </div>
            <div style="text-align: center; padding: 20px; font-size: 0.8em; color: #666;">
                <p>&copy; 2025 Dear Teddy. All rights reserved.</p>
            </div>
        </body>
    </html>
    """
    
    text_content = f"""
    Dear Teddy - Password Reset Request
    
    We received a request to reset your password. If you didn't make this request, you can ignore this email.
    
    To reset your password, visit this URL:
    {reset_url}
    
    This link will expire in 1 hour for security reasons.
    
    If you didn't request this password reset, no action is needed on your part.
    Your password will remain unchanged.
    
    © 2025 Dear Teddy. All rights reserved.
    """
    
    return send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        categories=["password_reset"]
    )

def send_test_email(to_email):
    """
    Send a test email to verify the SendGrid integration works.
    
    Args:
        to_email (str): Recipient's email address
        
    Returns:
        dict: Result with success status
    """
    subject = "Test Email from Dear Teddy"
    
    html_content = """
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1D4D4F; padding: 20px; text-align: center; color: white;">
                <h1 style="margin: 0;">Dear Teddy</h1>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd; border-top: none;">
                <h2>Test Email</h2>
                <p>This is a test email sent from the Dear Teddy application.</p>
                <p>If you're seeing this, the email notification system is working correctly!</p>
                <p>Email diagnostics:</p>
                <ul>
                    <li>Sender: dearteddybb@gmail.com</li>
                    <li>Time: {datetime_utc}</li>
                    <li>SendGrid: Operational</li>
                </ul>
            </div>
            <div style="text-align: center; padding: 20px; font-size: 0.8em; color: #666;">
                <p>&copy; 2025 Dear Teddy. All rights reserved.</p>
            </div>
        </body>
    </html>
    """.format(datetime_utc=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    
    text_content = f"""
    Dear Teddy - Test Email
    
    This is a test email sent from the Dear Teddy application.
    
    If you're seeing this, the email notification system is working correctly!
    
    Email diagnostics:
    - Sender: dearteddybb@gmail.com
    - Time: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
    - SendGrid: Operational
    
    © 2025 Dear Teddy. All rights reserved.
    """
    
    return send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        categories=["test"]
    )

def email_diagnostics():
    """
    Run diagnostics on the email configuration.
    
    Returns:
        dict: Diagnostic information
    """
    diagnostics = {
        "sendgrid_configured": is_sendgrid_configured(),
        "api_key_present": bool(os.environ.get('SENDGRID_API_KEY')),
        "fallback_available": FALLBACK_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Test API key format
    api_key = os.environ.get('SENDGRID_API_KEY')
    if api_key:
        diagnostics["api_key_format_valid"] = api_key.startswith('SG.')
        diagnostics["api_key_length"] = len(api_key)
    else:
        diagnostics["api_key_format_valid"] = False
        diagnostics["api_key_length"] = 0
        
    return diagnostics
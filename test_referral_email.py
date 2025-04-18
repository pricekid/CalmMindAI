"""
Test script to send a daily reminder email with referral link.
This script includes the referral section to verify the email template.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_referral_test_email(recipient_email):
    """
    Send a test email with the referral link section to verify format and delivery.
    
    Args:
        recipient_email: The recipient's email address
    """
    # Email configuration
    mail_server = "smtp.gmail.com"
    mail_port = 587
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_sender = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Test user information
    username = "Test User"
    test_referral_url = "https://calm-mind-ai-naturalarts.replit.app/register?ref=TESTCODE123"
    
    # Create email subject and content
    subject = "Calm Journey - Daily Wellness Reminder (With Referral Link)"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.5;">
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="color: #5f9ea0; margin: 0;">Calm Journey</h1>
            <p style="font-size: 18px; margin: 5px 0 0;">Daily Wellness Reminder</p>
        </div>
        
        <div style="padding: 20px; background-color: #fff; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #5f9ea0;">Hello {username}!</h2>
            
            <p>This is your daily reminder to take a moment for yourself and check in with your mental well-being.</p>
            
            <p>We'd love to hear how you're doing today. Consider spending just 5 minutes journaling about your thoughts and feelings.</p>
            
            <p style="text-align: center; margin: 25px 0;">
                <a href="https://calm-mind-ai-naturalarts.replit.app/journal/new" style="display: inline-block; background-color: #5f9ea0; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Create a New Journal Entry</a>
            </p>
            
            <hr style="border: 0; height: 1px; background-color: #eee; margin: 25px 0;">
            
            <p><strong>P.S.</strong> Know someone who could use a moment of calm?</p>
            
            <p>If you have a friend or loved one who might benefit from a gentle daily check-in, feel free to forward this email or share Calm Journey with them:</p>
            
            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all;">
                <a href="{test_referral_url}" style="color: #5f9ea0;">{test_referral_url}</a>
            </p>
            
            <p style="font-style: italic; font-size: 0.9em; color: #666;">Helping one another breathe easier—one day at a time.</p>
            
            <hr style="border: 0; height: 1px; background-color: #eee; margin: 25px 0;">
            
            <p style="font-style: italic; color: #666;">The Calm Journey Team</p>
            
            <p style="font-size: 0.8em; color: #888;">
                You received this email because you enabled notifications in your Calm Journey account.
                If you'd like to unsubscribe, please update your notification preferences in your account settings.
            </p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""Calm Journey - Daily Wellness Reminder

Hello {username}!

This is your daily reminder to take a moment for yourself and check in with your mental well-being.

We'd love to hear how you're doing today. Consider spending just 5 minutes journaling about your thoughts and feelings.

Visit https://calm-mind-ai-naturalarts.replit.app/journal/new to create a new journal entry.

--------------------------
P.S. Know someone who could use a moment of calm?

If you have a friend or loved one who might benefit from a gentle daily check-in, feel free to forward this email or share Calm Journey with them:

{test_referral_url}

Helping one another breathe easier—one day at a time.
--------------------------

The Calm Journey Team

--
You received this email because you enabled notifications in your Calm Journey account.
If you'd like to unsubscribe, please update your notification preferences in your account settings.
"""
    
    # Create the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_sender
    message["To"] = recipient_email
    
    # Add text and HTML parts
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))
    
    try:
        # Connect to the mail server
        logger.info(f"Connecting to mail server {mail_server}:{mail_port}...")
        server = smtplib.SMTP(mail_server, mail_port, timeout=15)
        server.starttls()
        
        # Log in to the mail server
        logger.info(f"Logging in to mail server as {mail_username}...")
        server.login(mail_username, mail_password)
        
        # Send the email
        logger.info(f"Sending referral test email to {recipient_email}...")
        server.sendmail(mail_sender, recipient_email, message.as_string())
        
        # Close the connection
        server.quit()
        
        logger.info(f"Referral test email sent successfully to {recipient_email}")
        return {"success": True}
    
    except Exception as e:
        error_msg = f"Error sending referral test email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
        print(f"Sending referral test email to {email}...")
        result = send_referral_test_email(email)
        
        if result["success"]:
            print("\n✅ Referral test email sent successfully!")
            print("* Check your inbox (and spam folder) to see the referral link formatting")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
    else:
        print("Usage: python3 test_referral_email.py [email_address]")
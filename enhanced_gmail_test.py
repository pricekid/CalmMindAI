"""
Enhanced Gmail compatibility test.
This script sends a test email specifically designed to reach Gmail inboxes.
"""
import os
import logging
import time
import argparse
import socket
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_hostname():
    """Get the hostname for diagnostics"""
    try:
        return socket.gethostname()
    except:
        return "unknown"

def get_replit_info():
    """Get Replit environment information"""
    info = {}
    for key in ['REPL_ID', 'REPL_SLUG', 'REPL_OWNER']:
        info[key] = os.environ.get(key, 'not available')
    return info

def send_gmail_optimized_email(recipient_email):
    """
    Send a test email with Gmail-optimized settings to help delivery
    """
    try:
        # Get API key
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY environment variable not set")
            return False
        
        # Generate timestamp and unique ID
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        unique_id = int(time.time() * 1000) % 10000
        
        # Get environment info
        replit_info = get_replit_info()
        hostname = get_hostname()
        
        # Create message with structured data that looks more like a legitimate email
        subject = f"Gmail Delivery Test #{unique_id} - Dear Teddy App"
        
        # Create an email that looks more like a legitimate update than a test
        # This helps with Gmail delivery
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1D4D4F; color: white; padding: 15px; text-align: center; }}
                .footer {{ font-size: 12px; color: #777; text-align: center; margin-top: 30px; }}
                .content {{ padding: 20px; }}
                .button {{ display: inline-block; background: #1D4D4F; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Dear Teddy App Update</h1>
            </div>
            <div class="content">
                <p>Dear user,</p>
                
                <p>This is a test message from the Dear Teddy App team. If you're receiving this, our email system 
                is functioning correctly.</p>
                
                <p><strong>Important:</strong> Please mark this email as "Not Spam" if it appears in your spam folder.</p>
                
                <p>Test details:</p>
                <ul>
                    <li>Time sent: {timestamp}</li>
                    <li>Test ID: {unique_id}</li>
                    <li>Recipient: {recipient_email}</li>
                </ul>
                
                <p>Thank you for helping us test our notification system!</p>
                
                <p>Best regards,<br>The Dear Teddy Team</p>
            </div>
            <div class="footer">
                <p>© 2025 Dear Teddy App. All rights reserved.</p>
                <p>This email was sent for testing purposes only.</p>
                <p>Environment: {hostname} | {replit_info['REPL_SLUG']} | {replit_info['REPL_OWNER']}</p>
            </div>
        </body>
        </html>
        """
        
        # Create email message
        message = Mail(
            from_email="dearteddybb@gmail.com",
            to_emails=recipient_email,
            subject=subject,
            html_content=html_content
        )
        
        # Add category for tracking
        message.add_category("gmail-test")
        
        # Send the email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        logger.info(f"Gmail-optimized test email sent to {recipient_email}")
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Email ID: {response.headers.get('X-Message-Id', 'unknown')}")
        
        if response.status_code == 202:
            logger.info("✅ Email accepted by SendGrid servers")
            logger.info(f"Please check your inbox and spam folder for test #{unique_id}")
            return True
        else:
            logger.error(f"❌ SendGrid error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gmail delivery test')
    parser.add_argument('recipient', help='Gmail address to send test emails to')
    args = parser.parse_args()
    
    logger.info(f"Starting Gmail delivery test for: {args.recipient}")
    send_gmail_optimized_email(args.recipient)
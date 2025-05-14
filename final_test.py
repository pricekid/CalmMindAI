"""
Final simplified test script for email delivery diagnostics.
"""
import os
import logging
import time
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_final_test(recipient_email):
    """Send a final test email with clear instructions and visually distinct content"""
    try:
        # Get API key from environment
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY environment variable not set")
            return False
            
        # Generate timestamp and unique ID to track this specific email
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        unique_id = int(time.time()) % 10000
        
        # Create eye-catching subject line
        subject = f"IMPORTANT: Dear Teddy Email Test #{unique_id}"
        
        # Create HTML content with instructions
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #1D4D4F; color: white; padding: 20px; text-align: center;">
                <h1>Dear Teddy App</h1>
                <h2>Email Delivery Test #{unique_id}</h2>
            </div>
            
            <div style="padding: 20px; border: 1px solid #ddd; border-top: none;">
                <p>This is a <strong>FINAL TEST</strong> of our email delivery system.</p>
                
                <p style="background-color: #ffeb3b; padding: 10px; border-left: 4px solid #ffc107;">
                    <strong>Important:</strong> If you see this email, please let us know immediately!
                </p>
                
                <ul>
                    <li>Time sent: {timestamp}</li>
                    <li>Test ID: #{unique_id}</li>
                    <li>Recipient: {recipient_email}</li>
                </ul>
                
                <p>We're testing several improvements to our email delivery system. Your feedback 
                is extremely important.</p>
                
                <p>Thank you,<br>The Dear Teddy Team</p>
            </div>
        </body>
        </html>
        """
        
        # Create message
        message = Mail(
            from_email="dearteddybb@gmail.com",
            to_emails=recipient_email,
            subject=subject,
            html_content=html_content
        )
        
        # Send message
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Log response
        logger.info(f"Final test email sent to {recipient_email}")
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 202:
            logger.info(f"✅ Success! Test #{unique_id} accepted by SendGrid")
            return True
        else:
            logger.error(f"❌ Error: Status code {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python final_test.py <recipient_email>")
        sys.exit(1)
    
    recipient = sys.argv[1]
    logger.info(f"Sending final test email to: {recipient}")
    
    success = send_final_test(recipient)
    if success:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")
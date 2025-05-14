"""
Test script to send a direct email using SendGrid.
"""
import os
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

def send_test_email(recipient_email):
    """
    Send a test email via SendGrid directly.
    """
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    if not sendgrid_api_key:
        print("ERROR: SENDGRID_API_KEY environment variable is not set")
        return False
    
    print(f"SendGrid API key found (first 5 chars): {sendgrid_api_key[:5]}...")
    
    # Create message
    from_email = Email("noreply@dearteddy.app")
    to_email = To(recipient_email)
    subject = "Test Email from Dear Teddy"
    html_content = """
    <html>
        <body>
            <h1>Test Email</h1>
            <p>This is a test email sent directly from the SendGrid API.</p>
            <p>If you're seeing this, the SendGrid integration is working correctly!</p>
        </body>
    </html>
    """
    content = Content("text/html", html_content)
    
    # Create mail
    mail = Mail(from_email, to_email, subject, content)
    
    try:
        # Send the email
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(mail)
        print(f"Email sent to {recipient_email}")
        print(f"Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_test_email_now.py <email_address>")
        sys.exit(1)
    
    recipient_email = sys.argv[1]
    success = send_test_email(recipient_email)
    
    if success:
        print("Email sent successfully!")
    else:
        print("Failed to send email.")
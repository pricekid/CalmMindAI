"""
Test script to verify mail configuration.
"""
import os
import sys
import logging
import traceback
from app import app, mail
from flask_mail import Message

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mail_config():
    """Test the email configuration by sending a test email."""
    test_recipient = None
    
    # Check if an email address was provided as an argument
    if len(sys.argv) > 1:
        test_recipient = sys.argv[1]
    
    # If no recipient provided, ask for one
    if not test_recipient:
        test_recipient = input("Enter an email address to send a test to: ")
    
    # Print current mail configuration
    print("\nCurrent Mail Configuration:")
    print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"MAIL_USERNAME: {'Set' if app.config.get('MAIL_USERNAME') else 'Not set'}")
    print(f"MAIL_PASSWORD: {'Set' if app.config.get('MAIL_PASSWORD') else 'Not set'}")
    print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    
    # Check if we have the necessary configuration
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        print("\nError: MAIL_USERNAME or MAIL_PASSWORD is not set.")
        print("Please set these environment variables before testing.")
        return False
    
    try:
        print(f"\nSending test email to {test_recipient}...")
        
        # Create a test message
        msg = Message(
            "Calm Journey - Mail Configuration Test",
            recipients=[test_recipient],
            body="This is a test email to verify the mail configuration is working correctly.",
            html="<h1>Calm Journey</h1><p>This is a test email to verify the mail configuration is working correctly.</p>"
        )
        
        # Try to send the message
        mail.send(msg)
        
        print("\nSuccess! Test email sent.")
        print("If you don't see the email in your inbox, please check your spam folder.")
        return True
    
    except Exception as e:
        print(f"\nError sending test email: {str(e)}")
        traceback.print_exc()
        
        # Provide some suggestions based on the error
        if "Authentication" in str(e):
            print("\nThis appears to be an authentication error. Please check:")
            print("1. Your MAIL_USERNAME and MAIL_PASSWORD are correct.")
            print("2. If using Gmail, make sure 'Allow less secure apps' is enabled or use an App Password.")
        elif "Connection" in str(e):
            print("\nThis appears to be a connection error. Please check:")
            print("1. Your MAIL_SERVER and MAIL_PORT settings are correct.")
            print("2. Your network allows outgoing connections to the mail server.")
        
        return False

if __name__ == "__main__":
    with app.app_context():
        test_mail_config()
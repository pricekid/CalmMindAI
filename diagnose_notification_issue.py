"""
This script diagnoses email notification issues and attempts to send an immediate 
notification to a specific user ID or email for testing.
"""
import os
import sys
import logging
import traceback
from flask import Flask
from app import app, mail, db
from models import User
from flask_mail import Message
from improved_email_service import send_email

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_email_config():
    """Check that all required email configuration is present."""
    mail_server = app.config.get('MAIL_SERVER')
    mail_port = app.config.get('MAIL_PORT')
    mail_username = app.config.get('MAIL_USERNAME')
    mail_password = app.config.get('MAIL_PASSWORD')
    mail_sender = app.config.get('MAIL_DEFAULT_SENDER')
    
    print("\n===== EMAIL CONFIGURATION =====")
    print(f"MAIL_SERVER: {mail_server}")
    print(f"MAIL_PORT: {mail_port}")
    print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"MAIL_USERNAME: {'Set' if mail_username else 'NOT SET (Required)'}")
    print(f"MAIL_PASSWORD: {'Set' if mail_password else 'NOT SET (Required)'}")
    print(f"MAIL_DEFAULT_SENDER: {mail_sender or 'NOT SET (Required)'}")
    
    if not all([mail_server, mail_port, mail_username, mail_password, mail_sender]):
        print("\n[ERROR] Missing required email configuration!")
        print("Make sure all mail-related environment variables are set.")
        return False
    
    print("\n[OK] Email configuration looks complete.")
    return True

def count_users_with_notifications():
    """Count how many users have notifications enabled."""
    with app.app_context():
        total_users = User.query.count()
        users_with_email = User.query.filter_by(notifications_enabled=True).count()
        users_with_sms = User.query.filter_by(sms_notifications_enabled=True).count()
        
        print("\n===== NOTIFICATION USERS =====")
        print(f"Total users: {total_users}")
        print(f"Users with email notifications enabled: {users_with_email}")
        print(f"Users with SMS notifications enabled: {users_with_sms}")
        
        if users_with_email == 0:
            print("\n[WARNING] No users have email notifications enabled!")
            print("Enable notifications for at least one user.")
            return False
            
        print("\n[OK] Users with notifications found.")
        return True

def test_send_immediate_to_email(email):
    """Send a test email to a specific email address."""
    try:
        print(f"\n===== SENDING TEST EMAIL TO {email} =====")
        
        # First, try with the improved email service
        print("Attempting to send with improved email service...")
        
        with app.app_context():
            subject = "Calm Journey - Notification Test"
            html_body = """
            <html>
            <body>
                <h2>Calm Journey - Notification Test</h2>
                <p>This is a test email to verify that the notification system is working correctly.</p>
                <p>If you're seeing this, it means the configuration is valid!</p>
                <hr>
                <p><em>The Calm Journey Team</em></p>
            </body>
            </html>
            """
            text_body = "Calm Journey - Notification Test\n\nThis is a test email to verify that the notification system is working correctly.\nIf you're seeing this, it means the configuration is valid!"
            
            result = send_email(email, subject, html_body, text_body)
            
            if result.get("success"):
                print("[OK] Email sent successfully with improved service!")
                return True
            else:
                print(f"[ERROR] Failed to send with improved service: {result.get('error')}")
                print("Trying with Flask-Mail...")
                
                # Fall back to Flask-Mail
                msg = Message(
                    subject="Calm Journey - Notification Test (Flask-Mail)",
                    recipients=[email],
                    body=text_body,
                    html=html_body,
                    sender=app.config['MAIL_DEFAULT_SENDER']
                )
                
                mail.send(msg)
                print("[OK] Email sent successfully with Flask-Mail!")
                return True
                
    except Exception as e:
        print(f"[ERROR] Failed to send email: {str(e)}")
        traceback.print_exc()
        return False

def test_send_to_user_id(user_id):
    """Send a test email to a specific user by ID."""
    try:
        with app.app_context():
            user = User.query.get(user_id)
            
            if not user:
                print(f"[ERROR] User with ID {user_id} not found!")
                return False
                
            if not user.email:
                print(f"[ERROR] User {user.username} (ID: {user_id}) has no email address!")
                return False
                
            print(f"\n===== SENDING TEST EMAIL TO USER {user.username} (ID: {user_id}) =====")
            print(f"Email: {user.email}")
            print(f"Notifications enabled: {user.notifications_enabled}")
            
            if not user.notifications_enabled:
                print("[WARNING] This user has notifications disabled!")
                response = input("Send anyway? (y/n): ")
                if response.lower() != 'y':
                    print("Aborted.")
                    return False
            
            return test_send_immediate_to_email(user.email)
            
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Main function to diagnose notification issues."""
    print("===== NOTIFICATION SYSTEM DIAGNOSIS =====")
    
    # Check email configuration
    if not check_email_config():
        print("\nPlease fix the email configuration issues before continuing.")
        return False
    
    # Check users with notifications
    count_users_with_notifications()
    
    # Check if arguments are provided for testing
    if len(sys.argv) > 1:
        arg_type = sys.argv[1]
        
        if arg_type == "user" and len(sys.argv) > 2:
            # Test sending to a specific user ID
            try:
                user_id = int(sys.argv[2])
                print(f"\n===== TESTING EMAIL TO USER ID {user_id} =====")
                success = test_send_to_user_id(user_id)
            except ValueError:
                print(f"[ERROR] Invalid user ID: {sys.argv[2]}")
                return False
                
        elif arg_type == "email" and len(sys.argv) > 2:
            # Test sending to a specific email address
            email = sys.argv[2]
            print(f"\n===== TESTING EMAIL TO {email} =====")
            success = test_send_immediate_to_email(email)
            
        else:
            print("Usage:")
            print("  python diagnose_notification_issue.py - Run general diagnostics")
            print("  python diagnose_notification_issue.py user <user_id> - Test email to specific user")
            print("  python diagnose_notification_issue.py email <email> - Test email to specific address")
            return False
            
        if success:
            print("\n===== SUCCESS =====")
            print("The email notification was sent successfully!")
            print("Check the recipient's inbox (and spam folder) for the test email.")
            print("\nIf you still have issues with the bulk notification system:")
            print("1. Check that users have notifications_enabled=True in the database")
            print("2. Verify email addresses are valid")
            print("3. Look for rate limiting or spam filtering by the email provider")
            return True
        else:
            print("\n===== FAILURE =====")
            print("The email notification could not be sent.")
            print("Review the error messages above for more information.")
            return False
    else:
        # Non-interactive mode, just run diagnostics
        print("\nEmail configuration and notification users check complete.")
        print("To test sending an email, run one of the following:")
        print("  python diagnose_notification_issue.py user <user_id> - Test email to specific user")
        print("  python diagnose_notification_issue.py email <email> - Test email to specific address")
    
    print("\nDiagnosis complete!")
    return True

if __name__ == "__main__":
    with app.app_context():
        main()
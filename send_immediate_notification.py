from app import app, mail, db
from models import User
from flask_mail import Message
import logging
import sys
import os

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_test_email(recipient_email):
    """Send a test email to verify mail configuration."""
    try:
        logger.info(f"Sending test email to {recipient_email}...")
        logger.info(f"Mail server: {app.config.get('MAIL_SERVER')}")
        logger.info(f"Mail port: {app.config.get('MAIL_PORT')}")
        logger.info(f"Mail use TLS: {app.config.get('MAIL_USE_TLS')}")
        logger.info(f"Mail sender: {app.config.get('MAIL_DEFAULT_SENDER')}")
        
        msg = Message(
            'Calm Journey: Test Email',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[recipient_email]
        )
        
        msg.body = "This is a test email from Calm Journey to verify that the email configuration is working correctly."
        
        mail.send(msg)
        logger.info(f"Test email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return False

def send_immediate_notification_to_all_users():
    """Send an immediate notification to all users reminding them to journal."""
    
    with app.app_context():
        # Log mail configuration
        logger.info("Mail configuration:")
        logger.info(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        logger.info(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        logger.info(f"MAIL_USERNAME: {'Set' if os.environ.get('MAIL_USERNAME') else 'Not set'}")
        logger.info(f"MAIL_PASSWORD: {'Set' if os.environ.get('MAIL_PASSWORD') else 'Not set'}")
        logger.info(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        
        # Get all users with notifications enabled
        users = User.query.filter_by(notifications_enabled=True).all()
        
        if not users:
            logger.info("No users found with notifications enabled.")
            return
        
        logger.info(f"Sending notifications to {len(users)} users...")
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                msg = Message(
                    'Special Reminder: Take a Moment to Journal - Calm Journey',
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[user.email]
                )
                
                # Get the base URL from the app configuration or use a default replit URL
                if 'BASE_URL' in app.config and app.config['BASE_URL']:
                    base_url = app.config['BASE_URL']
                    journal_url = f"{base_url}/journal/new"
                else:
                    # If BASE_URL isn't set, use the Replit domain if available
                    replit_domain = os.environ.get('REPL_SLUG', None)
                    if replit_domain:
                        journal_url = f"https://{replit_domain}.replit.app/journal/new"
                    else:
                        # Fallback to a relative URL only if running locally
                        journal_url = "/journal/new"
                
                # Log the URL for debugging
                logger.info(f"Generated journal URL: {journal_url}")
                
                msg.html = f"""
                <h2>Hello {user.username}!</h2>
                <p>This is a special reminder to take a moment for yourself today.</p>
                <p>Writing in your journal can help you process your thoughts and feelings, reduce stress, and gain clarity.</p>
                <p>We encourage you to spend just 5 minutes today writing about what's on your mind.</p>
                <p><a href="{journal_url}" style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px;">Start Writing Now</a></p>
                <p>Regular notifications will continue at your preferred time of 6:00 AM.</p>
                <p>Wishing you a peaceful day,<br>The Calm Journey Team</p>
                """
                
                mail.send(msg)
                success_count += 1
                logger.info(f"Sent notification to {user.email}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to send notification to {user.email}: {str(e)}")
        
        logger.info(f"Notification sending complete. Success: {success_count}, Errors: {error_count}")
        return {"success": success_count, "errors": error_count}

if __name__ == "__main__":
    try:
        logger.info("Starting immediate notification to all users...")
        
        # Check if we're testing with a specific email
        if len(sys.argv) > 1 and '@' in sys.argv[1]:
            test_recipient = sys.argv[1]
            logger.info(f"Running in test mode with recipient: {test_recipient}")
            with app.app_context():
                send_test_email(test_recipient)
        else:
            # Regular operation - send to all users
            result = send_immediate_notification_to_all_users()
            if result:
                logger.info(f"Notification stats: {result}")
            
        logger.info("Notification process complete!")
    except Exception as e:
        logger.error(f"An error occurred during the notification process: {str(e)}")
        sys.exit(1)
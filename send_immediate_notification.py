from app import app, mail, db
from models import User
from flask_mail import Message
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_immediate_notification_to_all_users():
    """Send an immediate notification to all users reminding them to journal."""
    
    with app.app_context():
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
                
                # Get the base URL from the app configuration or use the default
                base_url = app.config.get('BASE_URL', '')
                
                # If no BASE_URL is configured, use a relative URL
                journal_url = f"{base_url}/journal/new" if base_url else "/journal/new"
                
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

if __name__ == "__main__":
    try:
        logger.info("Starting immediate notification to all users...")
        send_immediate_notification_to_all_users()
        logger.info("Notification process complete!")
    except Exception as e:
        logger.error(f"An error occurred during the notification process: {str(e)}")
        sys.exit(1)
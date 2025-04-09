"""
Utility script to send an immediate email notification to a specific user
or all users with notifications enabled.
"""
import os
import sys
import logging
from app import app, db
from models import User
from improved_email_service import send_email

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_notification_to_user(user_id):
    """Send a notification to a specific user by ID."""
    with app.app_context():
        user = User.query.get(user_id)
        
        if not user:
            logger.error(f"User with ID {user_id} not found!")
            return False
            
        logger.info(f"Sending notification to user {user.username} (ID: {user_id}, Email: {user.email})")
        
        if not user.email:
            logger.error(f"User {user.username} (ID: {user_id}) has no email address!")
            return False
            
        # Get the base URL from the app configuration or use a default
        if 'BASE_URL' in app.config and app.config['BASE_URL']:
            base_url = app.config['BASE_URL']
            journal_url = f"{base_url}/journal/new"
        else:
            # For deployed apps, use the REPL_ID to ensure we get the correct URL
            repl_id = os.environ.get('REPL_ID', None)
            repl_owner = os.environ.get('REPL_OWNER', None)
            
            if repl_id and repl_owner:
                # Use the proper Replit deployed URL format
                journal_url = f"https://{repl_owner}-calm-journey.replit.app/journal/new"
            else:
                # Fallback to a relative URL only if running locally
                journal_url = "/journal/new"
        
        subject = 'Calm Journey - Custom Notification'
        html_body = f"""
        <html>
        <body>
            <h2>Hello {user.username}!</h2>
            <p>This is a custom notification from the Calm Journey app.</p>
            <p>Writing in your journal can help you process your thoughts and feelings, reduce stress, and gain clarity.</p>
            <p>We'd love to hear from you today! What's on your mind?</p>
            <p><a href="{journal_url}" style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px;">Start Writing Now</a></p>
            <p>Wishing you a peaceful day,<br>The Calm Journey Team</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Hello {user.username}!
        
        This is a custom notification from the Calm Journey app.
        
        Writing in your journal can help you process your thoughts and feelings, reduce stress, and gain clarity.
        
        We'd love to hear from you today! What's on your mind?
        
        Visit {journal_url} to start writing now.
        
        Wishing you a peaceful day,
        The Calm Journey Team
        """
        
        result = send_email(user.email, subject, html_body, text_body)
        
        if result.get("success"):
            logger.info(f"Successfully sent notification to {user.username} ({user.email})")
            return True
        else:
            logger.error(f"Failed to send notification: {result.get('error', 'Unknown error')}")
            return False

def send_notification_to_all_users():
    """Send notifications to all users with notifications enabled."""
    with app.app_context():
        users = User.query.filter_by(notifications_enabled=True).all()
        
        if not users:
            logger.warning("No users with notifications enabled found!")
            return False
            
        logger.info(f"Sending notifications to {len(users)} users with notifications enabled...")
        
        success_count = 0
        error_count = 0
        
        for user in users:
            if send_notification_to_user(user.id):
                success_count += 1
            else:
                error_count += 1
                
        logger.info(f"Notification sending complete. Success: {success_count}, Errors: {error_count}")
        
        if success_count > 0:
            return True
        else:
            return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            # If a numeric argument is provided, treat it as a user ID
            user_id = int(sys.argv[1])
            send_notification_to_user(user_id)
        except ValueError:
            print(f"Invalid user ID: {sys.argv[1]}")
            print("Usage: python send_immediate_notification.py [user_id]")
            print("       If user_id is not provided, notifications will be sent to all users with notifications enabled.")
            sys.exit(1)
    else:
        # Otherwise, send to all users with notifications enabled
        send_notification_to_all_users()
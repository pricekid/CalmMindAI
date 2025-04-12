"""
Script to send update notifications to all users with notifications enabled.
This uses our direct email sending method to bypass Flask-Mail.
"""
import os
import logging
import time
import json
from notification_service import send_email, ensure_data_directory

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_base_url():
    """Get the base URL for links in emails"""
    # Use environment variable if available, otherwise use default
    return os.environ.get('BASE_URL', 'https://calm-mind-ai-naturalarts.replit.app')

def load_users():
    """Load users from the data/users.json file"""
    ensure_data_directory()
    if not os.path.exists('data/users.json'):
        logger.error("data/users.json not found")
        return []
    
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Error decoding users.json file")
        return []
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def send_update_notification(email, username="there"):
    """
    Send an update notification email to a user.
    
    Args:
        email: The user's email address
        username: The user's username
    
    Returns:
        bool: True if successful, False otherwise
    """
    subject = "Calm Journey - New App Updates & Journaling Reminder"
    
    # Get the base URL for the application
    base_url = get_base_url()
    journal_url = f"{base_url}/journal/new"
    dashboard_url = f"{base_url}/dashboard"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="color: #5f9ea0; margin: 0;">Calm Journey</h1>
            <p style="font-size: 18px; margin: 5px 0 0;">App Updates & Reminder</p>
        </div>
        
        <div style="padding: 20px; background-color: #fff; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #5f9ea0; border-bottom: 1px solid #eee; padding-bottom: 10px;">Hello {username}!</h2>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #5f9ea0;">📝 Journaling Reminder</h3>
                <p>We hope you're doing well today! This is a friendly reminder to take a few minutes for yourself and check in with your mental well-being.</p>
                <p>Regular journaling has been shown to help reduce stress, improve mood, and increase self-awareness. Even just 5 minutes can make a difference!</p>
                
                <p style="text-align: center; margin: 25px 0;">
                    <a href="{journal_url}" style="display: inline-block; background-color: #5f9ea0; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Write in Journal</a>
                </p>
            </div>
            
            <div style="margin: 30px 0; padding: 15px; background-color: #f0f7f7; border-left: 4px solid #5f9ea0; border-radius: 3px;">
                <h3 style="color: #5f9ea0; margin-top: 0;">🎉 New App Updates</h3>
                <p>We're excited to share some recent improvements to Calm Journey:</p>
                <ul style="padding-left: 20px;">
                    <li><strong>Enhanced Email System:</strong> We've improved our email notifications with better styling and reliability.</li>
                    <li><strong>Simplified Login:</strong> You can now log in directly through email links without entering a password.</li>
                    <li><strong>Improved Voice Features:</strong> Our text-to-speech features now use more natural-sounding voices.</li>
                    <li><strong>Better Journal Analysis:</strong> Coach Mira's insights have been enhanced with our latest AI models.</li>
                </ul>
                <p>Log in to check out these new features!</p>
            </div>
            
            <p style="text-align: center; margin: 25px 0;">
                <a href="{dashboard_url}" style="display: inline-block; background-color: #6c757d; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Go to Dashboard</a>
            </p>
            
            <p style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
                Thank you for being part of the Calm Journey community. We're committed to supporting your mental wellness journey.
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
            <p>The Calm Journey Team</p>
            <p>If you'd like to change your notification preferences, you can update them in your account settings.</p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""Calm Journey - New App Updates & Journaling Reminder

Hello {username}!

📝 JOURNALING REMINDER
We hope you're doing well today! This is a friendly reminder to take a few minutes for yourself and check in with your mental well-being.

Regular journaling has been shown to help reduce stress, improve mood, and increase self-awareness. Even just 5 minutes can make a difference!

Write in your journal here: {journal_url}

🎉 NEW APP UPDATES
We're excited to share some recent improvements to Calm Journey:

- Enhanced Email System: We've improved our email notifications with better styling and reliability.
- Simplified Login: You can now log in directly through email links without entering a password.
- Improved Voice Features: Our text-to-speech features now use more natural-sounding voices.
- Better Journal Analysis: Coach Mira's insights have been enhanced with our latest AI models.

Log in to check out these new features: {dashboard_url}

Thank you for being part of the Calm Journey community. We're committed to supporting your mental wellness journey.

The Calm Journey Team

--
If you'd like to change your notification preferences, you can update them in your account settings.
"""
    
    # Send the email
    result = send_email(email, subject, html_body, text_body)
    return result.get('success', False)

def send_to_all_users():
    """
    Send update notifications to all users with notifications enabled.
    
    Returns:
        dict: Statistics about the sending process
    """
    # Load users
    users = load_users()
    logger.info(f"Loaded {len(users)} users")
    
    # Stats
    total_users = len(users)
    sent_count = 0
    skipped_count = 0
    failed_count = 0
    
    for user in users:
        # Only send notifications to users with notifications enabled
        if not user.get('notifications_enabled', False):
            logger.info(f"Skipping user {user.get('id')} ({user.get('email')}): Notifications disabled")
            skipped_count += 1
            continue
        
        # Get user email and username
        email = user.get('email')
        username = user.get('username', 'there')
        
        if not email:
            logger.warning(f"Skipping user {user.get('id')}: No email address")
            skipped_count += 1
            continue
        
        # Send notification
        logger.info(f"Sending update notification to {email}...")
        try:
            result = send_update_notification(email, username)
            
            if result:
                logger.info(f"Update notification sent to {email}")
                sent_count += 1
            else:
                logger.error(f"Failed to send update notification to {email}")
                failed_count += 1
        except Exception as e:
            logger.error(f"Error sending update notification to {email}: {str(e)}")
            failed_count += 1
        
        # Sleep briefly between emails to avoid rate limiting
        time.sleep(1)
    
    # Return stats
    stats = {
        "total_users": total_users,
        "sent_count": sent_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return stats

def main(auto_confirm=False):
    print("Calm Journey - Send Update Notifications to All Users")
    print("--------------------------------------------------")
    
    # Confirm before sending, unless auto_confirm is True
    if not auto_confirm:
        print("\nReady to send update notifications to all users with notifications enabled.")
        print("This will inform users about new app features and remind them to journal.")
        print("Are you sure you want to continue? (y/n)")
        try:
            confirm = input("> ").strip().lower()
            if confirm != 'y' and confirm != 'yes':
                print("Operation cancelled.")
                return
        except EOFError:
            print("Interactive input not available. Use --auto-confirm to bypass confirmation.")
            return
    else:
        print("\nAuto-confirm enabled. Proceeding without confirmation...")
    
    # Send notifications
    print("\nSending update notifications...")
    stats = send_to_all_users()
    
    # Print stats
    print("\nSending complete!")
    print(f"Total users: {stats['total_users']}")
    print(f"Notifications sent: {stats['sent_count']}")
    print(f"Users skipped: {stats['skipped_count']}")
    print(f"Failed to send: {stats['failed_count']}")

if __name__ == "__main__":
    import sys
    
    # Check if auto_confirm flag is provided
    auto_confirm = False
    if len(sys.argv) > 1 and sys.argv[1] == "--auto-confirm":
        auto_confirm = True
    
    main(auto_confirm)
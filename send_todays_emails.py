"""
Script to force send today's emails to all users with notifications enabled.
This will check which users have not received emails today and send them immediately.
"""
import os
import sys
import logging
import json
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_env_vars():
    """Ensure all required environment variables are set."""
    if not os.environ.get('MAIL_SERVER'):
        os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
        logger.info("Set MAIL_SERVER to smtp.gmail.com")
    
    if not os.environ.get('MAIL_PORT'):
        os.environ['MAIL_PORT'] = '587'
        logger.info("Set MAIL_PORT to 587")
    
    return True

def ensure_data_directory():
    """Ensure the data directory exists"""
    Path("data").mkdir(exist_ok=True)
    Path("data/notifications").mkdir(exist_ok=True)
    
def load_users():
    """Load users from the data/users.json file"""
    try:
        if os.path.exists("data/users.json"):
            with open("data/users.json", "r") as f:
                return json.load(f)
        else:
            logger.error("Users file not found at data/users.json")
            return []
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def check_notification_tracking():
    """Check the notification tracking system for today's notifications."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    tracking_file = f"data/notifications/email_{today}.json"
    
    try:
        if os.path.exists(tracking_file):
            with open(tracking_file, "r") as f:
                tracking_data = json.load(f)
                logger.info(f"Found tracking data for today: {len(tracking_data)} users received emails")
                return tracking_data
        else:
            logger.info(f"No tracking data found for today at {tracking_file}")
            return {}
    except Exception as e:
        logger.error(f"Error checking notification tracking: {str(e)}")
        return {}

def force_send_todays_emails():
    """Send emails to users who haven't received them today."""
    from notification_service import send_personalized_email
    
    # Ensure environment variables
    ensure_env_vars()
    ensure_data_directory()
    
    # Load users
    users = load_users()
    if not users:
        logger.error("No users found")
        return {"error": "No users found"}
    
    # Check who already received emails today
    tracking_data = check_notification_tracking()
    already_notified_user_ids = set(str(user_id) for user_id in tracking_data.keys())
    
    # Counter for tracking results
    results = {
        "total_users": len(users),
        "notification_enabled_count": 0,
        "already_notified_count": 0,
        "sent_count": 0,
        "error_count": 0
    }
    
    # Track which users were successfully notified
    newly_notified_users = {}
    
    # Process each user
    for user in users:
        user_id = str(user.get("id", ""))
        email = user.get("email", "")
        
        # Skip users without ID or email
        if not user_id or not email:
            logger.warning(f"Skipping user with missing ID or email: {user}")
            continue
        
        # Check if notifications are enabled for this user
        if user.get("notifications_enabled", False):
            results["notification_enabled_count"] += 1
            
            # Check if user already received notification today
            if user_id in already_notified_user_ids:
                logger.info(f"User {user_id} ({email}) already received email today")
                results["already_notified_count"] += 1
                continue
            
            # Send email to user
            try:
                logger.info(f"Sending email to user {user_id} ({email})...")
                send_personalized_email(email, user)
                
                # Update tracking
                newly_notified_users[user_id] = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "email": email,
                    "success": True
                }
                
                results["sent_count"] += 1
                logger.info(f"Email sent successfully to user {user_id} ({email})")
            except Exception as e:
                logger.error(f"Error sending email to user {user_id} ({email}): {str(e)}")
                results["error_count"] += 1
    
    # Update notification tracking file with newly notified users
    if newly_notified_users:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        tracking_file = f"data/notifications/email_{today}.json"
        
        try:
            # Merge existing and new data
            merged_tracking = {**tracking_data, **newly_notified_users}
            
            # Save updated tracking data
            with open(tracking_file, "w") as f:
                json.dump(merged_tracking, f, indent=2)
            
            logger.info(f"Updated notification tracking for {len(newly_notified_users)} new users")
        except Exception as e:
            logger.error(f"Error updating notification tracking: {str(e)}")
    
    return results

def main():
    """Main function to force send today's emails."""
    logger.info("=" * 80)
    logger.info("FORCE SEND TODAY'S EMAILS")
    logger.info("=" * 80)
    
    # Force send today's emails
    results = force_send_todays_emails()
    
    logger.info("=" * 80)
    logger.info(f"RESULTS:")
    logger.info(f"Total users: {results.get('total_users', 0)}")
    logger.info(f"Users with notifications enabled: {results.get('notification_enabled_count', 0)}")
    logger.info(f"Users already notified today: {results.get('already_notified_count', 0)}")
    logger.info(f"Emails sent successfully: {results.get('sent_count', 0)}")
    logger.info(f"Errors: {results.get('error_count', 0)}")
    logger.info("=" * 80)
    
    if results.get("sent_count", 0) > 0:
        logger.info(f"Successfully sent {results.get('sent_count')} emails!")
        return 0
    elif results.get("already_notified_count", 0) > 0 and results.get("error_count", 0) == 0:
        logger.info("No new emails sent - all users already received notifications today")
        return 0
    else:
        logger.error("Failed to send any emails")
        return 1

if __name__ == "__main__":
    sys.exit(main())
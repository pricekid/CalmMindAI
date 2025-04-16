"""
Script to force send email notifications to all users with notifications enabled.
This bypasses the scheduler and sends emails immediately.
"""
import os
import sys
import logging
import datetime
import time
import json

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

def record_notification_event(success_count, error_count):
    """Record that notifications were manually sent."""
    try:
        log_file = "data/manual_notifications.json"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = {
            "timestamp": timestamp,
            "success_count": success_count,
            "error_count": error_count,
            "total": success_count + error_count
        }
        
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(entry)
        
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)
        
        logger.info(f"Recorded notification event: {success_count} succeeded, {error_count} failed")
        return True
    except Exception as e:
        logger.error(f"Error recording notification event: {str(e)}")
        return False

def force_send_notifications():
    """Force send notifications to all users with notifications enabled."""
    # Import here to avoid circular imports
    from scheduler_service import send_daily_reminder_direct
    
    logger.info("Forcing send of email notifications to all users...")
    
    try:
        # Ensure environment variables are set
        ensure_env_vars()
        
        # Run the notification sending function directly
        result = send_daily_reminder_direct()
        
        success_count = result.get('sent_count', 0)
        error_count = result.get('total_users', 0) - success_count - result.get('skipped_count', 0)
        
        logger.info(f"Notification sending complete:")
        logger.info(f"  Total users: {result.get('total_users', 0)}")
        logger.info(f"  Sent successfully: {success_count}")
        logger.info(f"  Skipped: {result.get('skipped_count', 0)}")
        logger.info(f"  Failed: {error_count}")
        
        # Record the notification event
        record_notification_event(success_count, error_count)
        
        return result
    except Exception as e:
        logger.error(f"Error forcing notifications: {str(e)}")
        return {"error": str(e)}

def main():
    """Main function to force send notifications."""
    logger.info("=" * 80)
    logger.info("FORCE SEND NOTIFICATIONS")
    logger.info("=" * 80)
    
    # Force send notifications
    result = force_send_notifications()
    
    if 'error' in result:
        logger.error(f"Failed to send notifications: {result['error']}")
        return 1
    
    logger.info("=" * 80)
    logger.info("NOTIFICATIONS SENT SUCCESSFULLY")
    logger.info("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
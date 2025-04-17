"""
Script to send immediate notifications to all users with notifications enabled.
This bypasses the scheduler and sends emails right now.
"""
import os
import sys
import logging
import datetime
import json
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

def run_notification_job():
    """Run the daily reminder job manually."""
    try:
        # Import the function from scheduler_service
        from scheduler_service import send_daily_reminder_direct
        
        # Make sure environment variables are set
        ensure_env_vars()
        ensure_data_directory()
        
        # Run the notification function directly
        logger.info("Sending notifications to all users...")
        result = send_daily_reminder_direct()
        
        # Log the result
        if isinstance(result, dict):
            sent_count = result.get('sent_count', 0)
            skipped_count = result.get('skipped_count', 0)
            total_users = result.get('total_users', 0)
            
            logger.info(f"Notification job completed!")
            logger.info(f"Total users: {total_users}")
            logger.info(f"Emails sent: {sent_count}")
            logger.info(f"Users skipped: {skipped_count}")
            
            return result
        else:
            logger.error(f"Unexpected result from notification job: {result}")
            return {"error": "Unexpected result type"}
            
    except Exception as e:
        logger.error(f"Error running notification job: {str(e)}", exc_info=True)
        return {"error": str(e)}

def reset_notification_tracking():
    """Reset today's notification tracking to allow sending again."""
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        tracking_file = f"data/notifications/email_{today}.json"
        
        if os.path.exists(tracking_file):
            # Backup the file first
            backup_file = f"{tracking_file}.bak"
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
                
            with open(backup_file, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            
            logger.info(f"Backed up tracking file to {backup_file}")
            
            # Remove or truncate the file
            os.remove(tracking_file)
            logger.info(f"Removed tracking file {tracking_file}")
            
            return True
        else:
            logger.info(f"No tracking file found at {tracking_file}, nothing to reset")
            return True
    except Exception as e:
        logger.error(f"Error resetting notification tracking: {str(e)}")
        return False

def main():
    """Main function to send immediate notifications."""
    logger.info("=" * 80)
    logger.info("SEND IMMEDIATE NOTIFICATIONS")
    logger.info("=" * 80)
    
    # Ask if user wants to reset tracking
    reset = input("Do you want to reset notification tracking to send emails to ALL users? (y/n): ")
    
    if reset.lower() == 'y':
        logger.info("Resetting notification tracking...")
        if not reset_notification_tracking():
            logger.error("Failed to reset notification tracking, aborting")
            return 1
    
    # Run the notification job
    result = run_notification_job()
    
    if "error" in result:
        logger.error(f"Failed to send notifications: {result['error']}")
        return 1
        
    logger.info("=" * 80)
    logger.info(f"RESULTS:")
    for key, value in result.items():
        logger.info(f"{key}: {value}")
    logger.info("=" * 80)
    
    if result.get("sent_count", 0) > 0:
        logger.info(f"Successfully sent notifications!")
        return 0
    else:
        logger.warning("No new notifications were sent. This may be because all users already received notifications today.")
        logger.info("If you want to send to ALL users, run again and choose 'y' to reset tracking.")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        # Non-interactive mode for automation
        logger.info("Running in non-interactive force mode")
        reset_notification_tracking()
        run_notification_job()
        sys.exit(0)
    else:
        # Interactive mode
        sys.exit(main())
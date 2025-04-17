"""
Daily health check for notification system.
This script checks if notifications were sent today and triggers a resend if they weren't.
Run this script daily after the scheduled notification time (e.g., 8:00 AM UTC).
"""
import os
import sys
import json
import logging
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data and logs directories exist"""
    Path("data").mkdir(exist_ok=True)
    Path("data/notifications").mkdir(exist_ok=True)
    Path("data/logs").mkdir(exist_ok=True)
    Path("data/logs/notification_checks").mkdir(exist_ok=True)

def log_check_results(results):
    """Log check results to a file for historical tracking"""
    try:
        ensure_data_directory()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = f"data/logs/notification_checks/check_{timestamp}.json"
        
        # Add timestamp to results
        results["timestamp"] = datetime.datetime.now().isoformat()
        
        with open(log_file, "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Logged check results to {log_file}")
        return True
    except Exception as e:
        logger.error(f"Error logging check results: {str(e)}")
        return False

def check_sent_notifications():
    """Check if notifications were sent today."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    tracking_file = f"data/notifications/email_{today}.json"
    
    try:
        if os.path.exists(tracking_file):
            with open(tracking_file, "r") as f:
                tracking_data = json.load(f)
                notification_count = len(tracking_data)
                logger.info(f"Found {notification_count} notifications sent today")
                return {
                    "notifications_sent": True,
                    "count": notification_count,
                    "file": tracking_file
                }
        else:
            logger.warning(f"No notification tracking file found for today at {tracking_file}")
            return {
                "notifications_sent": False,
                "count": 0,
                "file": None
            }
    except Exception as e:
        logger.error(f"Error checking sent notifications: {str(e)}")
        return {
            "notifications_sent": False,
            "count": 0,
            "error": str(e)
        }

def load_users():
    """Load users from the data/users.json file"""
    try:
        if os.path.exists("data/users.json"):
            with open("data/users.json", "r") as f:
                users = json.load(f)
                return users
        else:
            logger.error("Users file not found at data/users.json")
            return []
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def count_notifications_enabled_users():
    """Count how many users have notifications enabled."""
    users = load_users()
    if not users:
        return 0
        
    enabled_count = 0
    for user in users:
        if user.get("notifications_enabled", False):
            enabled_count += 1
            
    return enabled_count
        
def check_scheduler_status():
    """Check if the scheduler is running."""
    try:
        if not os.path.exists("scheduler.pid"):
            logger.error("Scheduler PID file not found")
            return {
                "scheduler_running": False,
                "pid": None,
                "error": "PID file not found"
            }
            
        with open("scheduler.pid", "r") as f:
            pid = f.read().strip()
            
        if not pid:
            logger.error("Empty scheduler PID file")
            return {
                "scheduler_running": False,
                "pid": None,
                "error": "Empty PID file"
            }
            
        # Check if process is running
        try:
            pid = int(pid)
            if os.system(f"ps -p {pid} > /dev/null") == 0:
                logger.info(f"Scheduler is running with PID {pid}")
                return {
                    "scheduler_running": True,
                    "pid": pid
                }
            else:
                logger.error(f"Scheduler process with PID {pid} is not running")
                return {
                    "scheduler_running": False,
                    "pid": pid,
                    "error": "Process not running"
                }
        except ValueError:
            logger.error(f"Invalid PID in scheduler.pid file: {pid}")
            return {
                "scheduler_running": False,
                "pid": pid,
                "error": "Invalid PID"
            }
    except Exception as e:
        logger.error(f"Error checking scheduler status: {str(e)}")
        return {
            "scheduler_running": False,
            "pid": None,
            "error": str(e)
        }

def trigger_resend_if_needed(notification_check, count_enabled):
    """Trigger a resend of notifications if they haven't been sent today."""
    # Don't trigger resend if notifications were already sent
    if notification_check.get("notifications_sent", False):
        logger.info("Notifications were already sent today, no resend needed")
        return {
            "resend_triggered": False,
            "reason": "Already sent"
        }
        
    # If no notifications were sent and there are enabled users, trigger resend
    if count_enabled > 0:
        logger.info(f"Triggering resend for {count_enabled} users with notifications enabled")
        try:
            # Import and run the notification function
            from scheduler_service import send_daily_reminder_direct
            
            # Set necessary environment variables
            if not os.environ.get('MAIL_SERVER'):
                os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
            if not os.environ.get('MAIL_PORT'):
                os.environ['MAIL_PORT'] = '587'
                
            # Run the notification job
            result = send_daily_reminder_direct()
            
            if isinstance(result, dict):
                sent_count = result.get("sent_count", 0)
                logger.info(f"Resend triggered successfully, sent {sent_count} notifications")
                return {
                    "resend_triggered": True,
                    "sent_count": sent_count,
                    "total_users": result.get("total_users", 0),
                    "skipped_count": result.get("skipped_count", 0)
                }
            else:
                logger.error(f"Unexpected result from resend: {result}")
                return {
                    "resend_triggered": True,
                    "success": False,
                    "error": "Unexpected result type"
                }
        except Exception as e:
            logger.error(f"Error triggering resend: {str(e)}")
            return {
                "resend_triggered": True,
                "success": False,
                "error": str(e)
            }
    else:
        logger.info("No users with notifications enabled, skipping resend")
        return {
            "resend_triggered": False,
            "reason": "No enabled users"
        }

def main():
    """Main function to check and ensure notifications were sent."""
    try:
        logger.info("=" * 80)
        logger.info("NOTIFICATION SYSTEM DAILY HEALTH CHECK")
        logger.info("=" * 80)
        
        ensure_data_directory()
        
        # Check if notifications were sent today
        notification_check = check_sent_notifications()
        
        # Check how many users have notifications enabled
        count_enabled = count_notifications_enabled_users()
        logger.info(f"Found {count_enabled} users with notifications enabled")
        
        # Check scheduler status
        scheduler_status = check_scheduler_status()
        
        # Trigger resend if needed
        resend_results = {}
        if not notification_check.get("notifications_sent", False) and count_enabled > 0:
            resend_results = trigger_resend_if_needed(notification_check, count_enabled)
        
        # Compile results
        results = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "notification_check": notification_check,
            "users_with_notifications": count_enabled,
            "scheduler_status": scheduler_status,
            "resend_results": resend_results
        }
        
        # Log results
        log_check_results(results)
        
        # Print summary
        logger.info("=" * 80)
        logger.info("HEALTH CHECK SUMMARY:")
        logger.info(f"Date: {results['date']}")
        logger.info(f"Time: {results['time']}")
        logger.info(f"Notifications Sent Today: {notification_check.get('notifications_sent', False)}")
        logger.info(f"Notification Count: {notification_check.get('count', 0)}")
        logger.info(f"Users with Notifications Enabled: {count_enabled}")
        logger.info(f"Scheduler Running: {scheduler_status.get('scheduler_running', False)}")
        
        if resend_results:
            logger.info(f"Resend Triggered: {resend_results.get('resend_triggered', False)}")
            if resend_results.get('resend_triggered', False):
                logger.info(f"Resend Sent Count: {resend_results.get('sent_count', 0)}")
        
        logger.info("=" * 80)
        
        # Return success
        return 0
    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
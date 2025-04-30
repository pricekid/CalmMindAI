"""
Script to temporarily stop email notifications by pausing the scheduler.
"""
import os
import logging
import signal
import json
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists"""
    Path("data").mkdir(exist_ok=True)
    Path("data/notifications").mkdir(exist_ok=True)

def load_scheduler_pid():
    """Load the scheduler PID from the PID file"""
    pid_file = "scheduler.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
                return pid
        except Exception as e:
            logger.error(f"Error loading scheduler PID: {str(e)}")
            return None
    else:
        logger.error("Scheduler PID file not found")
        return None

def stop_scheduler():
    """Stop the scheduler process"""
    pid = load_scheduler_pid()
    if not pid:
        logger.error("Cannot stop scheduler: PID not found")
        return False
    
    try:
        # Try to terminate the process gracefully
        os.kill(pid, signal.SIGTERM)
        logger.info(f"Sent SIGTERM to scheduler process {pid}")
        
        # Remove the PID file
        if os.path.exists("scheduler.pid"):
            os.remove("scheduler.pid")
            logger.info("Removed scheduler PID file")
        
        return True
    except ProcessLookupError:
        logger.warning(f"Process {pid} not found, it may have already been stopped")
        
        # Remove the PID file if it exists
        if os.path.exists("scheduler.pid"):
            os.remove("scheduler.pid")
            logger.info("Removed stale scheduler PID file")
        
        return True
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        return False

def disable_all_email_notifications():
    """Disable email notifications for all users"""
    ensure_data_directory()
    
    # Load users
    users_file = "data/users.json"
    if not os.path.exists(users_file):
        logger.error("Users file not found")
        return False
    
    try:
        with open(users_file, "r") as f:
            users = json.load(f)
        
        # Count how many users have notifications enabled
        originally_enabled = sum(1 for user in users if user.get('notifications_enabled', False))
        
        # Disable notifications for all users
        for user in users:
            user['notifications_enabled'] = False
            user['sms_notifications_enabled'] = False
        
        # Save updated users
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)
        
        logger.info(f"Disabled email notifications for {originally_enabled} users")
        return True
    except Exception as e:
        logger.error(f"Error disabling notifications: {str(e)}")
        return False

def main():
    """Main function to stop notifications"""
    print("Stopping email notifications...")
    
    # First disable all notifications in user profiles
    if disable_all_email_notifications():
        print("Successfully disabled notifications for all users")
    else:
        print("Failed to disable notifications for users")
    
    # Then stop the scheduler
    if stop_scheduler():
        print("Successfully stopped the notification scheduler")
    else:
        print("Failed to stop the notification scheduler")
    
    # Create a marker file to indicate notifications are disabled
    try:
        with open("data/notifications_disabled", "w") as f:
            f.write(f"Notifications disabled at {datetime.now().isoformat()}")
        print("Created notifications_disabled marker file")
    except Exception as e:
        print(f"Warning: Could not create marker file: {e}")
    
    print("\nEmail notifications have been stopped. To restart them later:")
    print("1. Delete the file 'data/notifications_disabled'")
    print("2. Re-enable notifications in user profiles if desired")
    print("3. Run 'python start_scheduler.py' to restart the scheduler")

if __name__ == "__main__":
    from datetime import datetime
    main()
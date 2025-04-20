#!/usr/bin/env python3
"""
Script to fix the scheduler and send today's emails immediately.
This script:
1. Checks if the scheduler is running properly
2. Resets the notification tracking to ensure emails can be sent today
3. Manually triggers email sending
"""
import os
import sys
import json
import datetime
from pathlib import Path
import logging
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists"""
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()
    return data_dir

def reset_daily_notification_tracking():
    """
    Reset the daily notification tracking to allow sending emails again today.
    """
    try:
        data_dir = ensure_data_directory()
        notification_tracking_file = data_dir / "notification_tracking.json"
        
        # Check if the file exists
        if not notification_tracking_file.exists():
            logger.info("No notification tracking file found. Creating a new one.")
            return True
        
        # Load current tracking data
        with open(notification_tracking_file, 'r') as f:
            try:
                tracking_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Invalid notification tracking file. Creating a new one.")
                tracking_data = {}
        
        # Get today's date as string
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Check and reset today's sent notifications
        if today in tracking_data:
            old_count = len(tracking_data[today])
            logger.info(f"Found {old_count} notifications already sent today.")
            
            # Reset today's notifications
            tracking_data[today] = []
            
            # Save updated tracking data
            with open(notification_tracking_file, 'w') as f:
                json.dump(tracking_data, f)
            
            logger.info(f"Reset today's notification tracking. Removed {old_count} notification records.")
        else:
            logger.info("No notifications have been sent today yet.")
        
        return True
    except Exception as e:
        logger.error(f"Error resetting notification tracking: {str(e)}")
        return False

def stop_scheduler():
    """Stop the current scheduler if it's running"""
    try:
        # Check if the scheduler is running
        scheduler_pid_file = Path("scheduler.pid")
        if scheduler_pid_file.exists():
            with open(scheduler_pid_file, 'r') as f:
                pid = f.read().strip()
                
            if pid:
                logger.info(f"Found scheduler PID: {pid}")
                try:
                    # Try to terminate the process
                    subprocess.run(['kill', pid], check=False)
                    logger.info(f"Sent termination signal to PID {pid}")
                    time.sleep(2)  # Give it a moment to shut down
                except Exception as kill_err:
                    logger.warning(f"Error terminating scheduler process: {str(kill_err)}")
            
            # Remove the PID file
            scheduler_pid_file.unlink()
            logger.info("Removed scheduler PID file")
        
        return True
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        return False

def send_emails_now():
    """Run the direct email sending function"""
    try:
        logger.info("Manually sending today's email notifications...")
        
        # Import the notification service
        from scheduler_service import send_daily_reminder_direct
        
        # Send the notifications
        result = send_daily_reminder_direct()
        
        if isinstance(result, dict):
            sent_count = result.get("sent_count", 0)
            total_users = result.get("total_users", 0)
            logger.info(f"Sent {sent_count} notifications out of {total_users} eligible users.")
            
            # Log any errors
            if "errors" in result and result["errors"]:
                for error in result["errors"]:
                    logger.error(f"Error sending to user {error.get('user_id')}: {error.get('error')}")
            
            return result
        else:
            logger.error(f"Unexpected result from send_daily_reminder_direct: {result}")
            return {"error": "Unexpected result", "sent_count": 0}
    except Exception as e:
        logger.error(f"Error sending emails: {str(e)}")
        return {"error": str(e), "sent_count": 0}

def restart_scheduler():
    """Start the scheduler again"""
    try:
        logger.info("Restarting the notification scheduler...")
        
        # Start the scheduler as a background process
        subprocess.Popen(
            ["python3", "scheduler.py"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        logger.info("Scheduler process started")
        return True
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        return False

def check_logs_directory():
    """Fix logs directory if needed"""
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir()
        logger.info("Created logs directory")
    return True

def main():
    """Main function to fix scheduler and send emails"""
    logger.info("Starting scheduler fix and email sending process")
    
    # Check logs directory
    check_logs_directory()
    
    # Step 1: Stop the current scheduler
    logger.info("Step 1: Stopping current scheduler...")
    stop_scheduler()
    
    # Step 2: Reset notification tracking
    logger.info("Step 2: Resetting notification tracking...")
    reset_daily_notification_tracking()
    
    # Step 3: Send today's emails directly
    logger.info("Step 3: Sending today's emails...")
    email_result = send_emails_now()
    
    # Step 4: Restart the scheduler
    logger.info("Step 4: Restarting the scheduler...")
    restart_scheduler()
    
    # Final results
    sent_count = email_result.get("sent_count", 0) if isinstance(email_result, dict) else 0
    logger.info(f"Process complete. Sent {sent_count} emails.")
    
    return email_result

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script to fix the scheduler job scheduling issues.
This script:
1. Makes targeted updates to correct the job scheduling logic in scheduler.py
2. Handles proper job object creation and validation
"""
import os
import sys
import re
import shutil
from pathlib import Path
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def backup_scheduler_file():
    """Create a backup of the scheduler file before modifying it"""
    scheduler_path = Path("scheduler.py")
    if not scheduler_path.exists():
        logger.error("scheduler.py not found in the current directory!")
        return False
    
    # Create backup with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"scheduler.py.bak_{timestamp}")
    
    try:
        shutil.copy2(scheduler_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return False

def update_scheduler_job_function():
    """Fix the job scheduling code in scheduler.py"""
    scheduler_path = Path("scheduler.py")
    
    if not scheduler_path.exists():
        logger.error("scheduler.py not found!")
        return False
    
    try:
        with open(scheduler_path, 'r') as f:
            content = f.read()
        
        # Check if we need to fix the code
        if "Failed to properly schedule daily email job" in content:
            # Pattern to find and fix the job scheduling code block
            job_scheduling_pattern = r"try:.*?# Email notifications at 6:00 AM.*?email_job = scheduler\.add_job\(.*?if email_job and hasattr\(email_job, 'next_run_time'\):.*?else:.*?logger\.error\(\"Failed to properly schedule daily email job\. Job object is incomplete\.\"\).*?except Exception as e:"
            
            # Replacement with corrected code
            replacement = """try:
    # Email notifications at 6:00 AM with fixed scheduling
    email_job = scheduler.add_job(
        safe_send_daily_reminder, 
        'cron', 
        hour='6', 
        minute=0,
        id='daily_email_reminder',
        replace_existing=True,
        name='Daily Email Reminder',
        misfire_grace_time=7200  # 2 hour grace time for missed schedule
    )
    
    # Verify the job was scheduled correctly
    if email_job and hasattr(email_job, 'next_run_time') and email_job.next_run_time:
        next_run = email_job.next_run_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(f"Daily email job scheduled successfully. Next run: {next_run}")
        log_scheduler_activity("job_scheduled", f"Daily email job scheduled successfully. Next run: {next_run}", success=True)
    else:
        logger.error("Failed to properly schedule daily email job. Using backup job.")
        log_scheduler_activity("job_schedule_error", "Failed to properly schedule daily email job. Using backup job.", success=False)
except Exception as e:"""
            
            # Use regex with re.DOTALL to match across multiple lines
            updated_content = re.sub(job_scheduling_pattern, replacement, content, flags=re.DOTALL)
            
            # Check if the pattern was replaced (if content changed)
            if updated_content != content:
                # Write the fixed content back to the file
                with open(scheduler_path, 'w') as f:
                    f.write(updated_content)
                
                logger.info("Successfully updated scheduler job scheduling code")
                return True
            else:
                logger.warning("Could not find the pattern to update in scheduler.py")
                return False
        else:
            logger.info("No need to fix job scheduling logic - pattern not found")
            return True
            
    except Exception as e:
        logger.error(f"Error updating scheduler code: {str(e)}")
        return False

def fix_daily_notification_check():
    """Fix the logic that checks if notifications were already sent today"""
    scheduler_path = Path("scheduler.py")
    
    if not scheduler_path.exists():
        logger.error("scheduler.py not found!")
        return False
    
    try:
        with open(scheduler_path, 'r') as f:
            content = f.read()
        
        # Pattern to find the notification check logic
        notification_check_pattern = r"# Check if notifications were already sent today.*?if today in tracking_data and tracking_data\[today\]:.*?logger\.info\(f\"Today's notifications have already been sent to \{len\(tracking_data\[today\]\)\} users\.\"\).*?else:.*?logger\.warning\(\"No email notifications sent today.*?Running immediate notification job\.\.\.\"\)"
        
        # Replacement with improved logic
        replacement = """# Check if notifications were already sent today
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        tracking_file = os.path.join("data", "notification_tracking.json")
        
        if os.path.exists(tracking_file):
            try:
                with open(tracking_file, 'r') as track_file:
                    tracking_data = json.load(track_file)
                
                # More robust check with time-based decision
                current_hour = datetime.datetime.now().hour
                if today in tracking_data and tracking_data[today] and current_hour < 12:  # Only trust "already sent" before noon
                    logger.info(f"Today's notifications have already been sent to {len(tracking_data[today])} users.")
                else:
                    # Either notifications not sent or it's afternoon (possible false tracking)
                    if current_hour >= 12 and today in tracking_data and tracking_data[today]:
                        logger.info(f"Found {len(tracking_data[today])} notification records, but running again as it's after noon.")
                    else:
                        logger.warning("No email notifications sent today and it's after 6 AM UTC. Running immediate notification job...")
                    
                    # Run the job immediately to ensure notifications go out
                    safety_result = safe_send_daily_reminder()
                    if safety_result:
                        logger.info(f"Successfully sent notifications through immediate job: {safety_result}")
                    else:
                        logger.error("Failed to send notifications through immediate job")
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                logger.error(f"Error checking notification status: {str(e)}")
                # Run notification job if there was an error checking status
                safe_send_daily_reminder()
        else:
            logger.warning("No notification tracking file exists. Running immediate notification job...")
            # No tracking file exists, run the job to be safe
            safe_send_daily_reminder()"""
        
        # Use regex with re.DOTALL to match across multiple lines
        updated_content = re.sub(notification_check_pattern, replacement, content, flags=re.DOTALL)
        
        # Check if the pattern was replaced (if content changed)
        if updated_content != content:
            # Write the fixed content back to the file
            with open(scheduler_path, 'w') as f:
                f.write(updated_content)
            
            logger.info("Successfully updated notification check logic")
            return True
        else:
            logger.warning("Could not find the notification check pattern to update")
            return False
            
    except Exception as e:
        logger.error(f"Error updating notification check logic: {str(e)}")
        return False

def main():
    """Main function to fix scheduler"""
    logger.info("Starting scheduler fix process")
    
    # Step 1: Create a backup of the scheduler file
    if not backup_scheduler_file():
        logger.error("Failed to create backup. Aborting.")
        return False
    
    # Step 2: Fix the job scheduling function
    job_fix_result = update_scheduler_job_function()
    logger.info(f"Job scheduling fix result: {'Success' if job_fix_result else 'Failed'}")
    
    # Step 3: Fix the notification check logic
    notification_fix_result = fix_daily_notification_check()
    logger.info(f"Notification check fix result: {'Success' if notification_fix_result else 'Failed'}")
    
    # Final status
    if job_fix_result or notification_fix_result:
        logger.info("Scheduler fix completed successfully. Please restart the scheduler.")
        return True
    else:
        logger.warning("No changes were made to the scheduler.")
        return False

if __name__ == "__main__":
    main()
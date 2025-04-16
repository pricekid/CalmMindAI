"""
Fix the scheduler timezone issue to ensure jobs run at the correct time.
This script will:
1. Stop the current scheduler
2. Update the scheduler.py file to use explicit UTC timezone
3. Restart the scheduler process with the correct configuration
"""
import os
import sys
import logging
import datetime
import time
import signal
import psutil
import subprocess
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def stop_scheduler():
    """Stop the running scheduler process."""
    try:
        # Read the scheduler PID
        with open('scheduler.pid', 'r') as f:
            pid = int(f.read().strip())
        
        logger.info(f"Stopping scheduler process with PID {pid}...")
        
        # Try to terminate gracefully
        try:
            os.kill(pid, signal.SIGTERM)
            
            # Wait for termination
            for i in range(5):
                time.sleep(1)
                try:
                    # Check if process still exists
                    process = psutil.Process(pid)
                    logger.info(f"Process {pid} still exists, waiting... ({i+1}/5)")
                except psutil.NoSuchProcess:
                    logger.info(f"Process {pid} has been terminated")
                    return True
            
            # If still running, force kill
            logger.warning(f"Process {pid} didn't terminate gracefully, using SIGKILL")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
            
            try:
                process = psutil.Process(pid)
                logger.error(f"Failed to kill process {pid}")
                return False
            except psutil.NoSuchProcess:
                logger.info(f"Process {pid} has been forcefully terminated")
                return True
        except ProcessLookupError:
            logger.info(f"Process {pid} does not exist, nothing to stop")
            return True
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        return False

def update_scheduler_file():
    """Update the scheduler.py file to use explicit UTC timezone."""
    try:
        # Read the current scheduler.py file
        with open('scheduler.py', 'r') as f:
            content = f.read()
        
        # Check if pytz is already imported
        if 'import pytz' not in content:
            # Add pytz import
            content = re.sub(
                r'import signal\n',
                'import signal\nimport pytz\n',
                content
            )
        
        # Check if scheduler already has timezone set
        if 'timezone=pytz.UTC' not in content:
            # Update the scheduler initialization with timezone
            content = re.sub(
                r'scheduler = BlockingScheduler\(\s*job_defaults=\{',
                'scheduler = BlockingScheduler(\n    timezone=pytz.UTC,  # Use UTC for consistent scheduling\n    job_defaults={',
                content
            )
        
        # Backup the original file
        backup_file = 'scheduler.py.bak'
        if not os.path.exists(backup_file):
            with open(backup_file, 'w') as f:
                f.write(content)
            logger.info(f"Created backup file: {backup_file}")
        
        # Write the updated content
        with open('scheduler.py', 'w') as f:
            f.write(content)
        
        logger.info("Updated scheduler.py with explicit UTC timezone")
        return True
    except Exception as e:
        logger.error(f"Error updating scheduler file: {str(e)}")
        return False

def ensure_pytz_installed():
    """Make sure pytz is installed."""
    try:
        import pytz
        logger.info("pytz is already installed")
        return True
    except ImportError:
        logger.info("Installing pytz...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytz"])
            logger.info("pytz has been installed")
            return True
        except Exception as e:
            logger.error(f"Error installing pytz: {str(e)}")
            return False

def restart_scheduler():
    """Start the scheduler process with the updated configuration."""
    try:
        logger.info("Starting scheduler process...")
        
        # Make sure environment variables are properly set
        if not os.environ.get('MAIL_SERVER'):
            os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
        
        if not os.environ.get('MAIL_PORT'):
            os.environ['MAIL_PORT'] = '587'
        
        # Start the scheduler as a background process
        process = subprocess.Popen(
            ["python3", "scheduler.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Detach the process
        )
        
        # Wait to make sure it starts
        time.sleep(2)
        
        if process.poll() is None:
            pid = process.pid
            logger.info(f"Scheduler started with PID {pid}")
            
            # Save the PID to file
            with open('scheduler.pid', 'w') as f:
                f.write(str(pid))
            
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Scheduler failed to start: {stderr.decode()}")
            return False
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        return False

def update_scheduler_job_time():
    """
    Update the scheduler job time to run soon for testing.
    This will modify the cron job to run in the next few minutes.
    """
    try:
        # Read the current scheduler.py file
        with open('scheduler.py', 'r') as f:
            content = f.read()
        
        # Get current time
        now = datetime.datetime.now()
        test_hour = (now.hour) % 24  # Use current hour for testing
        test_minute = (now.minute + 3) % 60  # 3 minutes from now
        
        logger.info(f"Setting test job to run at {test_hour:02d}:{test_minute:02d}")
        
        # Update the daily email reminder job
        content = re.sub(
            r"scheduler\.add_job\(\s*safe_send_daily_reminder,\s*'cron',\s*hour='(\d+)',\s*minute=(\d+),",
            f"scheduler.add_job(\n    safe_send_daily_reminder, \n    'cron', \n    hour='{test_hour}', \n    minute={test_minute},",
            content
        )
        
        # Update the daily SMS reminder job
        content = re.sub(
            r"scheduler\.add_job\(\s*safe_send_daily_sms_reminder,\s*'cron',\s*hour='(\d+)',\s*minute=(\d+),",
            f"scheduler.add_job(\n    safe_send_daily_sms_reminder, \n    'cron', \n    hour='{test_hour}', \n    minute={test_minute},",
            content
        )
        
        # Update the Twilio credentials job
        creds_minute = (test_minute - 1) % 60  # One minute before the reminder
        creds_hour = test_hour if creds_minute < test_minute else (test_hour - 1) % 24
        
        content = re.sub(
            r"scheduler\.add_job\(\s*load_twilio_credentials,\s*'cron',\s*hour='(\d+)',\s*minute=(\d+),",
            f"scheduler.add_job(\n    load_twilio_credentials, \n    'cron', \n    hour='{creds_hour}', \n    minute={creds_minute},",
            content
        )
        
        # Write the updated content
        with open('scheduler.py', 'w') as f:
            f.write(content)
        
        logger.info(f"Updated scheduler jobs to run at {test_hour:02d}:{test_minute:02d}")
        return True
    except Exception as e:
        logger.error(f"Error updating scheduler job time: {str(e)}")
        return False

def immediately_run_job():
    """Run the daily email reminder job manually."""
    try:
        logger.info("Running daily email reminder job manually...")
        
        # Import the function from scheduler
        from scheduler import safe_send_daily_reminder
        
        # Run the function
        result = safe_send_daily_reminder()
        
        logger.info(f"Job result: {result}")
        return True
    except Exception as e:
        logger.error(f"Error running job manually: {str(e)}")
        return False

def main():
    """Main function to fix the scheduler timezone issue."""
    logger.info("=" * 80)
    logger.info("SCHEDULER TIMEZONE FIX")
    logger.info("=" * 80)
    
    # Make sure pytz is installed
    logger.info("Ensuring pytz is installed...")
    if not ensure_pytz_installed():
        logger.error("Failed to install pytz, cannot proceed")
        return 1
    
    # Stop the running scheduler
    logger.info("Stopping current scheduler...")
    if not stop_scheduler():
        logger.error("Failed to stop scheduler")
        return 1
    
    # Update the scheduler file with timezone
    logger.info("Updating scheduler file...")
    if not update_scheduler_file():
        logger.error("Failed to update scheduler file")
        return 1
    
    # Update job time to run soon for testing
    logger.info("Updating job schedule for testing...")
    if not update_scheduler_job_time():
        logger.error("Failed to update job schedule")
        return 1
    
    # Restart the scheduler
    logger.info("Restarting scheduler...")
    if not restart_scheduler():
        logger.error("Failed to restart scheduler")
        return 1
    
    logger.info("Scheduler has been updated and restarted with proper timezone configuration")
    
    # Run the job immediately for testing
    logger.info("Running job immediately...")
    immediately_run_job()
    
    logger.info("=" * 80)
    logger.info("SCHEDULER TIMEZONE FIX COMPLETED")
    logger.info("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
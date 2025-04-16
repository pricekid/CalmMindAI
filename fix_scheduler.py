"""
Script to fix the scheduler so it properly sends daily email notifications.
"""
import os
import sys
import logging
import datetime
import time
import signal
import psutil
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists."""
    if not os.path.exists('data'):
        os.makedirs('data')
        logger.info("Created data directory")

def log_action(action_type, message, success=True):
    """Log an action to a file for tracking."""
    ensure_data_directory()
    
    log_file = "data/scheduler_fixes.json"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    entry = {
        "timestamp": timestamp,
        "type": action_type,
        "message": message,
        "success": success
    }
    
    try:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(entry)
        
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Error logging action: {str(e)}")
        return False

def check_scheduler_process():
    """Check if the scheduler process is running."""
    try:
        with open('scheduler.pid', 'r') as f:
            pid = int(f.read().strip())
        
        try:
            process = psutil.Process(pid)
            cmdline = process.cmdline()
            
            if 'scheduler.py' in ' '.join(cmdline):
                logger.info(f"Scheduler process {pid} is running: {cmdline}")
                return True, pid, process
            else:
                logger.warning(f"Process {pid} is running but is not the scheduler: {cmdline}")
                return False, pid, None
        except psutil.NoSuchProcess:
            logger.error(f"Scheduler process {pid} is not running!")
            return False, pid, None
    except Exception as e:
        logger.error(f"Error checking scheduler process: {str(e)}")
        return False, None, None

def stop_scheduler():
    """Stop the scheduler process."""
    is_running, pid, process = check_scheduler_process()
    
    if not is_running or not pid:
        logger.warning("Scheduler is not running, nothing to stop")
        return True
    
    try:
        logger.info(f"Attempting to stop scheduler (PID {pid})...")
        
        # Try SIGTERM first for a graceful shutdown
        os.kill(pid, signal.SIGTERM)
        
        # Give the process time to shut down
        for _ in range(5):
            time.sleep(1)
            try:
                # Check if process still exists
                process = psutil.Process(pid)
                logger.info(f"Process {pid} still exists, waiting...")
            except psutil.NoSuchProcess:
                logger.info(f"Process {pid} has terminated")
                log_action("scheduler_stop", f"Scheduler with PID {pid} stopped gracefully")
                return True
        
        # If still running, use SIGKILL
        logger.warning(f"Process {pid} didn't terminate with SIGTERM, using SIGKILL")
        os.kill(pid, signal.SIGKILL)
        time.sleep(1)
        
        try:
            process = psutil.Process(pid)
            logger.error(f"Failed to kill process {pid}")
            return False
        except psutil.NoSuchProcess:
            logger.info(f"Process {pid} has been forcefully terminated")
            log_action("scheduler_stop", f"Scheduler with PID {pid} forcefully terminated")
            return True
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        return False

def fix_scheduler_environment():
    """Fix scheduler environment by ensuring all required variables are set."""
    # First, check what variables are currently set
    mail_vars = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
        'MAIL_PORT': os.environ.get('MAIL_PORT'),
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER')
    }
    
    # Set default values for missing variables
    if not mail_vars['MAIL_SERVER']:
        os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
        logger.info("Set MAIL_SERVER to smtp.gmail.com")
    
    if not mail_vars['MAIL_PORT']:
        os.environ['MAIL_PORT'] = '587'
        logger.info("Set MAIL_PORT to 587")
    
    if not mail_vars['MAIL_USERNAME']:
        os.environ['MAIL_USERNAME'] = 'calmjourney7@gmail.com'
        logger.info("Set MAIL_USERNAME to calmjourney7@gmail.com")
    
    if not mail_vars['MAIL_DEFAULT_SENDER']:
        os.environ['MAIL_DEFAULT_SENDER'] = 'calmjourney7@gmail.com'
        logger.info("Set MAIL_DEFAULT_SENDER to calmjourney7@gmail.com")
    
    # Check if password is set, which is critical
    if not mail_vars['MAIL_PASSWORD']:
        logger.error("MAIL_PASSWORD is not set! Cannot send emails without it.")
        return False
    
    logger.info("Mail environment variables are now properly set")
    return True

def start_scheduler():
    """Start the scheduler process."""
    logger.info("Starting scheduler process...")
    
    # Make sure environment variables are set before starting
    fix_scheduler_environment()
    
    try:
        # Start scheduler as a background process
        import subprocess
        process = subprocess.Popen(
            ["python3", "scheduler.py"], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # This detaches the process
        )
        
        # Wait a moment to make sure it starts
        time.sleep(2)
        
        # Verify the process is running
        if process.poll() is None:
            pid = process.pid
            logger.info(f"Scheduler started with PID {pid}")
            
            # Save PID to file
            with open('scheduler.pid', 'w') as f:
                f.write(str(pid))
            
            log_action("scheduler_start", f"Started scheduler with PID {pid}")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Scheduler failed to start: {stderr.decode()}")
            log_action("scheduler_start_failed", f"Failed to start scheduler: {stderr.decode()}", success=False)
            return False
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        log_action("scheduler_start_failed", f"Error starting scheduler: {str(e)}", success=False)
        return False

def test_scheduler_job():
    """Test the scheduler job by running it directly."""
    logger.info("Testing scheduler job by running it directly...")
    
    try:
        from scheduler_service import send_daily_reminder_direct
        
        # Run the job directly to test it
        logger.info("Running send_daily_reminder_direct()...")
        result = send_daily_reminder_direct()
        
        logger.info(f"Job result: {result}")
        if result['sent_count'] > 0:
            logger.info(f"Successfully sent {result['sent_count']} emails!")
            log_action("job_test", f"Manually sent {result['sent_count']} emails", success=True)
            return True
        else:
            logger.warning(f"No emails were sent. Skipped {result['skipped_count']} users.")
            log_action("job_test", f"No emails sent. Skipped {result['skipped_count']} users", success=False)
            return False
    except Exception as e:
        logger.error(f"Error testing scheduler job: {str(e)}")
        log_action("job_test_failed", f"Error testing scheduler job: {str(e)}", success=False)
        return False

def fix_scheduler_configuration():
    """Check and fix the scheduler configuration."""
    logger.info("Fixing scheduler configuration...")
    
    # We need to restart the scheduler to ensure it picks up the environment variables
    stop_scheduler()
    
    # Fix environment variables
    fix_scheduler_environment()
    
    # Start the scheduler again
    start_scheduler()
    
    # Verify it's running
    is_running, pid, _ = check_scheduler_process()
    
    if is_running:
        logger.info(f"Scheduler is now running with PID {pid}")
        log_action("fix_complete", f"Scheduler fixed and running with PID {pid}")
        return True
    else:
        logger.error("Failed to fix scheduler")
        log_action("fix_failed", "Failed to fix scheduler", success=False)
        return False

def manually_run_job():
    """Manually run the email job to send out notifications now."""
    logger.info("Manually running email notification job...")
    
    # Run the job directly
    try:
        from scheduler import safe_send_daily_reminder
        
        # Make sure environment variables are set first
        fix_scheduler_environment()
        
        # Run the job
        logger.info("Running safe_send_daily_reminder()...")
        result = safe_send_daily_reminder()
        
        logger.info(f"Job result: {result}")
        log_action("manual_job", f"Manually ran email job: {result}", success=True)
        return True
    except Exception as e:
        logger.error(f"Error manually running job: {str(e)}")
        log_action("manual_job_failed", f"Error manually running job: {str(e)}", success=False)
        return False

def main():
    """Main function to fix the scheduler."""
    logger.info("=" * 80)
    logger.info("SCHEDULER FIX UTILITY")
    logger.info("=" * 80)
    
    # Check if scheduler is running
    is_running, pid, _ = check_scheduler_process()
    logger.info(f"Scheduler running: {is_running}" + (f" (PID: {pid})" if is_running else ""))
    
    # Check environment variables
    logger.info("\nChecking mail environment variables...")
    env_ok = fix_scheduler_environment()
    logger.info(f"Environment variables OK: {env_ok}")
    
    # Fix scheduler if needed
    if not is_running or not env_ok:
        logger.info("\nFixing scheduler configuration...")
        fix_scheduler_configuration()
    
    # Test by running the job directly
    logger.info("\nTesting email notification job...")
    job_ok = test_scheduler_job()
    logger.info(f"Email job test result: {job_ok}")
    
    # Manually run the job to send notifications now
    logger.info("\nManually running email notification job...")
    manual_run = manually_run_job()
    logger.info(f"Manual job run result: {manual_run}")
    
    logger.info("=" * 80)
    logger.info("SCHEDULER FIX COMPLETE")
    logger.info("=" * 80)
    
    if job_ok:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
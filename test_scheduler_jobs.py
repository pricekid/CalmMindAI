"""
Test script to check if the scheduler jobs are properly configured and running.
"""
import os
import sys
import logging
import datetime
import json
from apscheduler.schedulers.blocking import BlockingScheduler
import signal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inspect_scheduler_process():
    """Check if the scheduler process exists and get info about its jobs."""
    try:
        with open('scheduler.pid', 'r') as f:
            pid = int(f.read().strip())
            logger.info(f"Scheduler PID: {pid}")
        
        # Check if the process is running
        import psutil
        try:
            process = psutil.Process(pid)
            logger.info(f"Scheduler process exists: {process.cmdline()}")
            logger.info(f"Process created: {datetime.datetime.fromtimestamp(process.create_time())}")
            logger.info(f"Process status: {process.status()}")
            
            # Get process environment
            try:
                env = process.environ()
                logger.info("Process environment variables:")
                mail_vars = [var for var in env if var.startswith('MAIL_')]
                for var in mail_vars:
                    if var == 'MAIL_PASSWORD':
                        logger.info(f"  {var}: {'Set' if env.get(var) else 'Not set'}")
                    else:
                        logger.info(f"  {var}: {env.get(var)}")
            except psutil.AccessDenied:
                logger.warning("Could not access process environment (permission denied)")
            
            return True
        except psutil.NoSuchProcess:
            logger.error(f"Process with PID {pid} doesn't exist")
            return False
    except Exception as e:
        logger.error(f"Error inspecting scheduler process: {str(e)}")
        return False

def test_scheduler_jobs():
    """Test that the scheduler jobs are correctly configured."""
    logger.info("Testing scheduler jobs configuration...")
    
    try:
        # Import the scheduler module to check its configuration
        import scheduler
        
        # Check job definitions
        jobs = scheduler.scheduler.get_jobs()
        logger.info(f"Found {len(jobs)} scheduled jobs")
        
        for job in jobs:
            logger.info(f"Job ID: {job.id}")
            logger.info(f"Job Name: {job.name}")
            logger.info(f"Job Function: {job.func.__name__}")
            
            # Handle different job types correctly
            if hasattr(job.trigger, 'fields'):
                # For cron triggers
                fields = job.trigger.fields
                schedule = {}
                for field in fields:
                    if hasattr(field, 'name') and hasattr(field, 'expressions'):
                        expressions = [str(expr) for expr in field.expressions]
                        schedule[field.name] = ', '.join(expressions)
                
                logger.info(f"Job Schedule (cron): {schedule}")
                
                # Calculate next run time for cron jobs
                try:
                    import pytz
                    now = datetime.datetime.now(pytz.utc)
                    next_run = job.trigger.get_next_fire_time(None, now)
                    if next_run:
                        logger.info(f"Next run time: {next_run}")
                        time_until = next_run - now
                        logger.info(f"Time until next run: {time_until}")
                    else:
                        logger.warning("Could not determine next run time")
                except Exception as e:
                    logger.error(f"Error calculating next run time: {str(e)}")
            elif hasattr(job.trigger, 'interval'):
                # For interval triggers
                logger.info(f"Job Interval: {job.trigger.interval} seconds")
                if hasattr(job.trigger, 'start_date'):
                    logger.info(f"Job Start Date: {job.trigger.start_date}")
            else:
                logger.info(f"Job Trigger: {job.trigger}")
            
            logger.info("-" * 50)
        
        # Check event listeners
        logger.info("Checking scheduler event listeners...")
        if hasattr(scheduler, 'job_listener'):
            logger.info("Job execution listener is configured")
        else:
            logger.error("Job execution listener is not configured")
        
        return True
    except Exception as e:
        logger.error(f"Error testing scheduler jobs: {str(e)}")
        return False

def run_job_manually():
    """Run the email notification job manually."""
    logger.info("Running the daily email reminder job manually...")
    
    try:
        # Make sure environment variables are set
        if not os.environ.get('MAIL_SERVER'):
            os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
            logger.info("Set MAIL_SERVER environment variable to smtp.gmail.com")
        
        if not os.environ.get('MAIL_PORT'):
            os.environ['MAIL_PORT'] = '587'
            logger.info("Set MAIL_PORT environment variable to 587")
        
        # Import the job function from the scheduler
        from scheduler import safe_send_daily_reminder
        
        # Run the job function directly
        logger.info("Executing safe_send_daily_reminder()...")
        result = safe_send_daily_reminder()
        
        logger.info(f"Job result: {result}")
        
        return True
    except Exception as e:
        logger.error(f"Error running job manually: {str(e)}")
        return False

def test_fix_scheduler_timezone():
    """
    Test fixing the scheduler timezone issue, which may be 
    preventing jobs from running at the expected time.
    """
    logger.info("Testing timezone fix for scheduler...")
    
    # Check current timezone settings
    import time
    logger.info(f"System timezone: {time.tzname}")
    
    # Get current UTC time
    utc_now = datetime.datetime.utcnow()
    local_now = datetime.datetime.now()
    
    logger.info(f"UTC time: {utc_now}")
    logger.info(f"Local time: {local_now}")
    logger.info(f"Difference: {local_now - utc_now}")
    
    # Check if scheduler.py has timezone configuration
    with open('scheduler.py', 'r') as f:
        scheduler_code = f.read()
    
    if 'timezone' in scheduler_code:
        logger.info("Scheduler has timezone configuration")
    else:
        logger.warning("Scheduler does not have explicit timezone configuration")
        
        # Add timezone configuration to scheduler
        logger.info("Creating patch to fix scheduler timezone...")
        
        scheduler_patch = """import pytz

# Use UTC timezone for consistent scheduling across environments
scheduler = BlockingScheduler(
    job_defaults={
        'misfire_grace_time': 3600,  # 1 hour grace time for all jobs
        'coalesce': True,          # Combine multiple missed runs into one
        'max_instances': 1         # Prevent multiple instances of the same job
    },
    timezone=pytz.UTC  # Explicitly set timezone to UTC
)"""
        
        # We don't actually apply the patch here, just show it
        logger.info("Patch to apply:")
        logger.info(scheduler_patch)
    
    # Change the timezone and time on scheduler cron jobs to run soon
    logger.info("Would modify job schedules to run soon for testing if applied")
    
    return True

def main():
    """Main function to test scheduler jobs."""
    logger.info("=" * 80)
    logger.info("SCHEDULER JOBS TEST")
    logger.info("=" * 80)
    
    # Inspect the scheduler process
    logger.info("\nInspecting scheduler process...")
    process_ok = inspect_scheduler_process()
    
    # Test scheduler jobs configuration
    logger.info("\nTesting scheduler jobs configuration...")
    jobs_ok = test_scheduler_jobs()
    
    # Test timezone fix
    logger.info("\nTesting timezone configuration...")
    timezone_ok = test_fix_scheduler_timezone()
    
    # Run job manually if needed
    run_manually = input("\nDo you want to run the email job manually? (y/n): ")
    if run_manually.lower() == 'y':
        logger.info("\nRunning job manually...")
        manual_ok = run_job_manually()
        logger.info(f"Manual job run result: {manual_ok}")
    
    logger.info("\n" + "=" * 80)
    logger.info("SCHEDULER JOBS TEST COMPLETED")
    logger.info("=" * 80)
    
    if process_ok and jobs_ok:
        logger.info("Scheduler and jobs are configured correctly.")
        return 0
    else:
        logger.error("Scheduler or jobs are not configured correctly.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
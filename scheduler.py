
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_SCHEDULER_STARTED
# Use the decoupled scheduler service instead of importing models directly
from scheduler_service import send_daily_reminder_direct, send_daily_sms_reminder_direct
import logging
import os
import sys
import traceback
import datetime
import signal
import time
import flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from scheduler_logs import log_scheduler_activity, ensure_data_directory

# Configure detailed logging with timestamp, process ID, and thread info
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PID:%(process)d] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set a higher log level just for this module
logger.setLevel(logging.DEBUG)

# Also log to a file for easier debugging
try:
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
except Exception as e:
    logger.error(f"Error scheduling daily email job: {str(e)}")
    log_scheduler_activity("job_schedule_error", f"Error scheduling daily email job: {str(e)}", success=False)

# SMS notifications at 6:00 AM
scheduler.add_job(
    safe_send_daily_sms_reminder, 
    'cron', 
    hour='6', 
    minute=0,
    id='daily_sms_reminder',
    replace_existing=True,
    name='Daily SMS Reminder'
)

# Load Twilio credentials 1 minute before SMS job
scheduler.add_job(
    load_twilio_credentials, 
    'cron', 
    hour='5', 
    minute=59,
    id='load_twilio_credentials',
    replace_existing=True,
    name='Load Twilio Credentials'
)

# Add backup email job at 6:10 AM in case the 6:00 AM job fails
try:
    scheduler.add_job(
        safe_send_daily_reminder,
        'cron', 
        hour='6', 
        minute=10,
        id='backup_email_reminder',
        replace_existing=True,
        name='Backup Email Reminder'
    )
    logger.info("Backup email job scheduled for 6:10 AM UTC")
    log_scheduler_activity("job_scheduled", "Backup email job scheduled for 6:10 AM UTC", success=True)
except Exception as e:
    logger.error(f"Error scheduling backup email job: {str(e)}")
    log_scheduler_activity("job_schedule_error", f"Error scheduling backup email job: {str(e)}", success=False)

# Health check every 30 minutes
scheduler.add_job(
    scheduler_health_check,
    'interval',
    minutes=30,
    id='scheduler_health_check',
    replace_existing=True,
    name='Scheduler Health Check'
)

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle termination signals to shut down gracefully"""
    signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
    logger.info(f"Received signal {signal_name}. Shutting down scheduler gracefully...")
    log_scheduler_activity("scheduler_shutdown", f"Shutting down scheduler due to signal {signal_name}")
    scheduler.shutdown()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    # Ensure data directory exists
    ensure_data_directory()
    
    # Log startup
    startup_time = datetime.datetime.now()
    logger.info(f"Starting notification scheduler at {startup_time}...")
    log_scheduler_activity("scheduler_startup", f"Starting notification scheduler at {startup_time}")
    
    try:
        # Load Twilio credentials at startup
        load_twilio_credentials()
        
        # Run a health check immediately
        scheduler_health_check()
        
        # Check if we missed today's notification (if it's after 6 AM but before 11 PM)
        current_hour = datetime.datetime.now(pytz.UTC).hour
        if 6 <= current_hour < 23:
            from notification_tracking import get_notification_stats
            today = datetime.datetime.now(pytz.UTC).strftime("%Y-%m-%d")
            
            # Get today's notification stats
            try:
                stats = get_notification_stats()
                today_stats = stats.get("email", {}).get(today, [])
                
                if not today_stats:
                    logger.warning(f"No email notifications sent today ({today}) and it's after 6 AM UTC. Running immediate notification job...")
                    log_scheduler_activity("missed_notification", f"No notifications sent today ({today}). Running immediate job.", success=True)
                    
                    try:
                        # Run the notification job immediately
                        safe_send_daily_reminder()
                    except Exception as e:
                        logger.error(f"Error running immediate notification job: {str(e)}")
                else:
                    logger.info(f"Today's notifications have already been sent to {len(today_stats)} users.")
            except Exception as e:
                logger.error(f"Error checking notification stats: {str(e)}")
        
        # Start the scheduler
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler shutting down due to keyboard interrupt")
        log_scheduler_activity("scheduler_shutdown", "Scheduler shutting down due to keyboard interrupt")
    except Exception as e:
        error_details = traceback.format_exc()
        logger.critical(f"Fatal error in scheduler: {str(e)}\n{error_details}")
        log_scheduler_activity("scheduler_fatal_error", f"Fatal error in scheduler: {str(e)}", success=False)
        sys.exit(1)

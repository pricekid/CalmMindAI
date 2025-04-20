
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
    file_handler = logging.FileHandler('data/scheduler_debug.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - [PID:%(process)d] - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    logger.debug("Added file handler for more detailed logging")
except Exception as e:
    print(f"Warning: Could not set up file logging: {e}")

# Create a Flask app context for database access
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {"connect_timeout": 30}  # Increase connection timeout
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import pytz for timezone support
import pytz

# Create BlockingScheduler with increased job defaults and timezone set to UTC
scheduler = BlockingScheduler(
    timezone=pytz.UTC,  # Explicitly use UTC timezone for consistent scheduling
    job_defaults={
        'misfire_grace_time': 3600,  # 1 hour grace time for all jobs
        'coalesce': True,          # Combine multiple missed runs into one
        'max_instances': 1         # Prevent multiple instances of the same job
    }
)

# Wrapper functions to add better error handling and logging with retries
def safe_send_daily_reminder(max_retries=3, retry_delay=300):
    """
    Wrapper around send_daily_reminder_direct with error handling, logging, and retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts (default 3)
        retry_delay: Delay between retries in seconds (default 300 = 5 minutes)
    """
    attempt = 1
    last_error = None
    
    while attempt <= max_retries:
        try:
            logger.info(f"[{datetime.datetime.now()}] Starting daily email reminder job (attempt {attempt}/{max_retries})")
            log_scheduler_activity("email_notification_start", f"Starting daily email notifications (attempt {attempt}/{max_retries})")
            
            # Use the direct service function that doesn't depend on models
            result = send_daily_reminder_direct()
            
            # Check if any emails were sent successfully
            if isinstance(result, dict) and result.get("sent_count", 0) > 0:
                logger.info(f"[{datetime.datetime.now()}] Completed daily email reminder job. Result: {result}")
                log_scheduler_activity("email_notification_complete", f"Completed daily email notifications: {result}")
                return result
            else:
                logger.warning(f"[{datetime.datetime.now()}] Daily email job completed but no emails were sent. Result: {result}")
                last_error = f"No emails sent: {result}"
                
                # If this is the last attempt, return the result anyway
                if attempt >= max_retries:
                    log_scheduler_activity("email_notification_warning", f"No emails sent after {max_retries} attempts: {result}")
                    return result
        except Exception as e:
            error_details = traceback.format_exc()
            last_error = str(e)
            logger.error(f"[{datetime.datetime.now()}] Error in daily email reminder (attempt {attempt}/{max_retries}): {str(e)}\n{error_details}")
            log_scheduler_activity("email_notification_error", f"Error in attempt {attempt}/{max_retries}: {str(e)}", success=False)
            
            # If this is the last attempt, raise the error
            if attempt >= max_retries:
                logger.error(f"[{datetime.datetime.now()}] All {max_retries} attempts failed for daily email reminder.")
                log_scheduler_activity("email_notification_failure", f"All {max_retries} attempts failed: {str(e)}", success=False)
                return False
        
        # Increment attempt counter and wait before retry
        attempt += 1
        
        if attempt <= max_retries:
            logger.info(f"[{datetime.datetime.now()}] Retrying daily email reminder in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    # Should not reach here, but just in case
    logger.error(f"[{datetime.datetime.now()}] Failed to send daily email reminders after {max_retries} attempts. Last error: {last_error}")
    log_scheduler_activity("email_notification_failure", f"Failed after {max_retries} attempts: {last_error}", success=False)
    return False

def safe_send_daily_sms_reminder(max_retries=3, retry_delay=300):
    """
    Wrapper around send_daily_sms_reminder_direct with error handling, logging, and retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts (default 3)
        retry_delay: Delay between retries in seconds (default 300 = 5 minutes)
    """
    attempt = 1
    last_error = None
    
    while attempt <= max_retries:
        try:
            logger.info(f"[{datetime.datetime.now()}] Starting daily SMS reminder job (attempt {attempt}/{max_retries})")
            log_scheduler_activity("sms_notification_start", f"Starting daily SMS notifications (attempt {attempt}/{max_retries})")
            
            # First ensure Twilio credentials are loaded
            credentials_loaded = load_twilio_credentials()
            if not credentials_loaded:
                logger.error(f"[{datetime.datetime.now()}] Failed to load Twilio credentials on attempt {attempt}/{max_retries}")
                last_error = "Failed to load Twilio credentials"
                
                # If this is the last attempt, return failure
                if attempt >= max_retries:
                    log_scheduler_activity("sms_notification_error", "Failed to load Twilio credentials after multiple attempts", success=False)
                    return {"error": "Failed to load Twilio credentials", "sent_count": 0, "total_users": 0}
            else:
                # Use the direct service function that doesn't depend on models
                result = send_daily_sms_reminder_direct()
                
                # Check if any SMS were sent successfully
                if isinstance(result, dict) and result.get("sent_count", 0) > 0:
                    logger.info(f"[{datetime.datetime.now()}] Completed daily SMS reminder job. Result: {result}")
                    log_scheduler_activity("sms_notification_complete", f"Completed daily SMS notifications: {result}")
                    return result
                else:
                    logger.warning(f"[{datetime.datetime.now()}] Daily SMS job completed but no messages were sent. Result: {result}")
                    last_error = f"No SMS sent: {result}"
                    
                    # If this is the last attempt, return the result anyway
                    if attempt >= max_retries:
                        log_scheduler_activity("sms_notification_warning", f"No SMS sent after {max_retries} attempts: {result}")
                        return result
        except Exception as e:
            error_details = traceback.format_exc()
            last_error = str(e)
            logger.error(f"[{datetime.datetime.now()}] Error in daily SMS reminder (attempt {attempt}/{max_retries}): {str(e)}\n{error_details}")
            log_scheduler_activity("sms_notification_error", f"Error in attempt {attempt}/{max_retries}: {str(e)}", success=False)
            
            # If this is the last attempt, raise the error
            if attempt >= max_retries:
                logger.error(f"[{datetime.datetime.now()}] All {max_retries} attempts failed for daily SMS reminder.")
                log_scheduler_activity("sms_notification_failure", f"All {max_retries} attempts failed: {str(e)}", success=False)
                return False
        
        # Increment attempt counter and wait before retry
        attempt += 1
        
        if attempt <= max_retries:
            logger.info(f"[{datetime.datetime.now()}] Retrying daily SMS reminder in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    # Should not reach here, but just in case
    logger.error(f"[{datetime.datetime.now()}] Failed to send daily SMS reminders after {max_retries} attempts. Last error: {last_error}")
    log_scheduler_activity("sms_notification_failure", f"Failed after {max_retries} attempts: {last_error}", success=False)
    return False

# Function to load Twilio credentials before SMS job runs
def load_twilio_credentials():
    """Load Twilio credentials from saved configuration file before sending SMS notifications"""
    try:
        logger.info("Loading Twilio credentials")
        
        # First check environment variables
        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
        
        # If not set, try to load from configuration
        if not all([twilio_sid, twilio_token, twilio_phone]):
            try:
                # Import here to avoid circular imports
                from admin_utils import load_twilio_config
                
                with app.app_context():
                    twilio_config = load_twilio_config()
                    
                    if twilio_config:
                        # Set environment variables if values found in config
                        if not twilio_sid and twilio_config.get("account_sid"):
                            os.environ["TWILIO_ACCOUNT_SID"] = twilio_config["account_sid"]
                            twilio_sid = twilio_config["account_sid"]
                        
                        if not twilio_token and twilio_config.get("auth_token"):
                            os.environ["TWILIO_AUTH_TOKEN"] = twilio_config["auth_token"]
                            twilio_token = twilio_config["auth_token"]
                        
                        if not twilio_phone and twilio_config.get("phone_number"):
                            os.environ["TWILIO_PHONE_NUMBER"] = twilio_config["phone_number"]
                            twilio_phone = twilio_config["phone_number"]
                        
                        logger.info("Successfully loaded Twilio credentials from configuration")
                        log_scheduler_activity("twilio_credentials", "Loaded Twilio credentials from configuration")
            except Exception as e:
                logger.error(f"Error loading Twilio configuration: {str(e)}")
                log_scheduler_activity("twilio_credentials_error", f"Error loading Twilio config: {str(e)}", success=False)
        
        # Verify credentials were loaded
        if all([twilio_sid, twilio_token, twilio_phone]):
            logger.info("Twilio credentials are available")
            return True
        else:
            missing = []
            if not twilio_sid: missing.append("TWILIO_ACCOUNT_SID")
            if not twilio_token: missing.append("TWILIO_AUTH_TOKEN")
            if not twilio_phone: missing.append("TWILIO_PHONE_NUMBER")
            
            logger.warning(f"Some Twilio credentials are missing: {', '.join(missing)}")
            log_scheduler_activity("twilio_credentials_incomplete", f"Missing Twilio credentials: {', '.join(missing)}", success=False)
            return False
    except Exception as e:
        logger.error(f"Error in load_twilio_credentials: {str(e)}")
        log_scheduler_activity("twilio_credentials_error", f"Error in load_twilio_credentials: {str(e)}", success=False)
        return False

# Health check job to run every 30 minutes
def scheduler_health_check():
    """Perform a health check and log it"""
    try:
        current_time = datetime.datetime.now()
        logger.info(f"Scheduler health check at {current_time}")
        log_scheduler_activity("scheduler_health", f"Scheduler health check at {current_time}")
        
        # Log upcoming jobs
        upcoming_jobs = scheduler.get_jobs()
        job_details = []
        for job in upcoming_jobs:
            try:
                next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(job, 'next_run_time') and job.next_run_time else "None"
                job_details.append(f"{job.name}: Next run at {next_run}")
            except Exception as job_error:
                logger.warning(f"Could not get next run time for job {job.name}: {str(job_error)}")
                job_details.append(f"{job.name}: Next run time unknown")
        
        if job_details:
            logger.info(f"Upcoming scheduled jobs: {', '.join(job_details)}")
        else:
            logger.info("No upcoming scheduled jobs found")
        
        return True
    except Exception as e:
        logger.error(f"Error in scheduler health check: {str(e)}")
        log_scheduler_activity("scheduler_health_error", f"Error in scheduler health check: {str(e)}", success=False)
        return False

# Event listeners for job execution
def job_listener(event):
    """Log when jobs are executed or fail"""
    if event.exception:
        logger.error(f"Job {event.job_id} failed: {event.exception}")
        log_scheduler_activity("job_error", f"Job {event.job_id} failed: {event.exception}", success=False)
    else:
        logger.info(f"Job {event.job_id} executed successfully")
        log_scheduler_activity("job_success", f"Job {event.job_id} executed successfully")

def scheduler_started_listener(event):
    """Log when the scheduler starts"""
    logger.info("Scheduler started successfully")
    log_scheduler_activity("scheduler_start", "Scheduler started successfully")

# Register event listeners
scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.add_listener(scheduler_started_listener, EVENT_SCHEDULER_STARTED)

# Schedule jobs with detailed logging
logger.info("Setting up daily email reminder job for 6:00 AM UTC...")
log_scheduler_activity("job_setup", "Setting up daily email reminder job for 6:00 AM UTC")

try:
    # Email notifications at 6:00 AM
    email_job = scheduler.add_job(
        safe_send_daily_reminder, 
        'cron', 
        hour='6', 
        minute=0,
        id='daily_email_reminder',
        replace_existing=True,
        name='Daily Email Reminder'
    )
    
    if email_job and hasattr(email_job, 'next_run_time'):
        next_run = email_job.next_run_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(f"Daily email job scheduled successfully. Next run: {next_run}")
        log_scheduler_activity("job_scheduled", f"Daily email job scheduled successfully. Next run: {next_run}", success=True)
    else:
        logger.error("Failed to properly schedule daily email job. Job object is incomplete.")
        log_scheduler_activity("job_schedule_error", "Failed to properly schedule daily email job", success=False)
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

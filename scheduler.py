
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_SCHEDULER_STARTED
from notification_service import send_daily_reminder
from sms_notification_service import send_daily_sms_reminder
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
import models
from scheduler_logs import log_scheduler_activity, ensure_data_directory

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Create BlockingScheduler with increased job defaults
scheduler = BlockingScheduler(
    job_defaults={
        'misfire_grace_time': 3600,  # 1 hour grace time for all jobs
        'coalesce': True,          # Combine multiple missed runs into one
        'max_instances': 1         # Prevent multiple instances of the same job
    }
)

# Wrapper functions to add better error handling and logging
def safe_send_daily_reminder():
    """Wrapper around send_daily_reminder with error handling and logging"""
    try:
        logger.info(f"[{datetime.datetime.now()}] Starting daily email reminder job")
        log_scheduler_activity("email_notification_start", "Starting daily email notifications")
        
        with app.app_context():
            result = send_daily_reminder()
        
        logger.info(f"[{datetime.datetime.now()}] Completed daily email reminder job. Result: {result}")
        log_scheduler_activity("email_notification_complete", f"Completed daily email notifications: {result}")
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"[{datetime.datetime.now()}] Error in daily email reminder: {str(e)}\n{error_details}")
        log_scheduler_activity("email_notification_error", f"Error in daily email reminder: {str(e)}", success=False)
        return False

def safe_send_daily_sms_reminder():
    """Wrapper around send_daily_sms_reminder with error handling and logging"""
    try:
        logger.info(f"[{datetime.datetime.now()}] Starting daily SMS reminder job")
        log_scheduler_activity("sms_notification_start", "Starting daily SMS notifications")
        
        # First ensure Twilio credentials are loaded
        load_twilio_credentials()
        
        with app.app_context():
            result = send_daily_sms_reminder()
        
        logger.info(f"[{datetime.datetime.now()}] Completed daily SMS reminder job. Result: {result}")
        log_scheduler_activity("sms_notification_complete", f"Completed daily SMS notifications: {result}")
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"[{datetime.datetime.now()}] Error in daily SMS reminder: {str(e)}\n{error_details}")
        log_scheduler_activity("sms_notification_error", f"Error in daily SMS reminder: {str(e)}", success=False)
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
            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "None"
            job_details.append(f"{job.name}: Next run at {next_run}")
        
        logger.info(f"Upcoming scheduled jobs: {', '.join(job_details)}")
        
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

# Schedule jobs
# Email notifications at 6:00 AM
scheduler.add_job(
    safe_send_daily_reminder, 
    'cron', 
    hour='6', 
    minute=0,
    id='daily_email_reminder',
    replace_existing=True,
    name='Daily Email Reminder'
)

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

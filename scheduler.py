#!/usr/bin/env python3
"""
Scheduler module (API keys removed)

The scheduler functionality is preserved but notification API keys have been removed.
To enable notifications again, add valid API keys to the environment.
"""

import os
import logging
import atexit
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Log notification status
if not os.environ.get("SENDGRID_API_KEY"):
    logger.warning("SENDGRID_API_KEY not found in environment - email notifications disabled")
    print("Email notifications disabled - no API key")

if not os.environ.get("TWILIO_ACCOUNT_SID") or not os.environ.get("TWILIO_AUTH_TOKEN"):
    logger.warning("Twilio credentials not found in environment - SMS notifications disabled")
    print("SMS notifications disabled - no API keys")

# Create the scheduler with Caribbean timezone (UTC-4) and prevent duplicate jobs
scheduler = BackgroundScheduler(timezone=pytz.timezone('America/Port_of_Spain'))
scheduler.add_jobstore('memory', coalesce=True, max_instances=1)

# Create lock file to prevent duplicate runs
def create_notification_lock():
    """Create a lock file to block notifications"""
    try:
        lock_file = "data/notifications_blocked"
        with open(lock_file, "w") as f:
            f.write(str(datetime.now(pytz.UTC)))
        logger.info("Created notification block file")
        return True
    except Exception as e:
        logger.error(f"Error creating notification block: {e}")
        return False

def remove_notification_lock():
    try:
        os.remove("data/notifications_blocked")
    except:
        pass

# Set up job logging
def job_listener(event):
    """Log information about job execution/errors"""
    if event.code == EVENT_JOB_EXECUTED:
        logger.info(f"Job executed successfully: {event.job_id}")
    elif event.code == EVENT_JOB_ERROR:
        logger.error(f"Job error: {event.job_id}, {event.exception}")

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Clean shutdown
def shutdown_scheduler():
    """Properly shut down the scheduler when the app exits"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down")

atexit.register(shutdown_scheduler)

# Store the PID for external management
def save_pid():
    """Save the current process ID to a file for external management"""
    with open("scheduler.pid", "w") as f:
        f.write(str(os.getpid()))
    logger.info(f"Saved scheduler PID: {os.getpid()}")

# Export the scheduler
__all__ = ['scheduler']
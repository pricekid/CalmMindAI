"""
Journal reminder scheduler module.
This module sets up the APScheduler to periodically check for and send journal reminders.
"""
import logging
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from journal_reminder_service import send_journal_reminder_notifications

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create scheduler
scheduler = BackgroundScheduler()

def start_journal_reminder_scheduler():
    """
    Start the scheduler for journal reminders.
    This will check for users who should receive reminders every 5 minutes.
    """
    try:
        if not scheduler.running:
            # Add job to check for and send journal reminders every 5 minutes
            scheduler.add_job(
                send_journal_reminder_notifications,
                IntervalTrigger(minutes=5),
                id='journal_reminder_job',
                replace_existing=True
            )
            
            # Start the scheduler
            scheduler.start()
            logger.info("Journal reminder scheduler started successfully")
        else:
            logger.info("Journal reminder scheduler is already running")
            
    except Exception as e:
        logger.error(f"Error starting journal reminder scheduler: {e}")

def stop_journal_reminder_scheduler():
    """Stop the journal reminder scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Journal reminder scheduler stopped")
    else:
        logger.info("Journal reminder scheduler is not running")
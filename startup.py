import logging
import os
import datetime
import socket
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for notification API keys
if not os.environ.get("SENDGRID_API_KEY"):
    logger.info("SENDGRID_API_KEY not found - email notifications disabled")
    print("Email notifications disabled - no API key")

if not os.environ.get("TWILIO_ACCOUNT_SID") or not os.environ.get("TWILIO_AUTH_TOKEN"):
    logger.info("Twilio credentials incomplete - SMS notifications disabled")
    print("SMS notifications disabled - missing API keys")

def log_scheduler_activity(activity_type, message, success=True):
    """Log scheduler activity"""
    logger.info(f"Scheduler activity: {activity_type} - {message}")

# Ensure data directory exists
Path("data").mkdir(exist_ok=True)

# Clean up any stale PID files
if os.path.exists("scheduler.pid"):
    try:
        os.remove("scheduler.pid")
        logger.info("Removed stale scheduler PID file")
    except Exception as e:
        logger.error(f"Error removing scheduler PID file: {str(e)}")

# Log notifications status
hostname = socket.gethostname()
logger.info(f"Server startup on host {hostname} at {datetime.datetime.now()}")
logger.info("Email and SMS notifications require valid API keys to function")
logger.info("To enable notifications, please add the appropriate API keys")
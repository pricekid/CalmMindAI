"""
SMS Notification service - DISABLED.
All SMS functions will simply log and return success=False.
"""
import logging
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_sms_notification(to_number, message, user_id=None):
    """

    # SMS NOTIFICATIONS DISABLED
    logger.info(f"SMS notification blocked: {send_sms_notification}")
    return {"success": False, "error": "SMS notifications are permanently disabled"}
    SMS DISABLED - This function will not send any SMS messages.
    """
    logger.info(f"SMS sending BLOCKED to {to_number}")
    return {"success": False, "error": "SMS notifications are permanently disabled"}

def check_notifications_blocked():
    """Check if notifications are blocked by a block file"""
    return True  # Always return True to block all notifications

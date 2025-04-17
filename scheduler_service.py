"""
Simplified service functions for the scheduler that don't create circular imports.
This module contains lightweight wrappers around notification functions.
"""
import os
import logging
import json
import datetime
import time
from notification_service import ensure_data_directory
from notification_tracking import user_received_notification, record_notification_sent, get_notification_statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_users():
    """Load users from the data/users.json file without requiring the User model"""
    ensure_data_directory()
    if not os.path.exists('data/users.json'):
        logger.error("data/users.json not found")
        return []
    
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Error decoding users.json file")
        return []
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def send_daily_sms_reminder_direct():
    """
    Send daily SMS reminders to users without direct User model dependency.
    This function works directly with the users.json data file.
    """
    from sms_notification_service import send_sms_notification  # Import here to avoid circular import
    
    # Stats tracking
    total_users = 0
    sent_count = 0
    skipped_count = 0
    
    # Load all users
    users = load_users()
    total_users = len(users)
    
    # Get current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # We're now using the notification_tracking module to handle tracking
    # No need to manually manage tracking files anymore
    
    # Send SMS to each eligible user
    for user in users:
        # Skip users who have disabled SMS notifications
        if not user.get('sms_notifications_enabled', False):
            logger.info(f"Skipping user {user.get('id')}: SMS notifications disabled")
            skipped_count += 1
            continue
        
        # Skip users without phone numbers
        phone_number = user.get('phone_number')
        if not phone_number:
            logger.info(f"Skipping user {user.get('id')}: No phone number")
            skipped_count += 1
            continue
        
        # Skip users who have already received an SMS today
        user_id = user.get('id')
        if user_received_notification(user_id, 'sms'):
            logger.info(f"Skipping user {user_id}: Already received SMS today")
            skipped_count += 1
            continue
        
        # Get username for personalization
        username = user.get('username', 'there')
        
        # Send a simple daily journaling reminder
        try:
            message = f"Hi {username}! 📔 This is your daily reminder to journal in Calm Journey. A few minutes of reflection can make a big difference in your day."
            result = send_sms_notification(phone_number, message)
            
            if result.get('success'):
                # Track successful notification using the new tracking system
                record_notification_sent(user_id, 'sms', phone_number)
                sent_count += 1
                logger.info(f"SMS sent to user {user_id} at {phone_number}")
            else:
                logger.error(f"Failed to send SMS to user {user_id}: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error sending SMS to user {user_id}: {str(e)}")
        
        # Brief pause to avoid rate limiting
        time.sleep(1)
    
    # No need to manually save tracking data anymore
    # The notification_tracking module handles this automatically
    
    # Return stats
    return {
        "total_users": total_users,
        "sent_count": sent_count,
        "skipped_count": skipped_count,
        "timestamp": datetime.datetime.now().isoformat()
    }

def send_daily_reminder_direct():
    """
    Send daily email reminders to users without direct User model dependency.
    This function works directly with the users.json data file.
    """
    from notification_service import send_daily_reminder  # Import here to avoid circular import
    
    # Stats tracking
    total_users = 0
    sent_count = 0
    skipped_count = 0
    
    # Load all users
    users = load_users()
    total_users = len(users)
    
    # Get current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # We're now using the notification_tracking module to handle tracking
    # No need to manually manage tracking files anymore
    
    # Send email to each eligible user
    for user in users:
        # Skip users who have disabled email notifications
        if not user.get('notifications_enabled', False):
            logger.info(f"Skipping user {user.get('id')}: Email notifications disabled")
            skipped_count += 1
            continue
        
        # Skip users without email addresses
        email = user.get('email')
        if not email:
            logger.info(f"Skipping user {user.get('id')}: No email address")
            skipped_count += 1
            continue
        
        # Skip users who have already received an email today
        user_id = user.get('id')
        if user_received_notification(user_id, 'email'):
            logger.info(f"Skipping user {user_id}: Already received email today")
            skipped_count += 1
            continue
        
        # Get username for personalization
        username = user.get('username', 'there')
        
        # Send a simple daily journaling reminder
        try:
            # Use the enhanced daily reminder function
            result = send_daily_reminder(user)
            
            # The result can be True, False, or a dict with 'success' key
            if (isinstance(result, bool) and result) or (isinstance(result, dict) and result.get('success')):
                # Track successful notification using the new tracking system
                record_notification_sent(user_id, 'email', email)
                sent_count += 1
                logger.info(f"Email sent to user {user_id} at {email}")
            else:
                error_msg = result.get('error') if isinstance(result, dict) else str(result)
                logger.error(f"Failed to send email to user {user_id}: {error_msg}")
        except Exception as e:
            logger.error(f"Error sending email to user {user_id}: {str(e)}")
        
        # Brief pause to avoid rate limiting
        time.sleep(1)
    
    # No need to manually save tracking data anymore
    # The notification_tracking module handles this automatically
    
    # Return stats
    return {
        "total_users": total_users,
        "sent_count": sent_count,
        "skipped_count": skipped_count,
        "timestamp": datetime.datetime.now().isoformat()
    }
"""
Enhanced notification tracking system.
This module provides functions for tracking which notifications have been sent
and when, with detailed logging and reporting.
"""
import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directories exist"""
    Path("data").mkdir(exist_ok=True)
    Path("data/notifications").mkdir(exist_ok=True)
    Path("data/logs").mkdir(exist_ok=True)
    Path("data/logs/notifications").mkdir(exist_ok=True)

def get_notification_tracking_file(notification_type: str, date: Optional[str] = None) -> str:
    """
    Get the path to the notification tracking file for a specific type and date.
    
    Args:
        notification_type: Type of notification (email, sms, weekly_summary)
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        Path to the tracking file
    """
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
    return f"data/notifications/{notification_type}_{date}.json"

def load_notification_tracking(notification_type: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Load notification tracking data for a specific type and date.
    
    Args:
        notification_type: Type of notification (email, sms, weekly_summary)
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        Dictionary mapping user IDs to notification data
    """
    ensure_data_directory()
    tracking_file = get_notification_tracking_file(notification_type, date)
    
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in tracking file {tracking_file}")
            return {}
        except Exception as e:
            logger.error(f"Error loading notification tracking from {tracking_file}: {str(e)}")
            return {}
    else:
        return {}

def save_notification_tracking(
    notification_type: str, 
    tracking_data: Dict[str, Any], 
    date: Optional[str] = None
) -> bool:
    """
    Save notification tracking data for a specific type and date.
    
    Args:
        notification_type: Type of notification (email, sms, weekly_summary)
        tracking_data: Dictionary mapping user IDs to notification data
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        True if successful, False otherwise
    """
    ensure_data_directory()
    tracking_file = get_notification_tracking_file(notification_type, date)
    
    try:
        with open(tracking_file, "w") as f:
            json.dump(tracking_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving notification tracking to {tracking_file}: {str(e)}")
        return False

def record_notification_sent(
    user_id: Union[str, int], 
    notification_type: str, 
    recipient: str, 
    success: bool = True, 
    details: Optional[Dict[str, Any]] = None,
    date: Optional[str] = None
) -> bool:
    """
    Record that a notification was sent to a user.
    
    Args:
        user_id: User ID
        notification_type: Type of notification (email, sms, weekly_summary)
        recipient: Recipient address (email or phone)
        success: Whether the notification was successfully sent
        details: Additional details about the notification
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        True if successful, False otherwise
    """
    # Convert user_id to string for consistency
    user_id = str(user_id)
    
    # Set default date to today
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Load existing tracking data
    tracking_data = load_notification_tracking(notification_type, date)
    
    # Create entry for this notification
    timestamp = datetime.datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "recipient": recipient,
        "success": success
    }
    
    # Add additional details if provided
    if details:
        entry.update(details)
    
    # Add to tracking data
    tracking_data[user_id] = entry
    
    # Save updated tracking data
    if save_notification_tracking(notification_type, tracking_data, date):
        # Also log this notification in the detailed log
        log_notification_activity(user_id, notification_type, recipient, success, details)
        return True
    else:
        return False

def user_received_notification(
    user_id: Union[str, int], 
    notification_type: str, 
    date: Optional[str] = None
) -> bool:
    """
    Check if a user has received a notification of a specific type on a specific date.
    
    Args:
        user_id: User ID
        notification_type: Type of notification (email, sms, weekly_summary)
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        True if the user received the notification, False otherwise
    """
    # Convert user_id to string for consistency
    user_id = str(user_id)
    
    # Load tracking data
    tracking_data = load_notification_tracking(notification_type, date)
    
    # Check if user is in tracking data and notification was successful
    if user_id in tracking_data and tracking_data[user_id].get("success", False):
        return True
    else:
        return False

def get_notification_status(
    user_id: Union[str, int], 
    notification_type: str, 
    date: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the status of a notification for a specific user.
    
    Args:
        user_id: User ID
        notification_type: Type of notification (email, sms, weekly_summary)
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        Notification status dictionary or None if not found
    """
    # Convert user_id to string for consistency
    user_id = str(user_id)
    
    # Load tracking data
    tracking_data = load_notification_tracking(notification_type, date)
    
    # Return user's status if found
    if user_id in tracking_data:
        return tracking_data[user_id]
    else:
        return None

def count_notifications_sent(notification_type: str, date: Optional[str] = None) -> int:
    """
    Count how many notifications of a specific type were successfully sent on a specific date.
    
    Args:
        notification_type: Type of notification (email, sms, weekly_summary)
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        Count of successful notifications
    """
    # Load tracking data
    tracking_data = load_notification_tracking(notification_type, date)
    
    # Count successful notifications
    return sum(1 for entry in tracking_data.values() if entry.get("success", False))

def log_notification_activity(
    user_id: Union[str, int], 
    notification_type: str, 
    recipient: str, 
    success: bool, 
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Log notification activity to a detailed log file.
    
    Args:
        user_id: User ID
        notification_type: Type of notification (email, sms, weekly_summary)
        recipient: Recipient address (email or phone)
        success: Whether the notification was successfully sent
        details: Additional details about the notification
        
    Returns:
        True if successful, False otherwise
    """
    ensure_data_directory()
    
    # Generate log file name with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = f"data/logs/notifications/activity_{timestamp}.json"
    
    # Create log entry
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": str(user_id),
        "notification_type": notification_type,
        "recipient": recipient,
        "success": success
    }
    
    # Add additional details if provided
    if details:
        entry["details"] = details
    
    # Load existing log
    log_entries = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                log_entries = json.load(f)
        except Exception as e:
            logger.error(f"Error loading notification log: {str(e)}")
            # Continue with empty log if there was an error
    
    # Append new entry
    log_entries.append(entry)
    
    # Save updated log
    try:
        with open(log_file, "w") as f:
            json.dump(log_entries, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving notification log: {str(e)}")
        return False

def get_notification_statistics(
    notification_type: Optional[str] = None, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get statistics about notifications sent over a date range.
    
    Args:
        notification_type: Type of notification (email, sms, weekly_summary), or None for all types
        start_date: Start date string in YYYY-MM-DD format, defaults to 7 days ago
        end_date: End date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        Dictionary containing notification statistics
    """
    # Set default dates
    if end_date is None:
        end_date_obj = datetime.datetime.now()
        end_date = end_date_obj.strftime("%Y-%m-%d")
    else:
        end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    if start_date is None:
        start_date_obj = end_date_obj - datetime.timedelta(days=7)
        start_date = start_date_obj.strftime("%Y-%m-%d")
    else:
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    
    # Initialize statistics
    stats = {
        "start_date": start_date,
        "end_date": end_date,
        "total_sent": 0,
        "total_failed": 0,
        "by_date": {},
        "by_type": {}
    }
    
    # Generate list of dates in range
    current_date_obj = start_date_obj
    while current_date_obj <= end_date_obj:
        current_date = current_date_obj.strftime("%Y-%m-%d")
        stats["by_date"][current_date] = {"sent": 0, "failed": 0}
        
        # Check notifications for this date
        notification_types = ["email", "sms", "weekly_summary"]
        if notification_type:
            notification_types = [notification_type]
        
        for ntype in notification_types:
            if ntype not in stats["by_type"]:
                stats["by_type"][ntype] = {"sent": 0, "failed": 0}
            
            tracking_data = load_notification_tracking(ntype, current_date)
            sent = sum(1 for entry in tracking_data.values() if entry.get("success", False))
            failed = len(tracking_data) - sent
            
            # Update statistics
            stats["by_date"][current_date]["sent"] += sent
            stats["by_date"][current_date]["failed"] += failed
            stats["by_type"][ntype]["sent"] += sent
            stats["by_type"][ntype]["failed"] += failed
            stats["total_sent"] += sent
            stats["total_failed"] += failed
        
        # Move to next date
        current_date_obj += datetime.timedelta(days=1)
    
    return stats

def clear_tracking_data(notification_type: str, date: Optional[str] = None) -> bool:
    """
    Clear tracking data for a specific notification type and date.
    This is useful for testing or resetting notifications.
    
    Args:
        notification_type: Type of notification (email, sms, weekly_summary)
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        True if successful, False otherwise
    """
    tracking_file = get_notification_tracking_file(notification_type, date)
    
    if os.path.exists(tracking_file):
        try:
            # Backup the file before removing
            backup_file = f"{tracking_file}.bak"
            with open(tracking_file, "r") as src:
                with open(backup_file, "w") as dst:
                    dst.write(src.read())
            
            # Remove the file
            os.remove(tracking_file)
            logger.info(f"Cleared tracking data for {notification_type} on {date or 'today'}")
            return True
        except Exception as e:
            logger.error(f"Error clearing tracking data: {str(e)}")
            return False
    else:
        # File doesn't exist, nothing to clear
        return True

def get_users_without_notification(notification_type: str, users: List[Dict[str, Any]], date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get a list of users who haven't received a notification of a specific type on a specific date.
    
    Args:
        notification_type: Type of notification (email, sms, weekly_summary)
        users: List of user dictionaries
        date: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        List of users who haven't received the notification
    """
    tracking_data = load_notification_tracking(notification_type, date)
    
    # Filter users who haven't received notification
    users_without_notification = []
    for user in users:
        user_id = str(user.get("id", ""))
        if not user_id:
            continue
            
        if user_id not in tracking_data or not tracking_data[user_id].get("success", False):
            users_without_notification.append(user)
    
    return users_without_notification
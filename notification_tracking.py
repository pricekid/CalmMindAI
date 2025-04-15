"""
Notification tracking system to ensure users don't receive duplicate notifications.
This module maintains a record of sent notifications and provides functions to check and update this record.
"""
import os
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')

def get_tracking_file():
    """Get the path to the notification tracking file"""
    ensure_data_directory()
    return 'data/email_notifications_sent.json'

def load_tracking_data():
    """
    Load notification tracking data from the tracking file.
    
    Returns:
        dict: Tracking data with dates as keys and lists of user IDs as values
    """
    tracking_file = get_tracking_file()
    
    # Default structure for tracking data
    tracking_data = {
        'email': {},
        'sms': {},
        'weekly_summary': {}
    }
    
    # Load existing tracking data if available
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                data = json.load(f)
                
                # Convert old format to new format if needed
                if isinstance(data, list):
                    # Old format is a list of events, convert to new format
                    for entry in data:
                        if isinstance(entry, dict) and 'result' in entry:
                            # Skip entries that don't have user tracking data
                            if not isinstance(entry['result'], dict) or 'admin_test' in entry['result']:
                                continue
                                
                            # Try to extract date from timestamp
                            try:
                                date_str = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d')
                                if 'mass_notification' in entry['result']:
                                    mass_data = entry['result']['mass_notification']
                                    if 'sent_users' in mass_data and isinstance(mass_data['sent_users'], list):
                                        tracking_data['email'][date_str] = mass_data['sent_users']
                            except (ValueError, KeyError):
                                continue
                else:
                    # New format already, use it
                    tracking_data = data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading tracking data: {str(e)}")
    
    # Ensure all sections exist
    for section in ['email', 'sms', 'weekly_summary']:
        if section not in tracking_data:
            tracking_data[section] = {}
    
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Ensure current date exists in all tracking sections
    for section in tracking_data:
        if current_date not in tracking_data[section]:
            tracking_data[section][current_date] = []
    
    return tracking_data

def save_tracking_data(tracking_data):
    """
    Save notification tracking data to the tracking file.
    
    Args:
        tracking_data: Dictionary with tracking information
    
    Returns:
        bool: True if successful, False otherwise
    """
    tracking_file = get_tracking_file()
    
    try:
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving tracking data: {str(e)}")
        return False

def clean_old_tracking_data(tracking_data, days_to_keep=30):
    """
    Remove tracking data older than the specified number of days.
    
    Args:
        tracking_data: Dictionary with tracking information
        days_to_keep: Number of days of data to retain
    
    Returns:
        dict: Cleaned tracking data
    """
    # Calculate cutoff date
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
    
    # Clean up each section
    for section in tracking_data:
        section_data = tracking_data[section]
        dates_to_remove = []
        
        for date_str in section_data:
            if date_str < cutoff_date:
                dates_to_remove.append(date_str)
        
        for date_str in dates_to_remove:
            del section_data[date_str]
    
    return tracking_data

def track_notification(notification_type, user_id):
    """
    Record that a notification has been sent to a user.
    
    Args:
        notification_type: Type of notification ('email', 'sms', or 'weekly_summary')
        user_id: ID of the user who received the notification
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Validate notification type
    if notification_type not in ['email', 'sms', 'weekly_summary']:
        logger.error(f"Invalid notification type: {notification_type}")
        return False
    
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Load tracking data
    tracking_data = load_tracking_data()
    
    # Ensure current date exists
    if current_date not in tracking_data[notification_type]:
        tracking_data[notification_type][current_date] = []
    
    # Add user to tracking data if not already present
    if user_id not in tracking_data[notification_type][current_date]:
        tracking_data[notification_type][current_date].append(user_id)
        
        # Clean up old data
        tracking_data = clean_old_tracking_data(tracking_data)
        
        # Save updated tracking data
        return save_tracking_data(tracking_data)
    
    return True

def has_received_notification(notification_type, user_id, days=0):
    """
    Check if a user has received a notification within the specified timeframe.
    
    Args:
        notification_type: Type of notification ('email', 'sms', or 'weekly_summary')
        user_id: ID of the user to check
        days: Number of days to look back (0 for current day only)
    
    Returns:
        bool: True if the user has received the notification, False otherwise
    """
    # Validate notification type
    if notification_type not in ['email', 'sms', 'weekly_summary']:
        logger.error(f"Invalid notification type: {notification_type}")
        return False
    
    # Load tracking data
    tracking_data = load_tracking_data()
    
    # Check all days in the specified range
    for i in range(days + 1):
        check_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        
        if check_date in tracking_data[notification_type]:
            if user_id in tracking_data[notification_type][check_date]:
                return True
    
    return False

def get_notified_users(notification_type, days=0):
    """
    Get a list of user IDs who have received notifications within the specified timeframe.
    
    Args:
        notification_type: Type of notification ('email', 'sms', or 'weekly_summary')
        days: Number of days to look back (0 for current day only)
    
    Returns:
        list: List of user IDs who have received notifications
    """
    # Validate notification type
    if notification_type not in ['email', 'sms', 'weekly_summary']:
        logger.error(f"Invalid notification type: {notification_type}")
        return []
    
    # Load tracking data
    tracking_data = load_tracking_data()
    
    # Collect user IDs from all days in the specified range
    user_ids = set()
    
    for i in range(days + 1):
        check_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        
        if check_date in tracking_data[notification_type]:
            user_ids.update(tracking_data[notification_type][check_date])
    
    return list(user_ids)

def get_notification_stats():
    """
    Get statistics about sent notifications.
    
    Returns:
        dict: Statistics about notifications
    """
    # Load tracking data
    tracking_data = load_tracking_data()
    
    # Initialize stats
    stats = {
        'email': {
            'today': 0,
            'week': 0,
            'month': 0
        },
        'sms': {
            'today': 0,
            'week': 0,
            'month': 0
        },
        'weekly_summary': {
            'today': 0,
            'week': 0,
            'month': 0
        }
    }
    
    # Calculate stats for each notification type
    for notification_type in tracking_data:
        # Get unique user counts for different periods
        today_users = get_notified_users(notification_type, days=0)
        week_users = get_notified_users(notification_type, days=7)
        month_users = get_notified_users(notification_type, days=30)
        
        stats[notification_type]['today'] = len(today_users)
        stats[notification_type]['week'] = len(week_users)
        stats[notification_type]['month'] = len(month_users)
    
    return stats
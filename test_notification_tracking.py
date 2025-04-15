"""
Test script for the notification tracking system.
This script tests the functionality of the notification tracking module.
"""
import os
import json
import logging
from datetime import datetime
from notification_tracking import (
    track_notification, has_received_notification, 
    get_notified_users, get_notification_stats,
    clean_old_tracking_data, load_tracking_data, save_tracking_data
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tracking_system():
    """Test the notification tracking system"""
    logger.info("Testing notification tracking system...")
    
    # Load current tracking data
    tracking_data = load_tracking_data()
    logger.info(f"Current tracking data structure: {list(tracking_data.keys())}")
    
    # Get current stats
    initial_stats = get_notification_stats()
    logger.info(f"Initial notification stats: {json.dumps(initial_stats, indent=2)}")
    
    # Test tracking a notification
    test_user_id = 999  # Use a test user ID
    logger.info(f"Testing tracking notification for test user {test_user_id}...")
    
    # Track notifications of different types
    track_notification('email', test_user_id)
    track_notification('sms', test_user_id)
    
    # Check if user has received notifications
    has_email = has_received_notification('email', test_user_id)
    has_sms = has_received_notification('sms', test_user_id)
    
    logger.info(f"Test user has received email: {has_email}")
    logger.info(f"Test user has received SMS: {has_sms}")
    
    # Get updated stats
    updated_stats = get_notification_stats()
    logger.info(f"Updated notification stats: {json.dumps(updated_stats, indent=2)}")
    
    # Get notified users
    email_users = get_notified_users('email')
    sms_users = get_notified_users('sms')
    
    logger.info(f"Number of users who received email today: {len(email_users)}")
    logger.info(f"Number of users who received SMS today: {len(sms_users)}")
    
    # Clean up test data
    logger.info("Cleaning up test data...")
    tracking_data = load_tracking_data()
    
    # Remove test user from tracking data
    for notification_type in tracking_data:
        for date in tracking_data[notification_type]:
            if test_user_id in tracking_data[notification_type][date]:
                tracking_data[notification_type][date].remove(test_user_id)
    
    # Save cleaned tracking data
    save_tracking_data(tracking_data)
    
    # Verify cleanup
    has_email_after = has_received_notification('email', test_user_id)
    has_sms_after = has_received_notification('sms', test_user_id)
    
    logger.info(f"Test user has received email after cleanup: {has_email_after}")
    logger.info(f"Test user has received SMS after cleanup: {has_sms_after}")
    
    logger.info("Notification tracking system test completed.")

def main():
    """Main function to test the notification tracking system"""
    test_tracking_system()
    return 0

if __name__ == "__main__":
    main()
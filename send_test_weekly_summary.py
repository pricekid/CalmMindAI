"""
Script to immediately send a test weekly summary email with the updated referral message.
This will send a real email using the current email template.
"""
import os
import sys
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_test_weekly_summary(user_id=2):  # Default to Jeff Peter (user ID 2)
    """
    Send a test weekly summary email to a specific user to verify the referral message.
    
    Args:
        user_id: The ID of the user to send the test email to (default: 2)
    """
    try:
        # Load users
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        
        # Find the user with the specified ID
        user = None
        for u in users:
            if u.get('id') == user_id:
                user = u
                break
        
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return False
        
        logger.info(f"Sending test weekly summary to {user['username']} ({user['email']})")
        
        # Create sample stats for the weekly summary
        sample_stats = {
            'entries': 3,
            'avg_anxiety': 5.7,
            'common_pattern': 'Work-related stress'
        }
        
        # Import the send_weekly_summary function
        from notification_service import send_weekly_summary
        
        # Send the test email
        result = send_weekly_summary(user, sample_stats)
        
        if result:
            logger.info(f"Successfully sent test weekly summary to {user['username']} ({user['email']})")
            return True
        else:
            logger.error(f"Failed to send test weekly summary to {user['username']} ({user['email']})")
            return False
    except Exception as e:
        logger.error(f"Error sending test weekly summary: {str(e)}")
        return False

if __name__ == "__main__":
    print("Sending test weekly summary email with referral message...")
    
    # Use Jeff Peter (user ID 2) by default
    user_id = 2  # naturalarts@gmail.com
    
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid user ID: {sys.argv[1]}. Using default user ID 2.")
    
    success = send_test_weekly_summary(user_id)
    
    if success:
        print("Test weekly summary email sent successfully! Check your inbox to see the referral message.")
    else:
        print("Failed to send test weekly summary email. Check the logs for more information.")
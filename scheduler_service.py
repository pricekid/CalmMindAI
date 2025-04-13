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
    
    # Prepare tracking file to avoid duplicate notifications
    ensure_data_directory()
    tracking_file = 'data/sms_notifications_sent.json'
    
    # Load existing tracking data
    tracking_data = {}
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            tracking_data = {}
    
    # Make sure today's date exists in tracking
    if current_date not in tracking_data:
        tracking_data[current_date] = []
    
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
        if user_id in tracking_data[current_date]:
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
                # Track successful notification
                tracking_data[current_date].append(user_id)
                sent_count += 1
                logger.info(f"SMS sent to user {user_id} at {phone_number}")
            else:
                logger.error(f"Failed to send SMS to user {user_id}: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error sending SMS to user {user_id}: {str(e)}")
        
        # Brief pause to avoid rate limiting
        time.sleep(1)
    
    # Save updated tracking data
    try:
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f)
    except Exception as e:
        logger.error(f"Error saving SMS tracking data: {str(e)}")
    
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
    from notification_service import send_notification  # Import here to avoid circular import
    
    # Stats tracking
    total_users = 0
    sent_count = 0
    skipped_count = 0
    
    # Load all users
    users = load_users()
    total_users = len(users)
    
    # Get current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Prepare tracking file to avoid duplicate notifications
    tracking_file = 'data/email_notifications_sent.json'
    
    # Load existing tracking data
    tracking_data = {}
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            tracking_data = {}
    
    # Make sure today's date exists in tracking
    if current_date not in tracking_data:
        tracking_data[current_date] = []
    
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
        if user_id in tracking_data[current_date]:
            logger.info(f"Skipping user {user_id}: Already received email today")
            skipped_count += 1
            continue
        
        # Get username for personalization
        username = user.get('username', 'there')
        
        # Send a simple daily journaling reminder
        try:
            # Construct email content
            subject = "Your Daily Journal Reminder"
            message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
                <div style="padding: 20px; background-color: #f7f2e9; border-radius: 10px; border-left: 4px solid #e6b980;">
                    <h2 style="color: #5f4b32; margin-top: 0;">Hello {username},</h2>
                    
                    <p>This is your gentle reminder to take a moment for yourself today and journal in Calm Journey.</p>
                    
                    <p>Even a brief entry can help you process your thoughts and emotions.</p>
                    
                    <div style="text-align: center; margin: 25px 0;">
                        <a href="https://calm-journey.replit.app/login" style="display: inline-block; background-color: #e6b980; color: #5f4b32; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Open Your Journal</a>
                    </div>
                    
                    <p style="font-style: italic; color: #7d6b4c;">Wishing you a peaceful and mindful day,<br>The Calm Journey Team</p>
                </div>
            </body>
            </html>
            """
            
            # Send the email
            result = send_notification(email, subject, message)
            
            if isinstance(result, dict) and result.get('success'):
                # Track successful notification
                tracking_data[current_date].append(user_id)
                sent_count += 1
                logger.info(f"Email sent to user {user_id} at {email}")
            else:
                error_msg = result.get('error') if isinstance(result, dict) else str(result)
                logger.error(f"Failed to send email to user {user_id}: {error_msg}")
        except Exception as e:
            logger.error(f"Error sending email to user {user_id}: {str(e)}")
        
        # Brief pause to avoid rate limiting
        time.sleep(1)
    
    # Save updated tracking data
    try:
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f)
    except Exception as e:
        logger.error(f"Error saving email tracking data: {str(e)}")
    
    # Return stats
    return {
        "total_users": total_users,
        "sent_count": sent_count,
        "skipped_count": skipped_count,
        "timestamp": datetime.datetime.now().isoformat()
    }
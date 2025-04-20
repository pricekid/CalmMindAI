import os
import logging
from datetime import datetime
from models import User
from app import db
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio configuration will be retrieved from environment variables at function call time
# This ensures we always use the latest values from the admin panel

# List of journaling tips for daily SMS reminders
JOURNALING_TIPS = [
    "Focus on gratitude in today's journal entry",
    "Try writing about a recent challenge and how you overcame it",
    "Reflect on your emotional patterns this week",
    "Write about one thing you'd like to improve",
    "List three things that made you smile today",
    "Describe a moment of peace you experienced recently",
    "Try a stream-of-consciousness writing for 5 minutes",
    "Reflect on a relationship that's important to you",
    "Write about your goals for the upcoming week",
    "Express a feeling you've been avoiding",
    "Write a letter to your future self",
    "Express yourself freely without judgment",
    "Build self-awareness through reflection"
]

def send_sms_notification(to_phone_number, message):
    """Send an SMS notification using Twilio."""
    # Get the latest Twilio credentials from environment variables
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
    
    if not all([twilio_sid, twilio_token, twilio_phone]):
        logger.error("Twilio credentials not configured. SMS notification not sent.")
        return False
    
    try:
        client = Client(twilio_sid, twilio_token)
        
        # Sending the SMS message
        sent_message = client.messages.create(
            body=message,
            from_=twilio_phone,
            to=to_phone_number
        )
        
        logger.info(f"SMS sent with SID: {sent_message.sid} to {to_phone_number}")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send SMS notification: {str(e)}")
        return False

def send_daily_sms_reminder():
    """Send daily SMS reminders to all users who have SMS notifications enabled."""
    # Query users with SMS notifications enabled and a phone number
    users = User.query.filter_by(
        sms_notifications_enabled=True
    ).filter(User.phone_number.isnot(None)).all()
    
    tip = JOURNALING_TIPS[datetime.now().day % len(JOURNALING_TIPS)]
    
    # Standardized referral text for SMS
    referral_text = "Know someone who needs support? Share Calm Journey: https://calm-mind-ai-naturalarts.replit.app"
    
    for user in users:
        try:
            message = f"Calm Journey: Take a moment to reflect and journal today. Tip: {tip}\n\n{referral_text}"
            success = send_sms_notification(user.phone_number, message)
            
            if success:
                logger.info(f"Sent SMS reminder to {user.username} at {user.phone_number}")
            else:
                logger.warning(f"Failed to send SMS to {user.username} at {user.phone_number}")
                
        except Exception as e:
            logger.error(f"Error sending SMS to {user.username}: {str(e)}")

def send_immediate_sms_to_all_users():
    """Send an immediate SMS notification to all users reminding them to journal."""
    users = User.query.filter_by(
        sms_notifications_enabled=True
    ).filter(User.phone_number.isnot(None)).all()
    
    # Standardized referral text for SMS
    referral_text = "Know someone who needs support? Share Calm Journey: https://calm-mind-ai-naturalarts.replit.app"
    
    message = f"Calm Journey: Take a moment for yourself right now. How are you feeling? Log into your journal and express yourself.\n\n{referral_text}"
    
    success_count = 0
    failure_count = 0
    
    for user in users:
        try:
            success = send_sms_notification(user.phone_number, message)
            
            if success:
                success_count += 1
                logger.info(f"Sent immediate SMS to {user.username} at {user.phone_number}")
            else:
                failure_count += 1
                logger.warning(f"Failed to send immediate SMS to {user.username} at {user.phone_number}")
                
        except Exception as e:
            failure_count += 1
            logger.error(f"Error sending immediate SMS to {user.username}: {str(e)}")
    
    return {
        "success_count": success_count,
        "failure_count": failure_count,
        "total_attempts": success_count + failure_count
    }
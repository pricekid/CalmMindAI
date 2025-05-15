"""
Journal reminder notification service.
This module schedules and sends journal reminder notifications based on user preferences.
"""
import logging
import os
from datetime import datetime, timedelta
import pytz
from flask import current_app, url_for
from models import User, PushSubscription
from app import db
from sqlalchemy import text
from push_notification_service import send_notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default prompts for morning and evening reminders
DEFAULT_MORNING_PROMPTS = [
    "What would make today feel like a win?",
    "What's one thing you're looking forward to today?",
    "How are you feeling this morning, and what might impact your day?",
    "What's one small thing you can do today to take care of yourself?",
    "What intention would you like to set for today?"
]

DEFAULT_EVENING_PROMPTS = [
    "What's one thought you want to leave here tonight?",
    "What went well today that you'd like to acknowledge?",
    "What's something that challenged you today, and how did you respond?",
    "What did you learn about yourself today?",
    "What are you grateful for from today?"
]


def get_current_time_in_user_timezone(user_timezone=None):
    """
    Get the current time in the user's timezone.
    Falls back to UTC if no timezone is provided.
    """
    user_tz = pytz.timezone(user_timezone) if user_timezone else pytz.UTC
    return datetime.now(user_tz)


def should_send_morning_reminder(user):
    """
    Check if a morning reminder should be sent to this user.
    
    Args:
        user: User object with notification preferences
        
    Returns:
        bool: True if a morning reminder should be sent
    """
    # Skip if user has notifications disabled or morning reminders disabled
    if not user.notifications_enabled or not user.morning_reminder_enabled:
        return False
        
    # For now, we'll use server time without timezone considerations
    # In a future update, we can add user timezone preferences
    current_time = datetime.now().time()
    target_time = user.morning_reminder_time
    
    # Check if current time is within 5 minutes of the target time
    # This is to account for scheduler running at intervals
    current_minutes = current_time.hour * 60 + current_time.minute
    target_minutes = target_time.hour * 60 + target_time.minute
    
    return abs(current_minutes - target_minutes) <= 5


def should_send_evening_reminder(user):
    """
    Check if an evening reminder should be sent to this user.
    
    Args:
        user: User object with notification preferences
        
    Returns:
        bool: True if an evening reminder should be sent
    """
    # Skip if user has notifications disabled or evening reminders disabled
    if not user.notifications_enabled or not user.evening_reminder_enabled:
        return False
        
    # For now, we'll use server time without timezone considerations
    current_time = datetime.now().time()
    target_time = user.evening_reminder_time
    
    # Check if current time is within 5 minutes of the target time
    current_minutes = current_time.hour * 60 + current_time.minute
    target_minutes = target_time.hour * 60 + target_time.minute
    
    return abs(current_minutes - target_minutes) <= 5


def get_random_prompt(prompt_type="morning"):
    """
    Get a random prompt based on the time of day.
    
    Args:
        prompt_type: 'morning' or 'evening'
        
    Returns:
        str: A journaling prompt
    """
    import random
    
    if prompt_type == "morning":
        return random.choice(DEFAULT_MORNING_PROMPTS)
    else:  # evening
        return random.choice(DEFAULT_EVENING_PROMPTS)


def send_journal_reminder_notifications():
    """
    Scan for users who should receive journal reminders and send notifications.
    This function is intended to be called periodically by a scheduler.
    """
    try:
        logger.info("Checking for users who need journal reminder notifications...")
        
        # Get all users with notifications enabled
        users = User.query.filter_by(notifications_enabled=True).all()
        
        morning_count = 0
        evening_count = 0
        
        for user in users:
            # Skip users with no push subscriptions
            if not user.push_subscriptions.count():
                continue
                
            # Check if we should send a morning reminder
            if should_send_morning_reminder(user):
                prompt = get_random_prompt("morning")
                send_journal_reminder(user, prompt, "morning")
                morning_count += 1
                
            # Check if we should send an evening reminder
            if should_send_evening_reminder(user):
                prompt = get_random_prompt("evening")
                send_journal_reminder(user, prompt, "evening")
                evening_count += 1
        
        logger.info(f"Sent {morning_count} morning reminders and {evening_count} evening reminders")
        
    except Exception as e:
        logger.error(f"Error sending journal reminder notifications: {e}")


def send_journal_reminder(user, prompt, reminder_type):
    """
    Send a journal reminder notification to a specific user.
    
    Args:
        user: User object to send the notification to
        prompt: The journaling prompt to include
        reminder_type: 'morning' or 'evening'
    """
    try:
        # Get all push subscriptions for this user
        subscriptions = PushSubscription.query.filter_by(user_id=user.id).all()
        
        if not subscriptions:
            logger.warning(f"User {user.id} has no push subscriptions")
            return
            
        title = "Time to journal with Dear Teddy"
        body = prompt
        
        # URL to redirect to when notification is clicked
        dashboard_url = url_for('dashboard', _external=True)
        
        # Add this notification to the record
        with db.engine.begin() as conn:
            current_time = datetime.utcnow()
            conn.execute(
                text("INSERT INTO notification_log (user_id, notification_type, sent_at) VALUES (:user_id, :type, :sent_at)"),
                {"user_id": user.id, "type": f"journal_reminder_{reminder_type}", "sent_at": current_time}
            )
            
        # Send the notification to the user
        send_notification(
            user_id=user.id,
            title=title,
            body=body,
            url=dashboard_url,
            tag=f"journal_reminder_{reminder_type}"
        )
            
        logger.info(f"Sent {reminder_type} journal reminder to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error sending journal reminder to user {user.id}: {e}")
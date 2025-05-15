"""
Push Notification Service for Dear Teddy

This module provides the backend functionality for Web Push notifications.
It allows the application to send push notifications to users who have
granted notification permissions and subscribed through their browser.
"""

import json
import os
import base64
import logging
from flask import current_app
from pywebpush import webpush, WebPushException
from app import db
from models import PushSubscription, User

logger = logging.getLogger(__name__)

# VAPID keys for Web Push - would typically be stored as environment variables
# We need to generate these keys for production
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
VAPID_CLAIMS = {
    "sub": "mailto:dearteddy@gmail.com",  # Using the same email as password reset
    "aud": "https://fcm.googleapis.com"
}

def get_public_key():
    """
    Get the VAPID public key for clients to use when subscribing.
    
    Returns:
        str: The VAPID public key
    """
    if not VAPID_PUBLIC_KEY:
        logger.warning("VAPID public key is not set. Push notifications will not work.")
        return None
    return VAPID_PUBLIC_KEY

def save_subscription(user_id, subscription_json):
    """
    Save a new push subscription for a user.
    
    Args:
        user_id (str): The user's ID
        subscription_json (str): JSON string containing the subscription info
        
    Returns:
        PushSubscription: The created subscription object
    """
    try:
        # Check if this subscription already exists for this user
        existing = PushSubscription.query.filter_by(
            user_id=user_id, 
            subscription_json=subscription_json
        ).first()
        
        if existing:
            logger.info(f"Subscription already exists for user {user_id}")
            return existing
            
        # Create a new subscription with Flask-SQLAlchemy model
        subscription = PushSubscription()
        subscription.user_id = user_id
        subscription.subscription_json = subscription_json
        subscription.journal_reminders = True
        subscription.mood_reminders = True
        subscription.feature_updates = True
        
        db.session.add(subscription)
        db.session.commit()
        logger.info(f"Created new push subscription for user {user_id}")
        return subscription
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving push subscription: {e}")
        return None

def delete_subscription(subscription_id):
    """
    Delete a push subscription.
    
    Args:
        subscription_id (int): The ID of the subscription to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        subscription = PushSubscription.query.get(subscription_id)
        if subscription:
            db.session.delete(subscription)
            db.session.commit()
            logger.info(f"Deleted push subscription {subscription_id}")
            return True
        return False
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting push subscription: {e}")
        return False

def send_notification(user_id, title, body, url=None, tag=None):
    """
    Send a push notification to all subscriptions for a specific user.
    
    Args:
        user_id (str): The user's ID
        title (str): The notification title
        body (str): The notification body text
        url (str, optional): URL to open when notification is clicked
        tag (str, optional): Tag to group notifications
        
    Returns:
        dict: Results with success and failure counts
    """
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        logger.error("VAPID keys not configured. Push notification not sent.")
        return {"success": 0, "failed": 0}
    
    subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()
    if not subscriptions:
        logger.info(f"No push subscriptions found for user {user_id}")
        return {"success": 0, "failed": 0}
    
    success_count = 0
    failed_count = 0
    
    # Prepare notification data
    data = {
        "title": title,
        "body": body
    }
    
    if url:
        data["url"] = url
    if tag:
        data["tag"] = tag
    
    for subscription in subscriptions:
        try:
            subscription_data = json.loads(subscription.subscription_json)
            webpush(
                subscription_info=subscription_data,
                data=json.dumps(data),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            
            # Update last notification timestamp
            subscription.last_notification_at = db.func.now()
            db.session.commit()
            
            success_count += 1
            logger.info(f"Successfully sent push notification to subscription {subscription.id}")
            
        except WebPushException as e:
            # If the subscription is expired or invalid
            if e.response and e.response.status_code in [404, 410]:
                logger.warning(f"Subscription {subscription.id} is no longer valid, removing it")
                db.session.delete(subscription)
                db.session.commit()
            
            failed_count += 1
            logger.error(f"WebPush failed for subscription {subscription.id}: {e}")
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Error sending push notification: {e}")
    
    return {
        "success": success_count,
        "failed": failed_count
    }

def send_notification_to_all_users(title, body, url=None, tag=None):
    """
    Send a push notification to all users with active subscriptions.
    
    Args:
        title (str): The notification title
        body (str): The notification body text
        url (str, optional): URL to open when notification is clicked
        tag (str, optional): Tag to group notifications
        
    Returns:
        dict: Results with success and failure counts
    """
    users = User.query.join(PushSubscription).distinct().all()
    
    total_success = 0
    total_failed = 0
    
    for user in users:
        result = send_notification(user.id, title, body, url, tag)
        total_success += result["success"]
        total_failed += result["failed"]
    
    return {
        "success": total_success,
        "failed": total_failed,
        "users_notified": len(users)
    }

def send_test_notification(user_id):
    """
    Send a test notification to a user.
    
    Args:
        user_id (str): The user's ID
        
    Returns:
        dict: Results of the notification attempt
    """
    return send_notification(
        user_id=user_id,
        title="Test Notification",
        body="This is a test notification from Dear Teddy!",
        url="/dashboard",
        tag="test"
    )

def generate_vapid_keys():
    """
    Generate VAPID keys for Web Push if they don't already exist.
    This should be run once during initial setup.
    
    Returns:
        dict: The generated public and private keys
    """
    try:
        from py_vapid import Vapid
        
        vapid = Vapid()
        vapid.generate_keys()
        
        # Export keys in the correct format for webpush
        private_key = vapid.private_key
        if private_key:
            private_key = private_key.encode().decode('utf8')
            
        public_key = vapid.public_key
        if public_key:
            public_key = base64.urlsafe_b64encode(public_key.encode()).decode('utf8')
        
        logger.info("Generated new VAPID keys for Web Push")
        
        return {
            "public_key": public_key,
            "private_key": private_key
        }
    except Exception as e:
        logger.error(f"Error generating VAPID keys: {e}")
        return None
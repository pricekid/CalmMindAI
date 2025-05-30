"""
Push Notification Routes for Dear Teddy

This module provides endpoints for managing web push notifications:
- Subscribe to push notifications
- Unsubscribe from push notifications
- Test push notifications
- Update notification preferences
"""

import json
import logging
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from push_notification_service import (
    get_public_key, save_subscription, delete_subscription,
    send_test_notification, generate_vapid_keys
)

# Create blueprint
push_notification_bp = Blueprint('push_notifications', __name__)
logger = logging.getLogger(__name__)

@push_notification_bp.route('/push-key', methods=['GET'])
def get_push_key():
    """
    Return the public VAPID key for web push subscriptions.
    This is used by the frontend to configure the subscription process.
    """
    public_key = get_public_key()
    if not public_key:
        return jsonify({"error": "Push notifications are not configured"}), 500
    return jsonify({"public_key": public_key})

@push_notification_bp.route('/push-subscribe', methods=['POST'])
@login_required
def subscribe():
    """
    Subscribe a user to push notifications. This endpoint is called
    by the frontend after the user has granted notification permissions.
    """
    subscription_json = request.json
    if not subscription_json:
        return jsonify({"error": "No subscription data provided"}), 400
    
    # Save the subscription
    result = save_subscription(
        user_id=current_user.id,
        subscription_json=json.dumps(subscription_json)
    )
    
    if result:
        return jsonify({"success": True, "message": "Subscription saved successfully"})
    else:
        return jsonify({"error": "Failed to save subscription"}), 500

@push_notification_bp.route('/push-unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """
    Unsubscribe a user from push notifications.
    """
    subscription_id = request.json.get('subscription_id')
    if not subscription_id:
        return jsonify({"error": "No subscription ID provided"}), 400
    
    # Delete the subscription
    result = delete_subscription(subscription_id)
    if result:
        return jsonify({"success": True, "message": "Unsubscribed successfully"})
    else:
        return jsonify({"error": "Failed to unsubscribe"}), 500

@push_notification_bp.route('/push-test', methods=['POST'])
@login_required
def test_notification():
    """
    Send a test notification to the current user.
    """
    result = send_test_notification(current_user.id)
    if result and result["success"] > 0:
        return jsonify({
            "success": True, 
            "message": f"Test notification sent successfully to {result['success']} device(s)"
        })
    else:
        return jsonify({
            "error": "No notifications were sent. Make sure you have subscribed on this device."
        }), 400

@push_notification_bp.route('/push-settings', methods=['GET'])
@login_required
def notification_settings():
    """
    Render the push notification settings page.
    """
    # Get list of user's current subscriptions
    from models import PushSubscription
    subscriptions = PushSubscription.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'notification_settings.html',
        subscriptions=subscriptions
    )

@push_notification_bp.route('/push-generate-keys', methods=['POST'])
def generate_keys():
    """
    Generate new VAPID keys for web push. This is an admin-only endpoint
    and should be secured in production.
    """
    # In production, this should be protected with admin authentication
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401
        
    # For simplicity in this demo, we're checking for admin status
    # In a real app, use proper admin authentication
    if getattr(current_user, 'username', '') != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    keys = generate_vapid_keys()
    if keys:
        return jsonify({
            "success": True,
            "message": "VAPID keys generated successfully. Set these as environment variables.",
            "keys": keys
        })
    else:
        return jsonify({"error": "Failed to generate VAPID keys"}), 500

def init_app(app):
    """
    Register the push notification blueprint with the Flask app.
    """
    app.register_blueprint(push_notification_bp)
    app.logger.info("Push notification routes registered successfully")
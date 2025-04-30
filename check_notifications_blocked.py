"""
Function to check if notifications are blocked by a block file.
This will be imported by notification_service.py to prevent emails from being sent.
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_notifications_blocked():
    """Check if notifications are blocked by a block file"""
    block_file = "data/notifications_blocked"
    if os.path.exists(block_file):
        logger.warning(f"Notifications are blocked by {block_file}")
        return True
    return False

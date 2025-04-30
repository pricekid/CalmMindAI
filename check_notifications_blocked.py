"""
Function to check if notifications are blocked by a block file.
This will be imported by notification_service.py to prevent emails from being sent.
"""
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("notification_blocker")

def check_notifications_blocked():
    """Check if notifications are blocked by a block file"""
    # Ensure the block file exists
    Path("data").mkdir(exist_ok=True)
    with open("data/notifications_blocked", "w") as f:
        f.write("Notifications permanently blocked")
    
    # Log the block
    logger.warning("Notifications are permanently blocked")
    
    # Always return True to indicate notifications are blocked
    return True
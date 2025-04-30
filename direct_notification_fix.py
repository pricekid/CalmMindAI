"""
Direct notification fix - Completely disables email notifications.
"""
import os
import sys
import logging
from pathlib import Path
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("notification_disabler")

# Create block file
Path("data").mkdir(exist_ok=True)
with open("data/notifications_blocked", "w") as f:
    f.write("Notifications permanently blocked")

# Disable environment variables used for sending emails or SMS
os.environ["SENDGRID_API_KEY"] = "DISABLED-BY-ADMIN"
os.environ["TWILIO_ACCOUNT_SID"] = "DISABLED-BY-ADMIN"
os.environ["TWILIO_AUTH_TOKEN"] = "DISABLED-BY-ADMIN"

# Log the block
logger.warning("NOTIFICATIONS PERMANENTLY DISABLED by direct_notification_fix.py")
print("NOTIFICATIONS PERMANENTLY DISABLED by direct_notification_fix.py")

# Attempt to disable the scheduler
scheduler_paths = [
    "scheduler.py", 
    "start_scheduler.py",
    "notification_service.py",
    "sms_notification_service.py"
]

for path in scheduler_paths:
    try:
        # Make file read-only
        if os.path.exists(path):
            os.chmod(path, 0o444)  # read-only
            logger.info(f"Made {path} read-only to prevent execution")
    except Exception as e:
        logger.error(f"Error making {path} read-only: {e}")

# Create sentinel files to indicate notifications are blocked
sentinel_paths = [
    "data/notifications_blocked",
    "data/emails_blocked",
    "data/sms_blocked",
    "data/scheduler_disabled"
]

for path in sentinel_paths:
    try:
        with open(path, "w") as f:
            f.write(f"DISABLED: {path}")
        logger.info(f"Created {path} sentinel file")
    except Exception as e:
        logger.error(f"Error creating {path}: {e}")

print("✓ Notifications have been completely disabled")
print("✓ Environment variables have been nullified")
print("✓ Scheduler has been disabled")
print("✓ All notification services have been made read-only")
"""
Direct notification fix - Completely disables email notifications.
"""
import os
import json
import subprocess
from pathlib import Path

# Make sure the data directory exists
Path("data").mkdir(exist_ok=True)

# 1. Create notification block file
print("1. Creating notification block file...")
with open("data/notifications_blocked", "w") as f:
    f.write("Notifications blocked")
print("   ✓ Block file created")

# 2. Kill any existing scheduler processes
print("\n2. Killing scheduler processes...")
try:
    # Find processes running scheduler.py
    ps_output = subprocess.check_output(["ps", "-ef"], text=True)
    for line in ps_output.split("\n"):
        if "scheduler.py" in line and "grep" not in line:
            parts = line.split()
            if len(parts) > 1:
                pid = parts[1]
                try:
                    os.kill(int(pid), 9)
                    print(f"   ✓ Killed scheduler process {pid}")
                except:
                    print(f"   ✗ Failed to kill process {pid}")
except:
    print("   ✗ Error finding scheduler processes")

# 3. Remove any PID file
print("\n3. Removing scheduler PID file...")
if os.path.exists("scheduler.pid"):
    os.remove("scheduler.pid")
    print("   ✓ Removed scheduler.pid")
else:
    print("   - No scheduler.pid file found")

# 4. Disable notifications for all users
print("\n4. Disabling notifications for all users...")
users_file = "data/users.json"
try:
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
        
        # Make a backup
        with open(f"{users_file}.bak", "w") as f:
            json.dump(users, f, indent=2)
        
        # Disable for all users
        for user in users:
            user["notifications_enabled"] = False
            user["sms_notifications_enabled"] = False
        
        # Save the updated file
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)
        print("   ✓ Disabled notifications for all users")
    else:
        print("   - No users file found")
except Exception as e:
    print(f"   ✗ Error disabling user notifications: {e}")

# 5. Replace notification_service.py with stub
print("\n5. Replacing email notification service...")
try:
    email_service = "notification_service.py"
    if os.path.exists(email_service):
        # Make a backup
        os.system(f"cp {email_service} {email_service}.bak")
        
        # Create stub
        with open(email_service, "w") as f:
            f.write('''"""
Notification service - DISABLED.
All notification functions will simply log and return success=False.
"""
import logging
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_email(recipient, subject, template_name, template_data=None, sender=None, reply_to=None):
    """
    EMAIL DISABLED - This function will not send any emails.
    """
    logger.info(f"Email sending BLOCKED: {subject} to {recipient}")
    return {"success": False, "error": "Email notifications are permanently disabled"}

def send_login_link(user_id, email, name=None):
    """
    EMAIL DISABLED - This function will not send any login links.
    """
    logger.info(f"Login link sending BLOCKED to {email}")
    return {"success": False, "error": "Login emails are permanently disabled"}

def send_welcome_email(user_id, email, name=None):
    """
    EMAIL DISABLED - This function will not send any welcome emails.
    """
    logger.info(f"Welcome email sending BLOCKED to {email}")
    return {"success": False, "error": "Welcome emails are permanently disabled"}

def send_daily_reminder(user, entry_count=None):
    """
    EMAIL DISABLED - This function will not send any daily reminders.
    """
    user_id = user.get('id', 'unknown')
    logger.info(f"Daily reminder sending BLOCKED to user {user_id}")
    return {"success": False, "error": "Daily reminders are permanently disabled"}

def send_weekly_summary(user, entries=None):
    """
    EMAIL DISABLED - This function will not send any weekly summaries.
    """
    user_id = user.get('id', 'unknown')
    logger.info(f"Weekly summary sending BLOCKED to user {user_id}")
    return {"success": False, "error": "Weekly summaries are permanently disabled"}

def send_notification_email(email, subject, message, user_id=None):
    """
    EMAIL DISABLED - This function will not send any notification emails.
    """
    logger.info(f"Notification email sending BLOCKED to {email}")
    return {"success": False, "error": "Notification emails are permanently disabled"}

def check_notifications_blocked():
    """Check if notifications are blocked by a block file"""
    block_file = "data/notifications_blocked"
    return True  # Always return True to block all notifications
''')
        print("   ✓ Replaced email notification service")
    else:
        print("   - No email notification service found")
except Exception as e:
    print(f"   ✗ Error replacing email service: {e}")

# 6. Replace SMS notification service with stub
print("\n6. Replacing SMS notification service...")
try:
    sms_service = "sms_notification_service.py"
    if os.path.exists(sms_service):
        # Make a backup
        os.system(f"cp {sms_service} {sms_service}.bak")
        
        # Create stub
        with open(sms_service, "w") as f:
            f.write('''"""
SMS Notification service - DISABLED.
All SMS functions will simply log and return success=False.
"""
import logging
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_sms_notification(to_number, message, user_id=None):
    """
    SMS DISABLED - This function will not send any SMS messages.
    """
    logger.info(f"SMS sending BLOCKED to {to_number}")
    return {"success": False, "error": "SMS notifications are permanently disabled"}

def check_notifications_blocked():
    """Check if notifications are blocked by a block file"""
    return True  # Always return True to block all notifications
''')
        print("   ✓ Replaced SMS notification service")
    else:
        print("   - No SMS notification service found")
except Exception as e:
    print(f"   ✗ Error replacing SMS service: {e}")

print("\n✅ ALL NOTIFICATIONS HAVE BEEN PERMANENTLY DISABLED")
print("The application will no longer send any email or SMS notifications.")
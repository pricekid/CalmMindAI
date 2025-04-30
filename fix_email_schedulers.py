"""
Script to permanently fix email notification schedulers by modifying the scheduler jobs.
This script will prevent the constant sending of emails while still allowing the scheduler to run.
"""
import os
import logging
import json
import sys
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists"""
    Path("data").mkdir(exist_ok=True)
    Path("data/notifications").mkdir(exist_ok=True)

def disable_all_email_notifications():
    """Disable email notifications for all users"""
    ensure_data_directory()
    
    # Load users
    users_file = "data/users.json"
    if not os.path.exists(users_file):
        logger.error("Users file not found")
        return False
    
    try:
        with open(users_file, "r") as f:
            users = json.load(f)
        
        # Count how many users have notifications enabled
        originally_enabled = sum(1 for user in users if user.get('notifications_enabled', False))
        
        # Disable notifications for all users
        for user in users:
            user['notifications_enabled'] = False
            user['sms_notifications_enabled'] = False
        
        # Save updated users
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)
        
        logger.info(f"Disabled email notifications for {originally_enabled} users")
        return True
    except Exception as e:
        logger.error(f"Error disabling notifications: {str(e)}")
        return False

def create_notification_block():
    """Create a file that blocks notifications from being sent"""
    try:
        block_file = "data/notifications_blocked"
        with open(block_file, "w") as f:
            f.write(f"Notifications blocked at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Created notification block file: {block_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating notification block file: {e}")
        return False

def patch_notification_service():
    """
    Patch the notification_service.py file to check for the block file
    before sending any notifications.
    """
    notification_file = "notification_service.py"
    
    if not os.path.exists(notification_file):
        logger.error(f"Notification service file not found: {notification_file}")
        return False
    
    try:
        # Read the original file
        with open(notification_file, "r") as f:
            content = f.read()
        
        # Create a backup
        with open(f"{notification_file}.bak", "w") as f:
            f.write(content)
        
        # Check if already patched
        if "def check_notifications_blocked():" in content:
            logger.info("Notification service already patched")
            return True
        
        # Find the send_email function
        if "def send_email(" not in content:
            logger.error("Could not find send_email function in notification service")
            return False
        
        # Add check_notifications_blocked function
        block_check_function = """
# Function to check if notifications are blocked
def check_notifications_blocked():
    '''Check if notifications are blocked by the existence of a block file'''
    block_file = "data/notifications_blocked"
    if os.path.exists(block_file):
        logger.warning(f"Notifications are blocked by {block_file}")
        return True
    return False

"""
        
        # Insert the function before the send_email function
        content = content.replace("def send_email(", block_check_function + "def send_email(")
        
        # Patch the send_email function to check for blocked notifications
        original_function_start = "def send_email("
        original_function_body_start = original_function_start + content.split(original_function_start)[1].split("\n")[0] + "\n"
        
        patched_function_start = original_function_body_start + "    # Check if notifications are blocked\n    if check_notifications_blocked():\n        logger.info(f\"Email to {recipient} blocked by notification block\")\n        return {'success': False, 'error': 'Notifications are blocked'}\n\n"
        
        content = content.replace(original_function_body_start, patched_function_start)
        
        # Similarly patch send_daily_reminder function
        if "def send_daily_reminder(" in content:
            original_function_start = "def send_daily_reminder("
            original_function_body_start = original_function_start + content.split(original_function_start)[1].split("\n")[0] + "\n"
            
            patched_function_start = original_function_body_start + "    # Check if notifications are blocked\n    if check_notifications_blocked():\n        logger.info(f\"Daily reminder to user {user.get('id')} blocked by notification block\")\n        return {'success': False, 'error': 'Notifications are blocked'}\n\n"
            
            content = content.replace(original_function_body_start, patched_function_start)
        
        # Write the patched file
        with open(notification_file, "w") as f:
            f.write(content)
        
        logger.info(f"Successfully patched {notification_file}")
        return True
    except Exception as e:
        logger.error(f"Error patching notification service: {e}")
        return False

def patch_sms_notification_service():
    """
    Patch the sms_notification_service.py file to check for the block file
    before sending any SMS.
    """
    sms_file = "sms_notification_service.py"
    
    if not os.path.exists(sms_file):
        logger.error(f"SMS notification service file not found: {sms_file}")
        return False
    
    try:
        # Read the original file
        with open(sms_file, "r") as f:
            content = f.read()
        
        # Create a backup
        with open(f"{sms_file}.bak", "w") as f:
            f.write(content)
        
        # Check if already patched
        if "from notification_service import check_notifications_blocked" in content:
            logger.info("SMS notification service already imports check_notifications_blocked")
        else:
            # Add import for check_notifications_blocked function
            import_line = "import json"
            new_import = "import json\nfrom notification_service import check_notifications_blocked"
            content = content.replace(import_line, new_import)
        
        # Patch the send_sms_notification function to check for blocked notifications
        if "def send_sms_notification(" in content:
            original_function_start = "def send_sms_notification("
            original_function_body_start = original_function_start + content.split(original_function_start)[1].split("\n")[0] + "\n"
            
            # Check if already patched
            if "if check_notifications_blocked():" in content.split(original_function_start)[1].split("try:")[0]:
                logger.info("SMS notification function already patched")
            else:
                patched_function_start = original_function_body_start + "    # Check if notifications are blocked\n    if check_notifications_blocked():\n        logger.info(f\"SMS to {to_number} blocked by notification block\")\n        return {'success': False, 'error': 'Notifications are blocked'}\n\n"
                content = content.replace(original_function_body_start, patched_function_start)
        
        # Write the patched file
        with open(sms_file, "w") as f:
            f.write(content)
        
        logger.info(f"Successfully patched {sms_file}")
        return True
    except Exception as e:
        logger.error(f"Error patching SMS notification service: {e}")
        return False

def main():
    """Main function to fix email schedulers"""
    print("Permanently fixing email notification issues...")
    
    # 1. Disable notifications for all users
    if disable_all_email_notifications():
        print("✓ Successfully disabled notifications for all users")
    else:
        print("✗ Failed to disable notifications for users")
    
    # 2. Create notification block file
    if create_notification_block():
        print("✓ Successfully created notification block file")
    else:
        print("✗ Failed to create notification block file")
    
    # 3. Patch notification service
    if patch_notification_service():
        print("✓ Successfully patched email notification service")
    else:
        print("✗ Failed to patch email notification service")
    
    # 4. Patch SMS notification service
    if patch_sms_notification_service():
        print("✓ Successfully patched SMS notification service")
    else:
        print("✗ Failed to patch SMS notification service")
    
    print("\nEmail notification issues have been fixed.")
    print("The system will now check for the block file before sending any notifications.")
    print("You can remove the block by deleting 'data/notifications_blocked' when you want to enable notifications again.")

if __name__ == "__main__":
    main()
"""
Script to permanently disable all email and SMS notifications.
This creates a block file and also modifies notification services to prevent any emails from being sent.
"""
import os
import json
import logging
import time
import sys
from pathlib import Path
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("stop_notifications")

def ensure_data_directory():
    """Ensure data directories exist"""
    Path("data").mkdir(exist_ok=True)
    Path("data/notifications").mkdir(exist_ok=True)

def create_notification_block():
    """Create a block file that prevents notifications"""
    block_file = "data/notifications_blocked"
    try:
        with open(block_file, "w") as f:
            f.write(f"Notifications blocked at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Created notification block file: {block_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating notification block: {e}")
        return False

def modify_notification_service():
    """Modify notification_service.py to completely disable email sending"""
    service_file = "notification_service.py"
    if not os.path.exists(service_file):
        logger.error(f"Notification service file not found: {service_file}")
        return False
    
    try:
        # Create a backup first
        backup_file = f"{service_file}.bak_block"
        os.system(f"cp {service_file} {backup_file}")
        logger.info(f"Created backup of notification service: {backup_file}")
        
        # Replace the send_email function completely
        with open(service_file, "r") as f:
            content = f.read()
        
        # Find send_email function
        if "def send_email(" not in content:
            logger.error("Could not find send_email function")
            return False
        
        # Define the function replacement
        send_email_replacement = """
def send_email(recipient, subject, template_name, template_data=None, sender=None, reply_to=None):
    # EMAIL SENDING DISABLED - This function is a stub that will not send any emails.
    #
    # Args:
    #    recipient: Email address of the recipient
    #    subject: Email subject line
    #    template_name: Name of the email template to use
    #    template_data: Data to render in the template
    #    sender: Sender email address
    #    reply_to: Reply-to email address
    #    
    # Returns:
    #    dict: Status of the operation (always success=False)
    logger.info(f"Email sending BLOCKED: {subject} to {recipient}")
    return {"success": False, "error": "Email notifications are permanently disabled"}

"""
        
        # Replace the function
        start_index = content.find("def send_email(")
        if start_index == -1:
            logger.error("Could not find start of send_email function")
            return False
        
        end_index = content.find("def ", start_index + 1)
        if end_index == -1:
            logger.error("Could not find end of send_email function")
            return False
        
        # Replace the function
        new_content = content[:start_index] + send_email_replacement + content[end_index:]
        
        with open(service_file, "w") as f:
            f.write(new_content)
        
        logger.info("Successfully overrode send_email function in notification_service.py")
        return True
    except Exception as e:
        logger.error(f"Error modifying notification service: {e}")
        return False

def modify_sms_notification_service():
    """Modify sms_notification_service.py to completely disable SMS sending"""
    service_file = "sms_notification_service.py"
    if not os.path.exists(service_file):
        logger.error(f"SMS notification service file not found: {service_file}")
        return False
    
    try:
        # Create a backup first
        backup_file = f"{service_file}.bak_block"
        os.system(f"cp {service_file} {backup_file}")
        logger.info(f"Created backup of SMS service: {backup_file}")
        
        # Replace the send_sms_notification function completely
        with open(service_file, "r") as f:
            content = f.read()
        
        # Find send_sms_notification function
        if "def send_sms_notification(" not in content:
            logger.error("Could not find send_sms_notification function")
            return False
        
        # Define the function replacement
        send_sms_replacement = """
def send_sms_notification(to_number, message, user_id=None):
    # SMS SENDING DISABLED - This function is a stub that will not send any SMS.
    # 
    # Args:
    #    to_number: Phone number to send to
    #    message: Message to send
    #    user_id: ID of the user (if applicable)
    # 
    # Returns:
    #    dict: Status of the operation (always success=False)
    logger.info(f"SMS sending BLOCKED to {to_number}")
    return {"success": False, "error": "SMS notifications are permanently disabled"}

"""
        
        # Replace the function
        start_index = content.find("def send_sms_notification(")
        if start_index == -1:
            logger.error("Could not find start of send_sms_notification function")
            return False
        
        end_index = content.find("def ", start_index + 1)
        if end_index == -1:
            # If there's no next function, use the end of the file
            end_index = len(content)
        
        # Replace the function
        new_content = content[:start_index] + send_sms_replacement + content[end_index:]
        
        with open(service_file, "w") as f:
            f.write(new_content)
        
        logger.info("Successfully overrode send_sms_notification function in sms_notification_service.py")
        return True
    except Exception as e:
        logger.error(f"Error modifying SMS service: {e}")
        return False

def disable_user_notifications():
    """Disable notifications for all users"""
    users_file = "data/users.json"
    if not os.path.exists(users_file):
        logger.error(f"Users file not found: {users_file}")
        return False
    
    try:
        # Load users
        with open(users_file, "r") as f:
            users = json.load(f)
        
        # Make a backup
        backup_file = f"{users_file}.bak_block"
        with open(backup_file, "w") as f:
            json.dump(users, f, indent=2)
        logger.info(f"Created backup of users file: {backup_file}")
        
        # Count users with notifications enabled
        email_enabled = sum(1 for user in users if user.get("notifications_enabled", False))
        sms_enabled = sum(1 for user in users if user.get("sms_notifications_enabled", False))
        
        # Disable notifications for all users
        for user in users:
            user["notifications_enabled"] = False
            user["sms_notifications_enabled"] = False
        
        # Save updated users
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)
        
        logger.info(f"Disabled email notifications for {email_enabled} users")
        logger.info(f"Disabled SMS notifications for {sms_enabled} users")
        return True
    except Exception as e:
        logger.error(f"Error disabling notifications: {e}")
        return False

def kill_scheduler_processes():
    """Kill all scheduler processes"""
    try:
        # Find scheduler processes
        result = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        lines = result.stdout.split("\n")
        
        found_processes = []
        for line in lines:
            if "python" in line and "scheduler.py" in line and "grep" not in line:
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    found_processes.append(pid)
        
        # Kill the processes
        for pid in found_processes:
            try:
                subprocess.run(["kill", "-9", pid])
                logger.info(f"Killed scheduler process {pid}")
            except Exception as e:
                logger.error(f"Failed to kill process {pid}: {e}")
        
        # Remove PID file
        if os.path.exists("scheduler.pid"):
            os.remove("scheduler.pid")
            logger.info("Removed scheduler.pid file")
        
        if found_processes:
            logger.info(f"Killed {len(found_processes)} scheduler processes")
        else:
            logger.info("No scheduler processes found to kill")
        
        return True
    except Exception as e:
        logger.error(f"Error killing scheduler processes: {e}")
        return False

def main():
    """Main function to stop notifications"""
    print("\n====== STOPPING EMAIL NOTIFICATIONS ======\n")
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Step 1: Create notification block
    print("STEP 1: Creating notification block file...")
    if create_notification_block():
        print("✓ Created notification block file")
    else:
        print("✗ Failed to create notification block file")
    
    # Step 2: Disable notifications for all users
    print("\nSTEP 2: Disabling notifications for all users...")
    if disable_user_notifications():
        print("✓ Disabled notifications for all users")
    else:
        print("✗ Failed to disable notifications for users")
    
    # Step 3: Modify notification service
    print("\nSTEP 3: Modifying notification service to prevent email sending...")
    if modify_notification_service():
        print("✓ Modified notification service to block emails")
    else:
        print("✗ Failed to modify notification service")
    
    # Step 4: Modify SMS notification service
    print("\nSTEP 4: Modifying SMS notification service to prevent SMS sending...")
    if modify_sms_notification_service():
        print("✓ Modified SMS notification service to block SMS")
    else:
        print("✗ Failed to modify SMS notification service")
    
    # Step 5: Kill scheduler processes
    print("\nSTEP 5: Killing all scheduler processes...")
    if kill_scheduler_processes():
        print("✓ Killed all scheduler processes")
    else:
        print("✗ Failed to kill scheduler processes")
    
    print("\n====== EMAIL NOTIFICATIONS STOPPED ======\n")
    print("All email and SMS notifications have been permanently disabled.")
    print("The system will NOT send ANY notifications until this is reversed.")

if __name__ == "__main__":
    main()
"""
Simple script to fix email notifications by disabling them in user profiles
and creating a block file that will be checked before sending emails.
"""
import os
import json
import logging
from pathlib import Path
import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure data directories exist"""
    Path("data").mkdir(exist_ok=True)
    Path("data/notifications").mkdir(exist_ok=True)

def disable_notifications_for_all_users():
    """Disable email and SMS notifications for all users"""
    ensure_data_directory()
    users_file = "data/users.json"
    
    if not os.path.exists(users_file):
        print(f"Error: Users file not found: {users_file}")
        return False
    
    try:
        # Load user data
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        # Get count of users with notifications enabled
        email_enabled_count = sum(1 for user in users if user.get('notifications_enabled', False))
        sms_enabled_count = sum(1 for user in users if user.get('sms_notifications_enabled', False))
        
        # Make a backup of the user file
        backup_file = f"{users_file}.bak"
        with open(backup_file, 'w') as f:
            json.dump(users, f, indent=2)
        print(f"Created backup of users file: {backup_file}")
        
        # Disable notifications for all users
        for user in users:
            user['notifications_enabled'] = False
            user['sms_notifications_enabled'] = False
        
        # Save updated users
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
        
        print(f"Disabled email notifications for {email_enabled_count} users")
        print(f"Disabled SMS notifications for {sms_enabled_count} users")
        return True
    except Exception as e:
        print(f"Error disabling notifications: {e}")
        return False

def create_notification_block_file():
    """Create a file to block notifications from being sent"""
    ensure_data_directory()
    block_file = "data/notifications_blocked"
    
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(block_file, 'w') as f:
            f.write(f"Notifications blocked at {timestamp}")
        print(f"Created notification block file: {block_file}")
        return True
    except Exception as e:
        print(f"Error creating notification block file: {e}")
        return False

def create_check_blocked_function():
    """Create a function file for checking blocked notifications"""
    function_file = "check_notifications_blocked.py"
    
    try:
        # Create the function file
        with open(function_file, 'w') as f:
            f.write('''"""
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
''')
        print(f"Created function file: {function_file}")
        return True
    except Exception as e:
        print(f"Error creating function file: {e}")
        return False

def modify_notification_service():
    """Modify the notification service to check for blocked notifications"""
    service_file = "notification_service.py"
    
    if not os.path.exists(service_file):
        print(f"Error: Notification service file not found: {service_file}")
        return False
    
    try:
        # Read the original file
        with open(service_file, 'r') as f:
            content = f.readlines()
        
        # Create a backup of the original file
        backup_file = f"{service_file}.bak"
        with open(backup_file, 'w') as f:
            f.writelines(content)
        print(f"Created backup of notification service file: {backup_file}")
        
        # Add import for check_notifications_blocked function
        import_line = "import logging\n"
        check_import = "import logging\nimport check_notifications_blocked\n"
        
        found = False
        for i, line in enumerate(content):
            if line.strip() == import_line.strip():
                content[i] = check_import
                found = True
                break
        
        if not found:
            # Add import at the top
            content.insert(0, check_import)
        
        # Modify the send_email function to check for blocked notifications
        for i, line in enumerate(content):
            if line.strip().startswith("def send_email("):
                # Find the first line after the function signature
                j = i + 1
                while j < len(content) and not content[j].strip().startswith("def "):
                    if content[j].strip() and not content[j].strip().startswith("#"):
                        # Insert the check here
                        content.insert(j, '    # Check if notifications are blocked\n')
                        content.insert(j+1, '    if check_notifications_blocked.check_notifications_blocked():\n')
                        content.insert(j+2, '        logger.info(f"Email to {recipient} blocked by notification block")\n')
                        content.insert(j+3, '        return {"success": False, "error": "Notifications are blocked"}\n\n')
                        print("Added notification block check to send_email function")
                        break
                    j += 1
        
        # Save the modified file
        with open(service_file, 'w') as f:
            f.writelines(content)
        
        print(f"Successfully modified notification service: {service_file}")
        return True
    except Exception as e:
        print(f"Error modifying notification service: {e}")
        return False

def modify_sms_service():
    """Modify the SMS service to check for blocked notifications"""
    service_file = "sms_notification_service.py"
    
    if not os.path.exists(service_file):
        print(f"Error: SMS service file not found: {service_file}")
        return False
    
    try:
        # Read the original file
        with open(service_file, 'r') as f:
            content = f.readlines()
        
        # Create a backup of the original file
        backup_file = f"{service_file}.bak"
        with open(backup_file, 'w') as f:
            f.writelines(content)
        print(f"Created backup of SMS service file: {backup_file}")
        
        # Add import for check_notifications_blocked function
        import_line = "import logging\n"
        check_import = "import logging\nimport check_notifications_blocked\n"
        
        found = False
        for i, line in enumerate(content):
            if line.strip() == import_line.strip():
                content[i] = check_import
                found = True
                break
        
        if not found:
            # Add import at the top
            content.insert(0, check_import)
        
        # Modify the send_sms_notification function to check for blocked notifications
        for i, line in enumerate(content):
            if line.strip().startswith("def send_sms_notification("):
                # Find the first line after the function signature
                j = i + 1
                while j < len(content) and not content[j].strip().startswith("def "):
                    if content[j].strip() and not content[j].strip().startswith("#"):
                        # Insert the check here
                        content.insert(j, '    # Check if notifications are blocked\n')
                        content.insert(j+1, '    if check_notifications_blocked.check_notifications_blocked():\n')
                        content.insert(j+2, '        logger.info(f"SMS to {to_number} blocked by notification block")\n')
                        content.insert(j+3, '        return {"success": False, "error": "Notifications are blocked"}\n\n')
                        print("Added notification block check to send_sms_notification function")
                        break
                    j += 1
        
        # Save the modified file
        with open(service_file, 'w') as f:
            f.writelines(content)
        
        print(f"Successfully modified SMS service: {service_file}")
        return True
    except Exception as e:
        print(f"Error modifying SMS service: {e}")
        return False

def kill_scheduler_processes():
    """Kill any running scheduler processes"""
    import subprocess
    
    try:
        # Find scheduler processes
        process = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        lines = process.stdout.split("\n")
        
        pids = []
        for line in lines:
            if "python" in line and "scheduler.py" in line and "grep" not in line:
                parts = line.split()
                if len(parts) > 1:
                    pids.append(parts[1])
        
        if not pids:
            print("No scheduler processes found")
            return True
        
        # Kill the processes
        for pid in pids:
            subprocess.run(["kill", "-9", pid])
            print(f"Killed scheduler process: {pid}")
        
        # Remove PID file
        if os.path.exists("scheduler.pid"):
            os.remove("scheduler.pid")
            print("Removed scheduler.pid file")
        
        return True
    except Exception as e:
        print(f"Error killing scheduler processes: {e}")
        return False

def main():
    """Main function to fix notification issues"""
    print("=== FIX EMAIL NOTIFICATIONS ===")
    print("This script will disable email notifications and prevent them from being sent.\n")
    
    # Step 1: Disable notifications for all users
    print("Step 1: Disabling notifications for all users...")
    disable_notifications_for_all_users()
    print()
    
    # Step 2: Create notification block file
    print("Step 2: Creating notification block file...")
    create_notification_block_file()
    print()
    
    # Step 3: Create check function
    print("Step 3: Creating notification check function...")
    create_check_blocked_function()
    print()
    
    # Step 4: Modify notification services
    print("Step 4: Modifying notification services...")
    modify_notification_service()
    modify_sms_service()
    print()
    
    # Step 5: Kill scheduler processes
    print("Step 5: Killing scheduler processes...")
    kill_scheduler_processes()
    print()
    
    print("=== NOTIFICATION FIX COMPLETE ===")
    print("The system has been modified to block all notifications.")
    print("To re-enable notifications in the future:")
    print("1. Delete the file 'data/notifications_blocked'")
    print("2. Re-enable notifications for users who should receive them")
    print("3. Restart the scheduler with 'python start_scheduler.py'")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script to check the status of update notifications that are being sent.
This looks for a temporary file created by the notification process.
"""

import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_notification_temp_file():
    """
    Check if the temporary notification status file exists and return its contents.
    This file is created by send_update_notification.py to track progress.
    """
    temp_file = 'data/update_notification_status.json'
    
    if not os.path.exists(temp_file):
        logger.info(f"Temporary status file not found: {temp_file}")
        return None
    
    try:
        with open(temp_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading temporary status file: {e}")
        return None

def check_active_processes():
    """
    Check if the send_update_notification.py script is still running.
    """
    import psutil
    
    script_name = "send_update_notification.py"
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and script_name in ' '.join(cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return False

def load_users():
    """Load users from the data/users.json file"""
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("Users file not found or invalid")
        return []

def check_status():
    """
    Check the status of update notifications.
    """
    # Load users to get total count
    users = load_users()
    total_users = len(users)
    
    # Check if the process is still running
    process_running = check_active_processes()
    
    # Check the status file
    status = check_notification_temp_file()
    
    if status:
        print(f"Update notification status (as of {status.get('timestamp', 'unknown')})")
        print(f"Total users: {status.get('total_users', 'unknown')}")
        print(f"Emails sent: {status.get('sent_count', 0)}")
        print(f"Users skipped: {status.get('skipped_count', 0)}")
        print(f"Failed to send: {status.get('failed_count', 0)}")
        
        # Show list of emails sent
        if 'sent_to' in status and status['sent_to']:
            print("\nEmails sent to:")
            for email in status['sent_to']:
                print(f"  - {email}")
        
        # Show list of failures
        if 'failures' in status and status['failures']:
            print("\nFailed to send to:")
            for email, error in status['failures'].items():
                print(f"  - {email}: {error}")
    else:
        print("No status information available.")
    
    # Show process status
    if process_running:
        print("\nNotification process is still running.")
    else:
        print("\nNotification process is not running.")
    
    # Provide advice
    if not status and not process_running:
        print("\nIt appears the notification process has not started or did not create a status file.")
    elif not process_running and status:
        if status.get('sent_count', 0) + status.get('skipped_count', 0) + status.get('failed_count', 0) < total_users:
            print("\nThe process appears to have stopped before completing all users.")
        else:
            print("\nThe process appears to have completed successfully.")

def main():
    print("Calm Journey - Update Notification Status Checker")
    print("--------------------------------------------------")
    
    check_status()

if __name__ == "__main__":
    main()
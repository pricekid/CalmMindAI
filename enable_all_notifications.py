#!/usr/bin/env python3
"""
Script to enable notifications for all users in the system.
This updates user preferences in the data/users.json file.
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

def ensure_data_directory():
    """Ensure the data directory exists"""
    os.makedirs('data', exist_ok=True)

def load_users():
    """Load users from the data/users.json file"""
    ensure_data_directory()
    
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("Users file not found or invalid, creating empty list")
        return []

def save_users(users):
    """Save users to the data/users.json file"""
    ensure_data_directory()
    
    with open('data/users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    logger.info(f"Saved {len(users)} users to data/users.json")

def enable_notifications_for_all():
    """
    Enable notifications for all users in the system.
    
    Returns:
        dict: Statistics about the update process
    """
    # Load users
    users = load_users()
    logger.info(f"Loaded {len(users)} users")
    
    # Track statistics
    stats = {
        'total_users': len(users),
        'updated_count': 0,
        'already_enabled': 0
    }
    
    # Update each user
    for user in users:
        # Check if notifications_enabled exists and is False
        if user.get('notifications_enabled', False) == False:
            user['notifications_enabled'] = True
            stats['updated_count'] += 1
            logger.info(f"Enabled notifications for user {user['id']} ({user['email']})")
        else:
            # User already has notifications enabled
            # Ensure the field exists
            user['notifications_enabled'] = True
            stats['already_enabled'] += 1
            logger.info(f"User {user['id']} ({user['email']}) already has notifications enabled")
    
    # Save updated users
    save_users(users)
    
    return stats

def main():
    print("Calm Journey - Enable Notifications for All Users")
    print("--------------------------------------------------")
    
    # Update users
    print("\nEnabling notifications for all users...")
    stats = enable_notifications_for_all()
    
    # Print stats
    print("\nUpdate complete!")
    print(f"Total users: {stats['total_users']}")
    print(f"Users updated: {stats['updated_count']}")
    print(f"Users already enabled: {stats['already_enabled']}")

if __name__ == "__main__":
    main()
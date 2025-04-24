"""
Script to list user IDs for direct login access.
"""
import os
import json
import sys
from pathlib import Path

# Path to users.json file
USERS_FILE = Path("data/users.json")

def list_users():
    """List users and their IDs"""
    if not USERS_FILE.exists():
        print(f"Users file not found: {USERS_FILE}")
        return

    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            
        print(f"Found {len(users)} users:")
        print("-" * 60)
        print(f"{'ID':<5} {'Email':<30} {'Name':<20}")
        print("-" * 60)
        
        for user in users:
            user_id = user.get('id', 'N/A')
            email = user.get('email', 'N/A')
            name = user.get('name', 'Unknown')
            print(f"{user_id:<5} {email:<30} {name:<20}")
            
        print("\nTo login directly, use URL: /simple-login/<user_id>")
        print("For example: /simple-login/1")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    list_users()
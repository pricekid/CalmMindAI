#!/usr/bin/env python3
"""
Fix missing password hashes for existing users.
This script identifies users with missing password hashes and provides a solution.
"""

from app import create_app
from models import User, db
from werkzeug.security import generate_password_hash
import logging

def fix_missing_password_hashes():
    """Fix users with missing password hashes by setting a temporary password"""
    app = create_app()
    with app.app_context():
        # Find users with missing password hashes
        users_no_hash = User.query.filter(
            (User.password_hash == None) | (User.password_hash == '')
        ).all()
        
        print(f"Found {len(users_no_hash)} users with missing password hashes")
        
        for user in users_no_hash:
            # Set a temporary password that they'll need to reset
            temp_password = f"temp_{user.username}_2025"
            user.set_password(temp_password)
            print(f"Set temporary password for user: {user.username}")
        
        # Commit all changes
        db.session.commit()
        print(f"Updated {len(users_no_hash)} users with temporary passwords")
        print("Users will need to use password reset to set their actual passwords")
        
        return len(users_no_hash)

if __name__ == "__main__":
    fix_missing_password_hashes()
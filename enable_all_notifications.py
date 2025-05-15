"""
Script to enable notifications for all users by default.
This ensures everyone receives journal reminders unless they manually turn them off.
"""
import os
import sys
from datetime import datetime, time

def enable_notifications_for_all_users():
    """Enable notifications for all users in the system."""
    try:
        from app import app, db
        from models import User
        
        with app.app_context():
            # Find all users with notifications disabled
            disabled_users = User.query.filter_by(notifications_enabled=False).all()
            disabled_count = len(disabled_users)
            
            # Find all users with morning reminders disabled
            morning_disabled = User.query.filter_by(morning_reminder_enabled=False).all()
            morning_disabled_count = len(morning_disabled)
            
            # Find all users with evening reminders disabled
            evening_disabled = User.query.filter_by(evening_reminder_enabled=False).all()
            evening_disabled_count = len(evening_disabled)
            
            print(f"Found {disabled_count} users with notifications disabled")
            print(f"Found {morning_disabled_count} users with morning reminders disabled")
            print(f"Found {evening_disabled_count} users with evening reminders disabled")
            
            # Update all users with notifications disabled
            for user in disabled_users:
                user.notifications_enabled = True
                print(f"Enabling notifications for user: {user.username or user.email}")
            
            # Update all users with morning reminders disabled
            for user in morning_disabled:
                user.morning_reminder_enabled = True
                print(f"Enabling morning reminders for user: {user.username or user.email}")
                
                # Set default morning reminder time if not set
                if not user.morning_reminder_time:
                    user.morning_reminder_time = time(8, 0)  # 8:00 AM
            
            # Update all users with evening reminders disabled
            for user in evening_disabled:
                user.evening_reminder_enabled = True
                print(f"Enabling evening reminders for user: {user.username or user.email}")
                
                # Set default evening reminder time if not set
                if not user.evening_reminder_time:
                    user.evening_reminder_time = time(20, 0)  # 8:00 PM
            
            # Commit changes to database
            db.session.commit()
            
            print("\nNotifications have been enabled for all users!")
            print("Users can still manually disable notifications in their settings.")
            
    except Exception as e:
        print(f"Error enabling notifications: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    enable_notifications_for_all_users()
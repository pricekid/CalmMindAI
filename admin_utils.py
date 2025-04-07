import json
import os
from datetime import datetime, timedelta
from models import User, JournalEntry, CBTRecommendation
from app import db
from flask_login import current_user

# File paths
DATA_DIR = 'data'
ADMIN_DIR = os.path.join(DATA_DIR, 'admin')
JOURNALS_FILE = os.path.join(DATA_DIR, 'journals.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
FLAGGED_FILE = os.path.join(DATA_DIR, 'flagged.json')
ADMIN_MESSAGES_FILE = os.path.join(DATA_DIR, 'admin_messages.json')
CONFIG_FILE = os.path.join(ADMIN_DIR, 'config.json')
TWILIO_CONFIG_FILE = os.path.join(ADMIN_DIR, 'twilio_config.json')

# Set up logging
import logging
logger = logging.getLogger(__name__)

def ensure_data_files_exist():
    """Ensure all data files exist with valid JSON"""
    # Create data directories
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(ADMIN_DIR, exist_ok=True)
    
    for file_path in [JOURNALS_FILE, USERS_FILE, FLAGGED_FILE, ADMIN_MESSAGES_FILE]:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)

    # Handle config files separately since they're dicts not lists
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                "openai_api_key": "",
                "max_tokens": 800,
                "model": "gpt-4o"
            }, f, indent=2)
            
    # Handle Twilio config file
    os.makedirs(os.path.dirname(TWILIO_CONFIG_FILE), exist_ok=True)
    if not os.path.exists(TWILIO_CONFIG_FILE):
        with open(TWILIO_CONFIG_FILE, 'w') as f:
            json.dump({
                "account_sid": "",
                "auth_token": "",
                "phone_number": ""
            }, f, indent=2)

def get_admin_stats():
    """Get statistics for the admin dashboard"""
    # Get real user count
    total_users = User.query.count()
    
    # Get real journal count
    total_journals = JournalEntry.query.count()
    
    # Mock daily active users (would normally come from session data)
    daily_active = min(10, total_users)
    
    # Get journal entries per day (last 7 days)
    current_date = datetime.utcnow()
    seven_days_ago = current_date - timedelta(days=7)
    
    entries_by_day = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day, 0, 0, 0)
        day_end = datetime(day.year, day.month, day.day, 23, 59, 59)
        
        count = JournalEntry.query.filter(
            JournalEntry.created_at >= day_start,
            JournalEntry.created_at <= day_end
        ).count()
        
        entries_by_day.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Count users with SMS notifications enabled
    sms_enabled_users = User.query.filter_by(sms_notifications_enabled=True).count()
    
    # Count users with email notifications enabled
    email_enabled_users = User.query.filter_by(notifications_enabled=True).count()
    
    # Mock top anxiety themes (would normally use NLP or tags)
    anxiety_themes = [
        {'theme': 'Work Stress', 'count': 12},
        {'theme': 'Social Anxiety', 'count': 8},
        {'theme': 'Health Concerns', 'count': 6}
    ]
    
    return {
        'total_users': total_users,
        'total_journals': total_journals,
        'daily_active_users': daily_active,
        'entries_by_day': entries_by_day,
        'anxiety_themes': anxiety_themes,
        'sms_enabled_users': sms_enabled_users,
        'email_enabled_users': email_enabled_users
    }

def export_journal_entries():
    """Export journal entries to journals.json"""
    entries = JournalEntry.query.all()
    
    exported_entries = []
    for entry in entries:
        # Get CBT recommendations for this entry
        recommendations = CBTRecommendation.query.filter_by(journal_entry_id=entry.id).all()
        recommendation_data = []
        
        for rec in recommendations:
            recommendation_data.append({
                'thought_pattern': rec.thought_pattern,
                'recommendation': rec.recommendation
            })
            
        # Format the entry
        entry_data = {
            'id': entry.id,
            'user_id': entry.user_id,
            'title': entry.title,
            'content': entry.content,
            'anxiety_level': entry.anxiety_level,
            'created_at': entry.created_at.isoformat(),
            'updated_at': entry.updated_at.isoformat(),
            'is_analyzed': entry.is_analyzed,
            'recommendations': recommendation_data
        }
        
        exported_entries.append(entry_data)
    
    # Save to the JSON file
    with open(JOURNALS_FILE, 'w') as f:
        json.dump(exported_entries, f, indent=2)
    
    return exported_entries

def export_users():
    """Export users to users.json"""
    users = User.query.all()
    
    exported_users = []
    for user in users:
        # Count user's journal entries
        entry_count = JournalEntry.query.filter_by(user_id=user.id).count()
        
        # Format the user
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'entry_count': entry_count
        }
        
        exported_users.append(user_data)
    
    # Save to the JSON file
    with open(USERS_FILE, 'w') as f:
        json.dump(exported_users, f, indent=2)
    
    return exported_users

def flag_journal_entry(journal_id, reason):
    """Flag a journal entry as having incorrect AI analysis"""
    # Load existing flagged entries
    flagged_entries = []
    if os.path.exists(FLAGGED_FILE):
        with open(FLAGGED_FILE, 'r') as f:
            try:
                flagged_entries = json.load(f)
            except json.JSONDecodeError:
                flagged_entries = []
    
    # Check if this entry is already flagged
    for entry in flagged_entries:
        if entry.get('journal_id') == journal_id:
            # Update the reason
            entry['reason'] = reason
            entry['updated_at'] = datetime.utcnow().isoformat()
            
            # Save the updated list
            with open(FLAGGED_FILE, 'w') as f:
                json.dump(flagged_entries, f, indent=2)
            
            return entry
    
    # Add new flagged entry
    new_flag = {
        'journal_id': journal_id,
        'reason': reason,
        'admin_id': current_user.id,
        'created_at': datetime.utcnow().isoformat()
    }
    
    flagged_entries.append(new_flag)
    
    # Save the updated list
    with open(FLAGGED_FILE, 'w') as f:
        json.dump(flagged_entries, f, indent=2)
    
    return new_flag

def is_entry_flagged(journal_id):
    """Check if a journal entry is flagged"""
    if os.path.exists(FLAGGED_FILE):
        with open(FLAGGED_FILE, 'r') as f:
            try:
                flagged_entries = json.load(f)
                for entry in flagged_entries:
                    if entry.get('journal_id') == journal_id:
                        return True
            except json.JSONDecodeError:
                pass
    
    return False

def get_flagged_entries():
    """Get all flagged journal entries"""
    flagged_entries = []
    if os.path.exists(FLAGGED_FILE):
        with open(FLAGGED_FILE, 'r') as f:
            try:
                flagged_entries = json.load(f)
            except json.JSONDecodeError:
                pass
    
    return flagged_entries

def save_admin_message(user_id, journal_id, message):
    """Save an admin message to a user about a journal entry"""
    # Load existing messages
    admin_messages = []
    if os.path.exists(ADMIN_MESSAGES_FILE):
        with open(ADMIN_MESSAGES_FILE, 'r') as f:
            try:
                admin_messages = json.load(f)
            except json.JSONDecodeError:
                admin_messages = []
    
    # Add new message
    new_message = {
        'id': len(admin_messages) + 1,
        'user_id': user_id,
        'journal_id': journal_id,
        'message': message,
        'admin_id': current_user.id,
        'created_at': datetime.utcnow().isoformat(),
        'is_read': False
    }
    
    admin_messages.append(new_message)
    
    # Save the updated list
    with open(ADMIN_MESSAGES_FILE, 'w') as f:
        json.dump(admin_messages, f, indent=2)
    
    return new_message

def get_admin_messages(user_id=None):
    """Get admin messages, optionally filtered by user_id"""
    admin_messages = []
    if os.path.exists(ADMIN_MESSAGES_FILE):
        with open(ADMIN_MESSAGES_FILE, 'r') as f:
            try:
                admin_messages = json.load(f)
                if user_id:
                    admin_messages = [m for m in admin_messages if m.get('user_id') == user_id]
            except json.JSONDecodeError:
                pass
    
    return admin_messages

def get_config():
    """Get API configuration"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    
    # Default config
    return {
        "openai_api_key": "",
        "max_tokens": 800,
        "model": "gpt-4o"
    }

def save_config(config):
    """Save API configuration"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config

def save_twilio_config(account_sid, auth_token, phone_number):
    """Save Twilio configuration to a file"""
    os.makedirs(os.path.dirname(TWILIO_CONFIG_FILE), exist_ok=True)
    
    config = {
        "account_sid": account_sid,
        "auth_token": auth_token,
        "phone_number": phone_number
    }
    
    try:
        with open(TWILIO_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving Twilio config: {str(e)}")
        return False

def load_twilio_config():
    """Load Twilio configuration from file"""
    if not os.path.exists(TWILIO_CONFIG_FILE):
        return {
            "account_sid": "",
            "auth_token": "",
            "phone_number": ""
        }
    
    try:
        with open(TWILIO_CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading Twilio config: {str(e)}")
        return {
            "account_sid": "",
            "auth_token": "",
            "phone_number": ""
        }
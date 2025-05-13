#!/usr/bin/env python3
"""
Restore database to April 29th state.

This script imports user and journal entry data from the April 30th backups,
but filters to include only data from April 29th or earlier.
"""

import os
import json
import logging
import uuid
from datetime import datetime, time, timedelta

from app import app, db
from models import User, JournalEntry, CBTRecommendation

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Directory for storing ID mappings
ID_MAPPING_DIR = 'data'
ID_MAPPING_FILE = os.path.join(ID_MAPPING_DIR, 'id_mapping.json')

# Target date cutoff - end of April 29th
TARGET_DATE = datetime(2025, 4, 29, 23, 59, 59)

def ensure_id_mapping_dir():
    """Ensure the ID mapping directory exists"""
    if not os.path.exists(ID_MAPPING_DIR):
        os.makedirs(ID_MAPPING_DIR)
        logger.info(f"Created directory: {ID_MAPPING_DIR}")

def load_id_mapping():
    """Load ID mapping from file"""
    if os.path.exists(ID_MAPPING_FILE):
        with open(ID_MAPPING_FILE, 'r') as f:
            mapping = json.load(f)
        logger.info(f"Loaded ID mapping for {len(mapping)} users")
        return mapping
    return {}

def save_id_mapping(id_mapping):
    """Save ID mapping to file"""
    ensure_id_mapping_dir()
    with open(ID_MAPPING_FILE, 'w') as f:
        json.dump(id_mapping, f, indent=2)
    logger.info(f"Saved ID mapping for {len(id_mapping)} users")

def load_users_from_backup(cutoff_date=TARGET_DATE):
    """
    Load users from April 30th backup, filtering for those created on or before the cutoff date.
    """
    backup_file = 'data/users.json.bak'
    if not os.path.exists(backup_file):
        logger.error(f"Backup file not found: {backup_file}")
        return []
    
    with open(backup_file, 'r') as f:
        all_users = json.load(f)
    
    # Filter users created on or before the cutoff date
    users = []
    for user in all_users:
        created_at = datetime.fromisoformat(user['created_at'])
        if created_at <= cutoff_date:
            users.append(user)
    
    logger.info(f"Loaded {len(users)} users from backup (from {len(all_users)} total)")
    return users

def load_journals_from_backup(cutoff_date=TARGET_DATE):
    """
    Load journal entries from all available backups, filtering for those created on or before the cutoff date.
    """
    journals_dir = 'data/journals'
    all_journals = []
    filtered_journals = []
    
    if not os.path.exists(journals_dir):
        logger.error(f"Journals directory not found: {journals_dir}")
        return []
    
    # Find all user journal backups
    backup_files = [f for f in os.listdir(journals_dir) if f.endswith('.bak')]
    logger.info(f"Found {len(backup_files)} journal backup files")
    
    for backup_file in backup_files:
        file_path = os.path.join(journals_dir, backup_file)
        try:
            with open(file_path, 'r') as f:
                journals = json.load(f)
                all_journals.extend(journals)
        except Exception as e:
            logger.error(f"Error loading {backup_file}: {e}")
    
    # Filter journals created on or before the cutoff date
    for journal in all_journals:
        created_at = datetime.fromisoformat(journal['created_at'])
        if created_at <= cutoff_date:
            filtered_journals.append(journal)
    
    logger.info(f"Loaded {len(filtered_journals)} journals from {len(all_journals)} total")
    return filtered_journals

def delete_all_data():
    """Delete all data in the database to prepare for import"""
    with app.app_context():
        logger.info("Deleting all existing data")
        
        # Create backups before deletion
        try:
            # Backup CBT recommendations
            current_cbts = CBTRecommendation.query.all()
            backup_data = []
            for cbt in current_cbts:
                cbt_dict = {c.name: getattr(cbt, c.name) for c in cbt.__table__.columns}
                # Convert datetime objects to strings
                for key, value in cbt_dict.items():
                    if isinstance(value, datetime):
                        cbt_dict[key] = value.isoformat()
                    elif isinstance(value, time):
                        cbt_dict[key] = value.isoformat()
                backup_data.append(cbt_dict)
            
            # Save CBT backup
            backup_path = f'backup_data/cbt_recommendations_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            logger.info(f"Created backup of current CBT recommendations at {backup_path}")
            
            # Backup journals
            current_journals = JournalEntry.query.all()
            backup_data = []
            for journal in current_journals:
                journal_dict = {c.name: getattr(journal, c.name) for c in journal.__table__.columns}
                # Convert datetime objects to strings
                for key, value in journal_dict.items():
                    if isinstance(value, datetime):
                        journal_dict[key] = value.isoformat()
                    elif isinstance(value, time):
                        journal_dict[key] = value.isoformat()
                backup_data.append(journal_dict)
            
            # Save journal backup
            backup_path = f'backup_data/journals_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            logger.info(f"Created backup of current journals at {backup_path}")
            
            # Backup users
            current_users = User.query.all()
            backup_data = []
            for user in current_users:
                user_dict = {c.name: getattr(user, c.name) for c in user.__table__.columns}
                # Convert datetime objects to strings
                for key, value in user_dict.items():
                    if isinstance(value, datetime):
                        user_dict[key] = value.isoformat()
                    elif isinstance(value, time):
                        user_dict[key] = value.isoformat()
                backup_data.append(user_dict)
            
            # Save user backup
            backup_path = f'backup_data/users_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            logger.info(f"Created backup of current users at {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backups: {e}")
        
        # Delete data in correct order to respect foreign keys
        try:
            # First delete all CBT recommendations
            cbt_count = CBTRecommendation.query.count()
            db.session.query(CBTRecommendation).delete()
            db.session.commit()
            logger.info(f"Deleted {cbt_count} CBT recommendations")
            
            # Then delete all journal entries
            journal_count = JournalEntry.query.count()
            db.session.query(JournalEntry).delete()
            db.session.commit()
            logger.info(f"Deleted {journal_count} journal entries")
            
            # Finally delete all users
            user_count = User.query.count()
            db.session.query(User).delete()
            db.session.commit()
            logger.info(f"Deleted {user_count} users")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting data: {e}")
            db.session.rollback()
            return False

def import_users_from_backup():
    """Import users from backup"""
    users = load_users_from_backup()
    id_mapping = load_id_mapping()
    
    # Import users
    with app.app_context():
        
        # Import users from backup
        for user_data in users:
            old_id = str(user_data['id'])
            
            # Create new UUID if not already mapped
            if old_id not in id_mapping:
                id_mapping[old_id] = str(uuid.uuid4())
            
            new_id = id_mapping[old_id]
            
            # Create user with mapped UUID
            new_user = User()
            new_user.id = new_id
            new_user.username = user_data.get('username')
            new_user.email = user_data.get('email')
            new_user.created_at = datetime.fromisoformat(user_data.get('created_at'))
            new_user.notifications_enabled = user_data.get('notifications_enabled', False)
            new_user.sms_notifications_enabled = user_data.get('sms_notifications_enabled', False)
            
            db.session.add(new_user)
        
        db.session.commit()
        logger.info(f"Imported {len(users)} users")
        
        # Save updated ID mapping
        save_id_mapping(id_mapping)

def import_journals_from_backup():
    """Import journal entries from backup"""
    journals = load_journals_from_backup()
    id_mapping = load_id_mapping()
    
    # Import journals
    with app.app_context():
        
        # Import journals from backup
        for journal_data in journals:
            old_user_id = str(journal_data['user_id'])
            
            # Skip if user ID not mapped
            if old_user_id not in id_mapping:
                logger.warning(f"Skipping journal for unmapped user ID: {old_user_id}")
                continue
            
            new_user_id = id_mapping[old_user_id]
            
            # Create journal entry with mapped user UUID
            new_journal = JournalEntry()
            new_journal.id = journal_data.get('id')
            new_journal.user_id = new_user_id
            new_journal.title = journal_data.get('title', 'Untitled Entry')  # Handle missing title
            new_journal.content = journal_data.get('content', '')
            new_journal.created_at = datetime.fromisoformat(journal_data.get('created_at'))
            new_journal.updated_at = datetime.fromisoformat(journal_data.get('updated_at', journal_data.get('created_at')))
            new_journal.anxiety_level = 5  # Default value
            # Handle field name changes
            new_journal.initial_insight = journal_data.get('feedback', journal_data.get('analysis', None))
            
            db.session.add(new_journal)
        
        db.session.commit()
        logger.info(f"Imported {len(journals)} journals")

def main():
    """Main function to restore database to April 29th state"""
    logger.info("Starting April 29th database restoration")
    
    # First delete all existing data
    if not delete_all_data():
        logger.error("Failed to delete existing data, aborting restoration")
        return
    
    # Import users first to establish ID mapping
    import_users_from_backup()
    
    # Import journals using the ID mapping
    import_journals_from_backup()
    
    logger.info("April 29th database restoration complete")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Restore database to April 30th state.

This script imports user and journal entry data from the April 30th backups.
It handles the migration from integer IDs to UUID strings for users.
"""

import os
import json
import logging
import uuid
from datetime import datetime

from app import app, db
from models import User, JournalEntry

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Directory for storing ID mappings
ID_MAPPING_DIR = 'data'
ID_MAPPING_FILE = os.path.join(ID_MAPPING_DIR, 'id_mapping.json')

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

def load_users_from_backup():
    """Load users from April 30th backup"""
    backup_file = 'data/users.json.bak'
    if not os.path.exists(backup_file):
        logger.error(f"Backup file not found: {backup_file}")
        return []
    
    with open(backup_file, 'r') as f:
        users = json.load(f)
    
    logger.info(f"Loaded {len(users)} users from backup")
    return users

def load_journals_from_backup():
    """Load journal entries from all available April 30th backups"""
    journals_dir = 'data/journals'
    all_journals = []
    
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
                logger.info(f"Loaded {len(journals)} journals from {backup_file}")
        except Exception as e:
            logger.error(f"Error loading {backup_file}: {e}")
    
    return all_journals

def import_users_from_backup():
    """Import users from April 30th backup"""
    users = load_users_from_backup()
    id_mapping = load_id_mapping()
    
    # Clear existing users if needed
    with app.app_context():
        existing_count = User.query.count()
        logger.info(f"Current user count in database: {existing_count}")
        
        if input(f"This will replace {existing_count} existing users with {len(users)} users from backup. Continue? (y/n): ").lower() != 'y':
            logger.info("User import canceled")
            return
        
        # Delete existing users
        db.session.query(User).delete()
        db.session.commit()
        logger.info("Deleted existing users")
        
        # Import users from backup
        for user_data in users:
            old_id = str(user_data['id'])
            
            # Create new UUID if not already mapped
            if old_id not in id_mapping:
                id_mapping[old_id] = str(uuid.uuid4())
            
            new_id = id_mapping[old_id]
            
            # Create user with mapped UUID
            new_user = User(
                id=new_id,
                username=user_data.get('username'),
                email=user_data.get('email'),
                created_at=datetime.fromisoformat(user_data.get('created_at')),
                notifications_enabled=user_data.get('notifications_enabled', False),
                sms_notifications_enabled=user_data.get('sms_notifications_enabled', False)
            )
            
            db.session.add(new_user)
        
        db.session.commit()
        logger.info(f"Imported {len(users)} users")
        
        # Save updated ID mapping
        save_id_mapping(id_mapping)

def import_journals_from_backup():
    """Import journal entries from April 30th backup"""
    journals = load_journals_from_backup()
    id_mapping = load_id_mapping()
    
    # Clear existing journals if needed
    with app.app_context():
        existing_count = JournalEntry.query.count()
        logger.info(f"Current journal count in database: {existing_count}")
        
        if input(f"This will replace {existing_count} existing journals with {len(journals)} journals from backup. Continue? (y/n): ").lower() != 'y':
            logger.info("Journal import canceled")
            return
        
        # Delete existing journals
        db.session.query(JournalEntry).delete()
        db.session.commit()
        logger.info("Deleted existing journals")
        
        # Import journals from backup
        for journal_data in journals:
            old_user_id = str(journal_data['user_id'])
            
            # Skip if user ID not mapped
            if old_user_id not in id_mapping:
                logger.warning(f"Skipping journal for unmapped user ID: {old_user_id}")
                continue
            
            new_user_id = id_mapping[old_user_id]
            
            # Create journal entry with mapped user UUID
            new_journal = JournalEntry(
                id=journal_data.get('id'),
                user_id=new_user_id,
                title=journal_data.get('title', 'Untitled Entry'),  # Handle missing title
                content=journal_data.get('content', ''),
                created_at=datetime.fromisoformat(journal_data.get('created_at')),
                updated_at=datetime.fromisoformat(journal_data.get('updated_at', journal_data.get('created_at'))),
                anxiety_level=5,  # Default value
                initial_insight=journal_data.get('feedback', journal_data.get('analysis', None))  # Handle field name changes
            )
            
            db.session.add(new_journal)
        
        db.session.commit()
        logger.info(f"Imported {len(journals)} journals")

def main():
    """Main function to restore database to April 30th state"""
    logger.info("Starting April 30th database restoration")
    
    # Import users first to establish ID mapping
    import_users_from_backup()
    
    # Import journals using the ID mapping
    import_journals_from_backup()
    
    logger.info("April 30th database restoration complete")

if __name__ == "__main__":
    main()
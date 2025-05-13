#!/usr/bin/env python3
"""
Data recovery script for Calm Journey application.
Recovers journal entries from various backup sources into the PostgreSQL database.
"""
import json
import os
import sys
import logging
import uuid
from datetime import datetime, timezone
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('journal_recovery')

# Constants
DATA_DIR = os.path.join('.', 'data')
JOURNALS_DIR = os.path.join(DATA_DIR, 'journals')
BACKUP_DIR = os.path.join('.', 'backup_data')

# Setup working directory
os.makedirs(BACKUP_DIR, exist_ok=True)

# Attempt to import Flask app and models
FLASK_AVAILABLE = False
try:
    from app import app, db
    from models import User, JournalEntry, CBTRecommendation
    FLASK_AVAILABLE = True
    logger.info("Flask app imported successfully")
except ImportError as e:
    logger.warning(f"Could not import Flask app: {e}. Will operate in export-only mode.")

# Global tracking variables
USER_ENTRY_COUNTS = defaultdict(int)
RECOVERED_ENTRIES = {}

def create_backup():
    """Create backup of existing data files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"data_backup_{timestamp}")
    
    try:
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
            
        # Copy key files
        files_to_backup = [
            "journals.json", 
            "users.json",
            "users.json.bak",
            "id_mapping.json"
        ]
        
        for filename in files_to_backup:
            src_path = os.path.join(DATA_DIR, filename)
            if os.path.exists(src_path):
                import shutil
                dst_path = os.path.join(backup_path, filename)
                shutil.copy2(src_path, dst_path)
                logger.info(f"Backed up {src_path} to {dst_path}")
                
        # Also back up journals directory
        if os.path.exists(JOURNALS_DIR):
            journal_backup_path = os.path.join(backup_path, "journals")
            os.makedirs(journal_backup_path, exist_ok=True)
            
            for journal_file in os.listdir(JOURNALS_DIR):
                src_path = os.path.join(JOURNALS_DIR, journal_file)
                if os.path.isfile(src_path):
                    dst_path = os.path.join(journal_backup_path, journal_file)
                    shutil.copy2(src_path, dst_path)
            
            logger.info(f"Backed up journal files to {journal_backup_path}")
            
        logger.info(f"Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None


def count_journal_entries():
    """Count journal entries in various sources"""
    counts = {
        "database": 0,
        "journals.json": 0,
        "user_journals": 0
    }
    
    # Count in database
    if FLASK_AVAILABLE:
        try:
            with app.app_context():
                counts["database"] = db.session.query(JournalEntry).count()
        except Exception as e:
            logger.error(f"Error counting database entries: {e}")
    
    # Count in journals.json
    journals_path = os.path.join(DATA_DIR, "journals.json")
    if os.path.exists(journals_path):
        try:
            with open(journals_path, 'r') as f:
                journals = json.load(f)
                counts["journals.json"] = len(journals)
        except Exception as e:
            logger.error(f"Error counting entries in journals.json: {e}")
    
    # Count in user journal files
    if os.path.exists(JOURNALS_DIR):
        total = 0
        for filename in os.listdir(JOURNALS_DIR):
            if filename.endswith('.json') and not filename.endswith('.bak'):
                try:
                    with open(os.path.join(JOURNALS_DIR, filename), 'r') as f:
                        entries = json.load(f)
                        file_count = len(entries)
                        total += file_count
                        logger.debug(f"Found {file_count} entries in {filename}")
                except Exception as e:
                    logger.error(f"Error counting entries in {filename}: {e}")
        counts["user_journals"] = total
    
    return counts


def get_id_mapping():
    """Get mapping from old integer IDs to new UUID strings"""
    id_mapping = {}
    id_mapping_file = os.path.join(DATA_DIR, "id_mapping.json")
    
    if os.path.exists(id_mapping_file):
        try:
            with open(id_mapping_file, 'r') as f:
                id_mapping = json.load(f)
                # Convert keys from strings to integers if needed
                id_mapping = {int(k) if k.isdigit() else k: v for k, v in id_mapping.items()}
                logger.info(f"Loaded {len(id_mapping)} ID mappings from {id_mapping_file}")
        except Exception as e:
            logger.error(f"Error loading ID mapping: {e}")
    
    if not id_mapping:
        # Try to rebuild mapping from users.json.bak
        users_bak_file = os.path.join(DATA_DIR, "users.json.bak")
        if os.path.exists(users_bak_file):
            try:
                with open(users_bak_file, 'r') as f:
                    legacy_users = json.load(f)
                
                # Try to match users by email
                if FLASK_AVAILABLE:
                    with app.app_context():
                        for legacy_user in legacy_users:
                            old_id = legacy_user.get('id')
                            email = legacy_user.get('email')
                            
                            if not email:
                                continue
                                
                            user = db.session.execute(
                                db.select(User).filter_by(email=email)
                            ).scalar_one_or_none()
                            
                            if user:
                                id_mapping[old_id] = user.id
                                # Track expected entry counts from backup
                                USER_ENTRY_COUNTS[old_id] = legacy_user.get('entry_count', 0)
                
                logger.info(f"Built {len(id_mapping)} ID mappings from users.json.bak")
                
                # Save for future use
                with open(id_mapping_file, 'w') as f:
                    json.dump(id_mapping, f, indent=2)
            except Exception as e:
                logger.error(f"Error building ID mapping from backup: {e}")
    
    return id_mapping


def extract_journals_from_file(file_path):
    """Extract journal entries from a file"""
    try:
        with open(file_path, 'r') as f:
            entries = json.load(f)
            logger.debug(f"Extracted {len(entries)} entries from {file_path}")
            return entries
    except Exception as e:
        logger.error(f"Error extracting journals from {file_path}: {e}")
        return []


def deduplicate_journals(journals):
    """Deduplicate journal entries based on content and creation time"""
    unique_journals = {}
    
    for entry in journals:
        # Skip entries without essential data
        if not entry.get('content'):
            continue
            
        # Generate a unique key based on content and creation time
        content = entry.get('content', '')
        created_at = entry.get('created_at', '')
        user_id = entry.get('user_id')
        
        # Convert integer user IDs to UUID strings using mapping
        if isinstance(user_id, int) and user_id in id_mapping:
            entry['user_id'] = id_mapping[user_id]
            
        # Skip entries with invalid user_id
        if not entry.get('user_id'):
            continue
            
        key = f"{user_id}_{content[:50]}_{created_at}"
        
        # Use the entry with more fields if duplicate exists
        if key in unique_journals:
            existing_entry = unique_journals[key]
            if len(entry) > len(existing_entry):
                unique_journals[key] = entry
        else:
            unique_journals[key] = entry
    
    logger.info(f"Deduplicated {len(journals)} entries to {len(unique_journals)} unique entries")
    return unique_journals


def normalize_field(entry, keys, default=''):
    """Get a field value from multiple possible keys"""
    for key in keys:
        if key in entry and entry[key]:
            return entry[key]
    return default


def import_journals_to_database(id_mapping, journals):
    """
    Import journal entries to database with proper field mapping
    Handles the conversion from legacy field names to current schema
    """
    if not FLASK_AVAILABLE:
        logger.error("Cannot import to database because Flask app is not available")
        return 0
        
    imported_count = 0
    
    with app.app_context():
        try:
            # Get existing entries to avoid duplicates
            existing_entries = {}
            
            for entry in db.session.execute(db.select(JournalEntry)).scalars():
                key = f"{entry.user_id}_{entry.content[:50]}_{entry.created_at.isoformat()}"
                existing_entries[key] = entry.id
                
            logger.info(f"Found {len(existing_entries)} existing entries in database")
            
            # Import entries
            for entry in journals:
                try:
                    # Convert integer user IDs to UUID strings using mapping
                    user_id = entry.get('user_id')
                    if isinstance(user_id, int):
                        if user_id in id_mapping:
                            user_id = id_mapping[user_id]
                        else:
                            logger.warning(f"No mapping for user ID {user_id}, skipping entry")
                            continue
                            
                    # Check if user exists
                    user = db.session.execute(
                        db.select(User).filter_by(id=user_id)
                    ).scalar_one_or_none()
                    
                    if not user:
                        logger.warning(f"User {user_id} not found, skipping entry")
                        continue
                        
                    # Generate key for deduplication
                    content = entry.get('content', '')
                    created_at_str = entry.get('created_at', '')
                    key = f"{user_id}_{content[:50]}_{created_at_str}"
                    
                    # Skip if already exists
                    if key in existing_entries:
                        logger.debug(f"Entry {key} already exists, skipping")
                        continue
                        
                    # Parse timestamps
                    if created_at_str:
                        try:
                            if 'Z' in created_at_str:
                                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            else:
                                created_at = datetime.fromisoformat(created_at_str)
                        except ValueError:
                            created_at = datetime.now(timezone.utc)
                    else:
                        created_at = datetime.now(timezone.utc)
                        
                    updated_at_str = entry.get('updated_at', created_at_str)
                    if updated_at_str:
                        try:
                            if 'Z' in updated_at_str:
                                updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                            else:
                                updated_at = datetime.fromisoformat(updated_at_str)
                        except ValueError:
                            updated_at = created_at
                    else:
                        updated_at = created_at
                        
                    # Map old field names to new schema
                    analysis = normalize_field(entry, ['initial_insight', 'analysis', 'gpt_response', 'feedback'])
                    user_reflection = normalize_field(entry, ['user_reflection', 'reflection'])
                    followup_insight = normalize_field(entry, ['followup_insight', 'followup'])
                    second_reflection = normalize_field(entry, ['second_reflection'])
                    closing_message = normalize_field(entry, ['closing_message'])
                    
                    # Create new entry
                    new_entry = JournalEntry(
                        user_id=user_id,
                        title=entry.get('title', 'Untitled Entry'),
                        content=content,
                        anxiety_level=entry.get('anxiety_level'),
                        created_at=created_at,
                        updated_at=updated_at,
                        is_analyzed=entry.get('is_analyzed', bool(analysis)),
                        initial_insight=analysis,
                        user_reflection=user_reflection,
                        followup_insight=followup_insight,
                        second_reflection=second_reflection,
                        closing_message=closing_message,
                        conversation_complete=entry.get('conversation_complete', 
                                                      bool(closing_message) or bool(second_reflection))
                    )
                    
                    db.session.add(new_entry)
                    
                    # Add CBT recommendations if present
                    recommendations = entry.get('recommendations', [])
                    for rec in recommendations:
                        if isinstance(rec, dict) and rec.get('thought_pattern') and rec.get('recommendation'):
                            cbt_rec = CBTRecommendation(
                                thought_pattern=rec['thought_pattern'],
                                recommendation=rec['recommendation'],
                                journal_entry=new_entry
                            )
                            db.session.add(cbt_rec)
                            
                    imported_count += 1
                    
                    # Commit every 10 entries
                    if imported_count % 10 == 0:
                        db.session.commit()
                        logger.info(f"Imported {imported_count} entries so far")
                        
                except Exception as e:
                    logger.error(f"Error importing entry: {e}")
                    continue
                    
            # Final commit
            db.session.commit()
            logger.info(f"Successfully imported {imported_count} journal entries")
            
        except Exception as e:
            logger.error(f"Error importing journals to database: {e}")
            db.session.rollback()
            
    return imported_count


def extract_all_journals():
    """Extract journal entries from all potential sources"""
    all_journals = []
    
    # 1. Extract from journals.json
    journals_path = os.path.join(DATA_DIR, "journals.json")
    if os.path.exists(journals_path):
        journals = extract_journals_from_file(journals_path)
        logger.info(f"Extracted {len(journals)} entries from journals.json")
        all_journals.extend(journals)
        
    # 2. Extract from user journal files
    if os.path.exists(JOURNALS_DIR):
        journal_files = [f for f in os.listdir(JOURNALS_DIR) 
                        if f.endswith('.json') and not f.endswith('.bak')]
        
        for filename in journal_files:
            file_path = os.path.join(JOURNALS_DIR, filename)
            entries = extract_journals_from_file(file_path)
            logger.info(f"Extracted {len(entries)} entries from {filename}")
            all_journals.extend(entries)
            
    # 3. Check backup files if needed
    return all_journals


def main():
    """Main recovery function"""
    logger.info("Starting journal recovery process")
    
    # Create backup before making any changes
    backup_path = create_backup()
    if not backup_path:
        logger.error("Failed to create backup, aborting recovery")
        return
        
    # Check initial journal counts
    initial_counts = count_journal_entries()
    logger.info(f"Initial journal counts: {initial_counts}")
    
    # Get user ID mapping
    global id_mapping
    id_mapping = get_id_mapping()
    logger.info(f"Loaded {len(id_mapping)} user ID mappings")
    
    # Extract and deduplicate journals
    all_journals = extract_all_journals()
    logger.info(f"Extracted {len(all_journals)} total journal entries from all sources")
    
    unique_journals = deduplicate_journals(all_journals)
    
    # Import to database if Flask is available
    if FLASK_AVAILABLE:
        imported_count = import_journals_to_database(id_mapping, list(unique_journals.values()))
        logger.info(f"Imported {imported_count} journal entries to database")
    else:
        logger.warning("Skipping database import because Flask app is not available")
    
    # Count final journal entries
    final_counts = count_journal_entries()
    
    logger.info("Journal recovery summary:")
    logger.info(f"Initial counts: {initial_counts}")
    logger.info(f"Final counts: {final_counts}")
    logger.info(f"Net change: {final_counts['database'] - initial_counts['database']} entries added to database")
    
    logger.info("Journal recovery process complete")


if __name__ == "__main__":
    main()
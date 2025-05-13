"""
Script to restore journal entries from any available backup sources.
This attempts to find and recover journal data from various potential locations.
"""

import os
import json
import logging
import sys
from datetime import datetime
import glob
import shutil
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app components (with error handling)
try:
    from app import app, db
    from models import User, JournalEntry, CBTRecommendation
    FLASK_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import Flask app: {e}")
    FLASK_AVAILABLE = False

# Define constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
JOURNALS_FILE = os.path.join(DATA_DIR, "journals.json")
BACKUP_DIR = os.path.join(DATA_DIR, "recovery_backup")
USER_ENTRY_COUNTS = {}

def ensure_backup_directory():
    """Create a backup directory for recovery purposes"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        logger.info(f"Created backup directory at {BACKUP_DIR}")

def backup_current_data():
    """Backup current journal data before attempting recovery"""
    ensure_backup_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup current journal.json
    if os.path.exists(JOURNALS_FILE):
        backup_file = os.path.join(BACKUP_DIR, f"journals_{timestamp}.json")
        shutil.copy2(JOURNALS_FILE, backup_file)
        logger.info(f"Backed up journals.json to {backup_file}")
    
    # Backup user journal files
    journal_dir = os.path.join(DATA_DIR, "journals")
    if os.path.exists(journal_dir):
        journal_backup_dir = os.path.join(BACKUP_DIR, f"journals_{timestamp}")
        os.makedirs(journal_backup_dir, exist_ok=True)
        
        for journal_file in glob.glob(os.path.join(journal_dir, "*.json")):
            if os.path.isfile(journal_file):
                shutil.copy2(journal_file, journal_backup_dir)
        
        logger.info(f"Backed up user journal files to {journal_backup_dir}")
    
    return True

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

def count_journal_entries():
    """Count all journal entries in various sources"""
    # Count entries in database
    db_count = 0
    if FLASK_AVAILABLE:
        with app.app_context():
            try:
                db_count = JournalEntry.query.count()
                logger.info(f"Found {db_count} journal entries in the database")
            except Exception as e:
                logger.error(f"Error counting database journal entries: {e}")
    
    # Count entries in journals.json
    json_count = 0
    if os.path.exists(JOURNALS_FILE):
        try:
            with open(JOURNALS_FILE, 'r') as f:
                journal_data = json.load(f)
                json_count = len(journal_data)
                logger.info(f"Found {json_count} journal entries in journals.json")
        except Exception as e:
            logger.error(f"Error counting JSON journal entries: {e}")
    
    # Count entries in user journal files
    user_file_count = 0
    journal_dir = os.path.join(DATA_DIR, "journals")
    if os.path.exists(journal_dir):
        try:
            for journal_file in glob.glob(os.path.join(journal_dir, "*.json")):
                if os.path.isfile(journal_file) and not journal_file.endswith(".bak"):
                    with open(journal_file, 'r') as f:
                        user_journals = json.load(f)
                        user_file_count += len(user_journals)
            logger.info(f"Found {user_file_count} journal entries in user journal files")
        except Exception as e:
            logger.error(f"Error counting user journal entries: {e}")
    
    # Count expected entries from user backups
    expected_count = sum(USER_ENTRY_COUNTS.values())
    logger.info(f"Expected {expected_count} journal entries based on user entry counts")
    
    return {
        "database": db_count,
        "json_file": json_count,
        "user_files": user_file_count,
        "expected": expected_count
    }

def find_all_journal_files():
    """Find all files that might contain journal data"""
    journal_files = []
    
    # Check main journals directory
    journal_dir = os.path.join(DATA_DIR, "journals")
    if os.path.exists(journal_dir):
        for file in glob.glob(os.path.join(journal_dir, "*.json*")):
            journal_files.append(file)
    
    # Check for any other potential journal data
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if "journal" in file.lower() and file.endswith((".json", ".bak", ".backup")):
                full_path = os.path.join(root, file)
                if full_path not in journal_files:
                    journal_files.append(full_path)
    
    logger.info(f"Found {len(journal_files)} potential journal data files")
    return journal_files

def extract_journals_from_file(file_path):
    """Extract journal entries from a file"""
    journals = []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
            # Check if it's directly a list of journal entries
            if isinstance(data, list) and len(data) > 0:
                # Check first item for expected journal fields
                first_item = data[0]
                if any(key in first_item for key in ('content', 'title', 'user_id')):
                    journals.extend(data)
                    logger.info(f"Extracted {len(data)} journal entries from {file_path}")
            
            # Check if it's a nested structure
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        # Check if this list contains journal entries
                        first_item = value[0]
                        if isinstance(first_item, dict) and any(k in first_item for k in ('content', 'title', 'user_id')):
                            journals.extend(value)
                            logger.info(f"Extracted {len(value)} journal entries from nested data in {file_path}")
    
    except Exception as e:
        logger.error(f"Error extracting journals from {file_path}: {e}")
    
    return journals

def import_journals_to_database(id_mapping, journals):
    """Import journal entries to database using the ID mapping"""
    if not FLASK_AVAILABLE:
        logger.error("Flask app not available, cannot import to database")
        return 0
    
    imported_count = 0
    
    with app.app_context():
        try:
            # Get existing journal entries by content to avoid duplicates
            existing_entries = set()
            for entry in JournalEntry.query.all():
                # Create a hash of user_id and content to identify duplicates
                entry_hash = f"{entry.user_id}:{entry.content[:100]}"
                existing_entries.add(entry_hash)
            
            logger.info(f"Found {len(existing_entries)} existing entries to avoid duplicates")
            
            for journal in journals:
                try:
                    # Handle both old integer IDs and new UUID format
                    user_id = journal.get('user_id')
                    if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
                        user_id = int(user_id)
                        if user_id not in id_mapping:
                            logger.warning(f"No mapping found for user ID {user_id}, skipping entry")
                            continue
                        new_user_id = id_mapping[user_id]
                    else:
                        # Already UUID format
                        new_user_id = user_id
                    
                    # Verify user exists
                    user = db.session.execute(db.select(User).filter_by(id=new_user_id)).scalar_one_or_none()
                    if not user:
                        logger.warning(f"User with ID {new_user_id} not found, skipping entry")
                        continue
                    
                    # Skip if no content
                    content = journal.get('content', '')
                    if not content:
                        logger.warning("Skipping entry with no content")
                        continue
                    
                    # Check for duplicates using our hash
                    entry_hash = f"{new_user_id}:{content[:100]}"
                    if entry_hash in existing_entries:
                        logger.info(f"Entry already exists for user {new_user_id}, skipping")
                        continue
                    
                    # Parse created_at timestamp
                    created_at = journal.get('created_at')
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except ValueError:
                            created_at = datetime.utcnow()
                    else:
                        created_at = datetime.utcnow()
                    
                    # Create new entry with appropriate field mappings
                    new_entry = JournalEntry()
                    new_entry.user_id = new_user_id
                    new_entry.title = journal.get('title', 'Untitled Entry')
                    new_entry.content = content
                    new_entry.created_at = created_at
                    new_entry.updated_at = created_at
                    new_entry.anxiety_level = journal.get('anxiety_level')
                    
                    # Map old fields to new schema
                    # Try all possible field names from different versions
                    analysis = journal.get('analysis', journal.get('gpt_response', journal.get('feedback', '')))
                    reflection = journal.get('reflection', journal.get('user_reflection', ''))
                    followup = journal.get('followup_insight', journal.get('followup', ''))
                    
                    new_entry.initial_insight = analysis
                    new_entry.followup_insight = followup
                    new_entry.user_reflection = reflection
                    new_entry.is_analyzed = bool(analysis)
                    new_entry.conversation_complete = bool(followup)
                    
                    db.session.add(new_entry)
                    db.session.flush()  # Get the ID without committing
                    
                    # Create CBT recommendation if available
                    if journal.get('thought_pattern') or journal.get('cbt_patterns'):
                        try:
                            # Handle different CBT pattern formats
                            if journal.get('thought_pattern'):
                                # Single pattern format
                                recommendation_text = ""
                                if journal.get('alternative_thought'):
                                    recommendation_text += f"Alternative thought: {journal.get('alternative_thought')}\n\n"
                                if journal.get('action_step'):
                                    recommendation_text += f"Action step: {journal.get('action_step')}"
                                    
                                rec = CBTRecommendation()
                                rec.journal_entry_id = new_entry.id
                                rec.thought_pattern = journal.get('thought_pattern', '')
                                rec.recommendation = recommendation_text or "Consider reframing this thought pattern."
                                
                                db.session.add(rec)
                            elif journal.get('cbt_patterns') and isinstance(journal.get('cbt_patterns'), list):
                                # Multiple patterns format
                                for pattern in journal.get('cbt_patterns'):
                                    if not isinstance(pattern, dict):
                                        continue
                                        
                                    rec = CBTRecommendation()
                                    rec.journal_entry_id = new_entry.id
                                    rec.thought_pattern = pattern.get('pattern', 'Unknown Pattern')
                                    rec.recommendation = pattern.get('description', 'No description provided')
                                    
                                    db.session.add(rec)
                        except Exception as rec_error:
                            logger.error(f"Error creating recommendation: {rec_error}")
                    
                    # Add to existing entries set to avoid duplicates
                    existing_entries.add(entry_hash)
                    imported_count += 1
                    
                    # Commit periodically
                    if imported_count % 5 == 0:
                        db.session.commit()
                        logger.info(f"Imported {imported_count} entries so far")
                        
                except Exception as entry_error:
                    logger.error(f"Error processing entry: {entry_error}")
                    db.session.rollback()
            
            # Final commit
            db.session.commit()
            logger.info(f"Successfully imported {imported_count} journal entries")
            
        except Exception as e:
            logger.error(f"Error importing journals to database: {e}")
            db.session.rollback()
    
    return imported_count

def main():
    """Main function to restore journal data"""
    logger.info("Starting journal recovery process")
    
    # Backup current data
    backup_current_data()
    
    # Get ID mapping
    id_mapping = get_id_mapping()
    if not id_mapping:
        logger.error("Failed to build user ID mapping, aborting")
        return
    
    # Count initial journal entries
    initial_counts = count_journal_entries()
    
    # Find all potential journal files
    journal_files = find_all_journal_files()
    
    # Extract and collect all journal entries
    all_journals = []
    for file_path in journal_files:
        journals = extract_journals_from_file(file_path)
        all_journals.extend(journals)
    
    logger.info(f"Found {len(all_journals)} total journal entries across all sources")
    
    # Remove duplicates based on content and user_id
    unique_journals = {}
    for journal in all_journals:
        user_id = journal.get('user_id')
        content = journal.get('content', '')
        if not content or not user_id:
            continue
            
        # Create a unique key for this journal
        key = f"{user_id}:{content[:100]}"
        
        # Keep the one with more fields filled in
        if key not in unique_journals or len(journal) > len(unique_journals[key]):
            unique_journals[key] = journal
    
    logger.info(f"Filtered to {len(unique_journals)} unique journal entries")
    
    # Import to database
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
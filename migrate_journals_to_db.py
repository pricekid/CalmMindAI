"""
Script to migrate journal entries from JSON files to the database.
This addresses the issue where users can't see their existing journal entries.
"""
import os
import json
from datetime import datetime
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app components
from app import app, db
from models import User, JournalEntry, CBTRecommendation

# Define constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
JOURNALS_FILE = os.path.join(DATA_DIR, "journals.json")

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def load_journals_from_json():
    """Load journal entries from the JSON file"""
    ensure_data_directory()
    
    if not os.path.exists(JOURNALS_FILE):
        logger.warning(f"Journal file {JOURNALS_FILE} does not exist. No journals to migrate.")
        return []
    
    try:
        with open(JOURNALS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {JOURNALS_FILE}")
        return []

def migrate_journals_to_db():
    """Migrate journal entries from JSON to the database"""
    with app.app_context():
        journals = load_journals_from_json()
        
        if not journals:
            logger.info("No journals found to migrate.")
            return
        
        logger.info(f"Found {len(journals)} journals to migrate.")
        
        # Get existing journal entries by ID
        existing_ids = {entry.id for entry in JournalEntry.query.all()}
        
        # Counter for statistics
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        for journal in journals:
            try:
                journal_id = journal.get('id')
                
                # Skip existing entries
                if journal_id in existing_ids:
                    logger.debug(f"Skipping existing journal ID {journal_id}")
                    skipped_count += 1
                    continue
                
                # Get the user (owner) of this journal
                user_id = journal.get('user_id')
                user = User.query.get(user_id)
                
                if not user:
                    logger.warning(f"User {user_id} not found for journal {journal_id}, skipping.")
                    skipped_count += 1
                    continue
                
                # Create new journal entry from JSON data
                entry = JournalEntry(
                    id=journal_id,
                    title=journal.get('title', 'Untitled Entry'),
                    content=journal.get('content', ''),
                    created_at=datetime.fromisoformat(journal.get('created_at')) if journal.get('created_at') else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(journal.get('updated_at')) if journal.get('updated_at') else datetime.utcnow(),
                    is_analyzed=journal.get('is_analyzed', False),
                    anxiety_level=journal.get('anxiety_level'),
                    initial_insight=journal.get('gpt_response'),
                    user_reflection=journal.get('user_reflection'),
                    user_id=user_id
                )
                
                # Add the entry
                db.session.add(entry)
                
                # Add any CBT recommendations if available
                cbt_patterns = journal.get('cbt_patterns', [])
                for pattern in cbt_patterns:
                    if not isinstance(pattern, dict):
                        continue
                        
                    recommendation = CBTRecommendation(
                        thought_pattern=pattern.get('pattern', 'Unknown Pattern'),
                        recommendation=pattern.get('description', 'No description provided'),
                        journal_entry=entry
                    )
                    db.session.add(recommendation)
                
                added_count += 1
                
                # Commit every 10 entries to avoid large transactions
                if added_count % 10 == 0:
                    db.session.commit()
                    logger.info(f"Committed {added_count} entries so far")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error migrating journal {journal.get('id')}: {str(e)}")
        
        # Final commit for any remaining entries
        db.session.commit()
        
        logger.info(f"Migration complete. Added: {added_count}, Skipped: {skipped_count}, Errors: {error_count}")
        
if __name__ == "__main__":
    migrate_journals_to_db()
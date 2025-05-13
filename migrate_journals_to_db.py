"""
Migrate journal entries from JSON files to database.
This script reads all user journal entries from JSON files and adds them to the database.
"""
import os
import json
import datetime
import logging
import sys
from app import app, db
from models import User, JournalEntry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_json_journal_files():
    """Find all user journal JSON files in the data directory"""
    journal_files = []
    journal_dir = "data/journals"
    
    if not os.path.exists(journal_dir):
        logging.warning(f"Journal directory {journal_dir} does not exist")
        return journal_files
    
    for filename in os.listdir(journal_dir):
        if filename.startswith("user_") and filename.endswith("_journals.json"):
            journal_files.append(os.path.join(journal_dir, filename))
    
    logging.info(f"Found {len(journal_files)} journal files")
    return journal_files

def migrate_journal_file(filepath):
    """Migrate a single journal file to the database"""
    # Extract user ID from filename (format: user_{user_id}_journals.json)
    filename = os.path.basename(filepath)
    user_id = filename.split("_")[1]
    
    logging.info(f"Processing journal file for user {user_id}")
    
    # Check if user exists in the database
    user = User.query.get(user_id)
    if not user:
        logging.warning(f"User {user_id} not found in database, skipping")
        return 0
    
    try:
        # Load journal entries from file
        with open(filepath, 'r') as f:
            journal_entries = json.load(f)
        
        logging.info(f"Found {len(journal_entries)} entries in file {filename}")
        imported_count = 0
        
        # Process each entry
        for entry in journal_entries:
            # Skip if entry doesn't have basic required fields
            if not all(key in entry for key in ['content', 'created_at']):
                logging.warning(f"Entry missing required fields, skipping: {entry}")
                continue
            
            # Check if this entry already exists in the database
            # Use content and timestamp to identify duplicates
            created_at = datetime.datetime.fromisoformat(entry.get('created_at'))
            existing_entry = JournalEntry.query.filter_by(
                user_id=user_id,
                content=entry.get('content'),
                created_at=created_at
            ).first()
            
            if existing_entry:
                logging.info(f"Entry already exists in database, skipping")
                continue
            
            # Create a new journal entry
            new_entry = JournalEntry(
                # Use title from entry or generate a default title
                title=entry.get('title', f"Journal Entry {datetime.datetime.now().strftime('%B %d, %Y')}"),
                content=entry.get('content'),
                user_id=user_id,
                # Convert anxiety level (mood) if present
                anxiety_level=entry.get('anxiety_level', 
                                        mood_to_anxiety_level(entry.get('mood', 'neutral'))),
                initial_insight=entry.get('feedback'),
                is_analyzed=bool(entry.get('feedback')),
                created_at=created_at,
                updated_at=datetime.datetime.fromisoformat(entry.get('updated_at', entry.get('created_at')))
            )
            
            db.session.add(new_entry)
            imported_count += 1
            
        # Commit all changes
        db.session.commit()
        logging.info(f"Imported {imported_count} entries for user {user_id}")
        return imported_count
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error migrating file {filepath}: {str(e)}")
        return 0

def mood_to_anxiety_level(mood):
    """Convert text mood to numeric anxiety level (1-10)"""
    mood_map = {
        'very_anxious': 9,
        'anxious': 7, 
        'neutral': 5,
        'calm': 3,
        'great': 1
    }
    return mood_map.get(mood.lower(), 5)  # Default to 5 (neutral) if mood not found

def migrate_all_journals():
    """Migrate all journal files to the database"""
    with app.app_context():
        journal_files = find_json_journal_files()
        total_imported = 0
        
        for filepath in journal_files:
            imported_count = migrate_journal_file(filepath)
            total_imported += imported_count
            
        logging.info(f"Migration complete. Total entries imported: {total_imported}")
        return total_imported

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--run':
        total_imported = migrate_all_journals()
        print(f"Migration complete. Total entries imported: {total_imported}")
    else:
        print("This script will migrate journal entries from JSON files to the database.")
        print("To run this script, use --run flag:")
        print("python migrate_journals_to_db.py --run")
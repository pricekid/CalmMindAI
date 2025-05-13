"""
Import legacy data from backup JSON files into current database schema.
This script handles the conversion from integer IDs to UUID strings.
"""
import json
import logging
import os
import uuid
from datetime import datetime
import sys

from app import app, db
from models import User, JournalEntry, CBTRecommendation

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def import_legacy_users():
    """Import users from the backup JSON file into the current database."""
    try:
        # Load backup data
        with open('data/users.json.bak', 'r') as f:
            legacy_users = json.load(f)
            
        logger.info(f"Found {len(legacy_users)} legacy users to import")
        
        # Map of old integer IDs to new UUID strings
        id_mapping = {}
        
        # Import users
        imported_count = 0
        for user_data in legacy_users:
            old_id = user_data.get('id')
            email = user_data.get('email')
            
            # Skip if no email (we need it for uniqueness)
            if not email:
                logger.warning(f"Skipping user with ID {old_id} - no email address")
                continue
                
            # Check if already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                logger.info(f"User with email {email} already exists with ID {existing_user.id}")
                id_mapping[old_id] = existing_user.id
                continue
            
            # Create new user with UUID
            new_uuid = str(uuid.uuid4())
            id_mapping[old_id] = new_uuid
            
            # Convert created_at to datetime if it's a string
            created_at = user_data.get('created_at')
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()
            
            new_user = User(
                id=new_uuid,
                username=user_data.get('username'),
                email=email,
                created_at=created_at,
                notifications_enabled=user_data.get('notifications_enabled', False),
                sms_notifications_enabled=user_data.get('sms_notifications_enabled', False)
            )
            
            db.session.add(new_user)
            imported_count += 1
            
            # Commit periodically to avoid large transactions
            if imported_count % 10 == 0:
                db.session.commit()
                logger.info(f"Imported {imported_count} users so far")
        
        # Final commit
        db.session.commit()
        logger.info(f"Successfully imported {imported_count} legacy users")
        
        # Save ID mapping for journal entries
        with open('data/id_mapping.json', 'w') as f:
            json.dump(id_mapping, f, indent=2)
            
        return id_mapping
        
    except Exception as e:
        logger.error(f"Error importing legacy users: {e}")
        db.session.rollback()
        return {}

def import_legacy_journals(id_mapping):
    """Import journal entries using the ID mapping from users."""
    try:
        # Find all journal files
        journal_dir = 'data/journals'
        journal_files = [f for f in os.listdir(journal_dir) if f.endswith('.json') and not f.endswith('.bak')]
        
        total_imported = 0
        
        for filename in journal_files:
            try:
                # Extract user ID from filename (both old integer and new UUID formats)
                if filename.startswith('user_') and '_journals.json' in filename:
                    user_id_part = filename.replace('user_', '').replace('_journals.json', '')
                    
                    # Handle both old integer IDs and new UUID format
                    if user_id_part.isdigit():
                        old_user_id = int(user_id_part)
                        if old_user_id not in id_mapping:
                            logger.warning(f"No mapping found for user ID {old_user_id}, skipping file {filename}")
                            continue
                        new_user_id = id_mapping[old_user_id]
                    else:
                        # Already in UUID format
                        new_user_id = user_id_part
                    
                    # Find the user
                    user = User.query.get(new_user_id)
                    if not user:
                        logger.warning(f"User with ID {new_user_id} not found, skipping file {filename}")
                        continue
                    
                    # Load journal entries
                    with open(os.path.join(journal_dir, filename), 'r') as f:
                        journal_data = json.load(f)
                    
                    imported_for_user = 0
                    # Import each entry
                    for entry in journal_data:
                        # Skip if already exists (check by title and content to avoid duplicates)
                        title = entry.get('title', '')
                        content = entry.get('content', '')
                        if not content:
                            continue
                            
                        # Check for existing entry
                        existing = JournalEntry.query.filter_by(
                            user_id=new_user_id,
                            title=title,
                            content=content
                        ).first()
                        
                        if existing:
                            logger.debug(f"Journal entry already exists for user {new_user_id}: {title}")
                            continue
                        
                        # Parse the created_at timestamp
                        created_at = entry.get('created_at')
                        if isinstance(created_at, str):
                            try:
                                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            except ValueError:
                                created_at = datetime.utcnow()
                        else:
                            created_at = datetime.utcnow()
                        
                        # Create new entry with mapped field names
                        new_entry = JournalEntry(
                            user_id=new_user_id,
                            title=entry.get('title', ''),
                            content=entry.get('content', ''),
                            created_at=created_at,
                            anxiety_level=entry.get('anxiety_level'),
                            # Map old field names to new schema
                            initial_insight=entry.get('analysis', ''),
                            followup_insight=entry.get('reflection', ''),
                            user_reflection=entry.get('user_reflection', ''),
                            # Set reasonable defaults for new fields
                            is_analyzed=True if entry.get('analysis') else False,
                            conversation_complete=True if entry.get('reflection') else False
                        )
                        
                        db.session.add(new_entry)
                        imported_for_user += 1
                        
                        # Create CBT recommendation if available
                        if 'thought_pattern' in entry and entry['thought_pattern']:
                            # Combine old alternative thought and action step to match new schema
                            recommendation_text = ""
                            if entry.get('alternative_thought'):
                                recommendation_text += f"Alternative thought: {entry.get('alternative_thought', '')}\n\n"
                            if entry.get('action_step'):
                                recommendation_text += f"Action step: {entry.get('action_step', '')}"
                                
                            recommendation = CBTRecommendation(
                                journal_entry_id=new_entry.id,
                                thought_pattern=entry.get('thought_pattern', ''),
                                recommendation=recommendation_text or "Consider reframing this thought pattern."
                            )
                            db.session.add(recommendation)
                    
                    # Commit after each file
                    db.session.commit()
                    logger.info(f"Imported {imported_for_user} journal entries for user {new_user_id}")
                    total_imported += imported_for_user
                    
            except Exception as file_error:
                logger.error(f"Error processing journal file {filename}: {file_error}")
                db.session.rollback()
        
        logger.info(f"Successfully imported {total_imported} journal entries in total")
        return total_imported
        
    except Exception as e:
        logger.error(f"Error importing legacy journals: {e}")
        db.session.rollback()
        return 0

def main():
    """Main function to run the import."""
    logger.info("Starting legacy data import")
    
    # Import in the correct order
    with app.app_context():
        # First import users
        logger.info("Importing legacy users")
        id_mapping = import_legacy_users()
        
        if not id_mapping:
            logger.error("Failed to import users, aborting")
            sys.exit(1)
        
        # Then import journal entries
        logger.info("Importing legacy journal entries")
        import_legacy_journals(id_mapping)
        
    logger.info("Legacy data import complete")

if __name__ == "__main__":
    main()
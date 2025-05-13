"""
Import legacy journal entries from backup files into the current database schema.
"""
import json
import logging
import os
from datetime import datetime
import sys

from app import app, db
from models import User, JournalEntry, CBTRecommendation

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_id_mapping():
    """Get the mapping from old integer IDs to new UUID strings."""
    try:
        # Check if we already have an ID mapping file
        if os.path.exists('data/id_mapping.json'):
            with open('data/id_mapping.json', 'r') as f:
                id_mapping = json.load(f)
                # Convert keys from strings to integers
                return {int(k): v for k, v in id_mapping.items()}
        
        # If not, build a mapping based on email addresses
        id_mapping = {}
        with open('data/users.json.bak', 'r') as f:
            legacy_users = json.load(f)
            
        for user_data in legacy_users:
            old_id = user_data.get('id')
            email = user_data.get('email')
            
            if not email:
                continue
                
            # Find user by email
            user = db.session.execute(
                db.select(User).filter_by(email=email)
            ).scalar_one_or_none()
            
            if user:
                id_mapping[old_id] = user.id
        
        # Save for future use
        with open('data/id_mapping.json', 'w') as f:
            json.dump(id_mapping, f, indent=2)
            
        return id_mapping
        
    except Exception as e:
        logger.error(f"Error building ID mapping: {e}")
        return {}

def import_journals(id_mapping):
    """Import journal entries using the ID mapping from users."""
    try:
        # Find all journal files
        journal_dir = 'data/journals'
        journal_files = [f for f in os.listdir(journal_dir) 
                        if f.endswith('.json') and not f.endswith('.bak')]
        
        logger.info(f"Found {len(journal_files)} journal files to process")
        total_imported = 0
        
        for filename in journal_files:
            try:
                # Extract user ID from filename (both old integer and new UUID formats)
                if filename.startswith('user_') and '_journals.json' in filename:
                    file_path = os.path.join(journal_dir, filename)
                    user_id_part = filename.replace('user_', '').replace('_journals.json', '')
                    
                    # Handle both old integer IDs and new UUID format
                    if user_id_part.isdigit():
                        old_user_id = int(user_id_part)
                        if old_user_id not in id_mapping:
                            logger.warning(f"No mapping found for user ID {old_user_id}, skipping {filename}")
                            continue
                        new_user_id = id_mapping[old_user_id]
                    else:
                        # Already in UUID format
                        new_user_id = user_id_part
                    
                    # Verify user exists
                    user = db.session.execute(
                        db.select(User).filter_by(id=new_user_id)
                    ).scalar_one_or_none()
                    
                    if not user:
                        logger.warning(f"User with ID {new_user_id} not found, skipping {filename}")
                        continue
                    
                    # Load journal entries
                    with open(file_path, 'r') as f:
                        try:
                            journal_data = json.load(f)
                            logger.info(f"Loaded {len(journal_data)} entries from {filename}")
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in {filename}")
                            continue
                    
                    # Process each entry
                    imported_for_user = 0
                    for entry in journal_data:
                        try:
                            # Skip if no content
                            content = entry.get('content', '')
                            if not content:
                                logger.warning("Skipping entry with no content")
                                continue
                                
                            # Check for duplicates based on content and user
                            existing = db.session.execute(
                                db.select(JournalEntry).filter_by(
                                    user_id=new_user_id,
                                    content=content
                                )
                            ).scalar_one_or_none()
                            
                            if existing:
                                logger.info(f"Entry already exists for user {new_user_id}, skipping")
                                continue
                            
                            # Parse created_at timestamp
                            created_at = entry.get('created_at')
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
                            new_entry.title = entry.get('title', 'Untitled Entry')
                            new_entry.content = content
                            new_entry.created_at = created_at
                            new_entry.updated_at = created_at
                            new_entry.anxiety_level = entry.get('anxiety_level')
                            
                            # Map old fields to new schema
                            analysis = entry.get('analysis', '')
                            reflection = entry.get('reflection', '')
                            user_reflection = entry.get('user_reflection', '')
                            
                            new_entry.initial_insight = analysis
                            new_entry.followup_insight = reflection
                            new_entry.user_reflection = user_reflection
                            new_entry.is_analyzed = bool(analysis)
                            new_entry.conversation_complete = bool(reflection)
                            
                            db.session.add(new_entry)
                            db.session.flush()  # Get the ID without committing
                            
                            # Create CBT recommendation if available
                            if entry.get('thought_pattern'):
                                try:
                                    # Combine old fields to match new schema
                                    recommendation_text = ""
                                    if entry.get('alternative_thought'):
                                        recommendation_text += f"Alternative thought: {entry.get('alternative_thought')}\n\n"
                                    if entry.get('action_step'):
                                        recommendation_text += f"Action step: {entry.get('action_step')}"
                                        
                                    rec = CBTRecommendation()
                                    rec.journal_entry_id = new_entry.id
                                    rec.thought_pattern = entry.get('thought_pattern', '')
                                    rec.recommendation = recommendation_text or "Consider reframing this thought pattern."
                                    
                                    db.session.add(rec)
                                except Exception as rec_error:
                                    logger.error(f"Error creating recommendation: {rec_error}")
                            
                            imported_for_user += 1
                            
                            # Commit periodically
                            if imported_for_user % 10 == 0:
                                db.session.commit()
                                logger.info(f"Imported {imported_for_user} entries for user {new_user_id}")
                                
                        except Exception as entry_error:
                            logger.error(f"Error processing entry: {entry_error}")
                            db.session.rollback()
                    
                    # Final commit for this user
                    db.session.commit()
                    logger.info(f"Completed import of {imported_for_user} entries for user {new_user_id}")
                    total_imported += imported_for_user
                
            except Exception as file_error:
                logger.error(f"Error processing journal file {filename}: {file_error}")
                db.session.rollback()
        
        logger.info(f"Total journal entries imported: {total_imported}")
        return total_imported
        
    except Exception as e:
        logger.error(f"Error in journal import process: {e}")
        db.session.rollback()
        return 0

def main():
    """Main function to run the import."""
    logger.info("Starting journal import process")
    
    with app.app_context():
        # Get ID mapping
        id_mapping = get_id_mapping()
        
        if not id_mapping:
            logger.error("Failed to build user ID mapping, aborting")
            sys.exit(1)
        
        # Import journal entries
        import_journals(id_mapping)
        
    logger.info("Journal import process complete")

if __name__ == "__main__":
    main()
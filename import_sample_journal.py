"""
Import a single sample journal entry to verify schema compatibility.
"""
import logging
from app import app, db
from models import JournalEntry, CBTRecommendation
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def import_sample_journal():
    """Import a single sample journal entry with the new schema."""
    try:
        with app.app_context():
            # Use a known user ID from the database
            user_id = None
            
            # Find a user ID
            users = db.session.execute(db.select(db.text("id")).select_from(db.text("\"user\"")).limit(1)).fetchone()
            if users:
                user_id = users[0]
                logger.info(f"Found user ID: {user_id}")
            else:
                logger.error("No users found in database")
                return False
                
            # Create a sample journal entry with the new schema fields
            new_entry = JournalEntry()
            new_entry.user_id = user_id
            new_entry.title = "Sample Test Entry"
            new_entry.content = "This is a test entry to verify schema compatibility."
            new_entry.created_at = datetime.utcnow()
            new_entry.anxiety_level = 5
            new_entry.initial_insight = "Sample initial insight about this journal entry."
            new_entry.user_reflection = "User's reflection on the insight."
            new_entry.followup_insight = "Follow-up insight based on user reflection."
            new_entry.is_analyzed = True
            new_entry.conversation_complete = True
            
            db.session.add(new_entry)
            db.session.flush()  # Get the ID without committing
            
            logger.info(f"Created journal entry with ID: {new_entry.id}")
            
            # Create a recommendation
            recommendation = CBTRecommendation()
            recommendation.journal_entry_id = new_entry.id
            recommendation.thought_pattern = "Catastrophizing"
            recommendation.recommendation = "Try to challenge this thought by considering more realistic outcomes."
            recommendation.created_at = datetime.utcnow()
            
            db.session.add(recommendation)
            db.session.commit()
            
            logger.info("Successfully created sample journal entry and recommendation")
            return True
    except Exception as e:
        logger.error(f"Error creating sample journal entry: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    import_sample_journal()
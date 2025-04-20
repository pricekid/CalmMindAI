"""
Script to add the user_reflection column to the journal_entry table.
This is needed for the reflective pause feature.
"""
import os
import logging
from app import app, db
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_user_reflection_column():
    """Add the user_reflection column to the journal_entry table if it doesn't exist"""
    try:
        with app.app_context():
            # Check if the column exists already
            conn = db.engine.connect()
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='journal_entry' AND column_name='user_reflection'
            """))
            
            # If the column doesn't exist, add it
            if result.rowcount == 0:
                logger.info("Adding user_reflection column to journal_entry table...")
                conn.execute(text("""
                    ALTER TABLE journal_entry 
                    ADD COLUMN user_reflection TEXT
                """))
                logger.info("Column added successfully.")
            else:
                logger.info("user_reflection column already exists in journal_entry table.")
            
            conn.close()
            
    except Exception as e:
        logger.error(f"Error adding user_reflection column: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting migration to add user_reflection column...")
    add_user_reflection_column()
    logger.info("Migration completed.")
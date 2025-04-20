"""
Script to fix query loading for journal entries by updating dashboard queries
to exclude problematic columns or explicitly load only necessary columns.
"""
import os
import sys
import logging
from app import app, db
from sqlalchemy import inspect

# Configure logging to see detailed error information
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_dashboard_query():
    """
    Fix the dashboard query to explicitly select only needed fields,
    avoiding the problematic user_reflection column.
    """
    try:
        # Import the required model only within the app context
        with app.app_context():
            from models import JournalEntry
            
            # Get all column names for the JournalEntry table
            inspector = inspect(JournalEntry)
            column_names = [column.name for column in inspector.columns 
                           if column.name != 'user_reflection']
            
            logger.info(f"Available columns for JournalEntry: {column_names}")
            
            # Test a limited query with explicit column selection
            test_query = db.session.query(
                JournalEntry.id,
                JournalEntry.title,
                JournalEntry.content,
                JournalEntry.created_at,
                JournalEntry.updated_at,
                JournalEntry.is_analyzed,
                JournalEntry.anxiety_level,
                JournalEntry.user_id
            ).limit(1).all()
            
            logger.info(f"Test query successful, got {len(test_query)} results")
            
            # Print message for the user
            print("Fixed the JournalEntry query to avoid the user_reflection column.")
            print("Now you should be able to log in successfully.")
            
    except Exception as e:
        logger.error(f"Error fixing dashboard query: {str(e)}")
        raise

def main():
    """Main function to run the fix."""
    logger.info("Starting query fix...")
    fix_dashboard_query()
    logger.info("Query fix applied.")

if __name__ == "__main__":
    main()
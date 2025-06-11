"""
Script to add demographics columns to the user table.
This allows users to provide demographic information for personalized AI responses.
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_demographics_columns():
    """Add demographics columns to the user table if they don't exist"""
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not found")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # List of columns to add
        columns_to_add = [
            ('demographics_collected', 'BOOLEAN DEFAULT FALSE'),
            ('age_range', 'VARCHAR(20)'),
            ('gender', 'VARCHAR(30)'),
            ('location', 'VARCHAR(100)'),
            ('mental_health_concerns', 'TEXT')
        ]
        
        for column_name, column_definition in columns_to_add:
            try:
                with engine.connect() as conn:
                    # Try to add the column
                    sql = f'ALTER TABLE "user" ADD COLUMN {column_name} {column_definition};'
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(f"Added column {column_name} to user table")
            except (OperationalError, ProgrammingError) as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    logger.info(f"Column {column_name} already exists, skipping")
                else:
                    logger.error(f"Error adding column {column_name}: {str(e)}")
                    # Continue with other columns instead of failing completely
        
        logger.info("Demographics columns migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during demographics migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_demographics_columns()
    if success:
        print("Demographics columns added successfully!")
    else:
        print("Failed to add demographics columns.")
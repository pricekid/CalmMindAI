"""
Script to add journal reminder columns to the user table.
This allows users to set preferences for morning and evening journal reminders.
"""
import logging
import os
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Boolean, Time, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_journal_reminder_columns():
    """Add journal reminder columns to the user table if they don't exist"""
    # Connect to the database
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return
    
    engine = create_engine(database_url)
    metadata = MetaData()
    
    try:
        # Reflect the existing user table
        user_table = Table('user', metadata, autoload_with=engine)
        
        # Check if columns already exist
        columns_to_add = {}
        if 'morning_reminder_enabled' not in user_table.columns:
            columns_to_add['morning_reminder_enabled'] = Column('morning_reminder_enabled', Boolean, default=True)
        
        if 'morning_reminder_time' not in user_table.columns:
            default_morning_time = datetime.strptime('08:00', '%H:%M').time()
            columns_to_add['morning_reminder_time'] = Column('morning_reminder_time', Time, default=default_morning_time)
        
        if 'evening_reminder_enabled' not in user_table.columns:
            columns_to_add['evening_reminder_enabled'] = Column('evening_reminder_enabled', Boolean, default=True)
        
        if 'evening_reminder_time' not in user_table.columns:
            default_evening_time = datetime.strptime('20:00', '%H:%M').time()
            columns_to_add['evening_reminder_time'] = Column('evening_reminder_time', Time, default=default_evening_time)
        
        # Add any missing columns
        if columns_to_add:
            with engine.begin() as conn:
                for column_name, column in columns_to_add.items():
                    logger.info(f"Adding column {column_name} to user table")
                    # Use text() to properly create SQL statements
                    conn.execute(text(f"ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS {column_name} {column.type}"))
                    
                    # Set default values for existing users
                    if column_name == 'morning_reminder_enabled' or column_name == 'evening_reminder_enabled':
                        conn.execute(text(f"UPDATE \"user\" SET {column_name} = TRUE WHERE {column_name} IS NULL"))
                    elif column_name == 'morning_reminder_time':
                        conn.execute(text(f"UPDATE \"user\" SET {column_name} = '08:00:00' WHERE {column_name} IS NULL"))
                    elif column_name == 'evening_reminder_time':
                        conn.execute(text(f"UPDATE \"user\" SET {column_name} = '20:00:00' WHERE {column_name} IS NULL"))
            
            logger.info("Journal reminder columns added successfully")
        else:
            logger.info("Journal reminder columns already exist")
        
    except OperationalError as e:
        logger.error(f"Database operation failed: {e}")
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")

if __name__ == "__main__":
    add_journal_reminder_columns()
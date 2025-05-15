"""
Script to add notification_log table to the database.
This table tracks notifications sent to users.
"""
import logging
import os
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_notification_log_table():
    """Add notification_log table to the database if it doesn't exist"""
    # Connect to the database
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return
    
    engine = create_engine(database_url)
    
    try:
        # Check if table exists
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'notification_log')"
            ))
            exists = result.scalar()
            
            if not exists:
                logger.info("Creating notification_log table")
                conn.execute(text("""
                    CREATE TABLE notification_log (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        notification_type VARCHAR(50) NOT NULL,
                        sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        status VARCHAR(20) DEFAULT 'sent',
                        error_message TEXT,
                        FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                logger.info("Successfully created notification_log table")
            else:
                logger.info("notification_log table already exists")
                
    except OperationalError as e:
        logger.error(f"Database operation failed: {e}")
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")

if __name__ == "__main__":
    add_notification_log_table()
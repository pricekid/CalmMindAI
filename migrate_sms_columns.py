"""
Migration script to add SMS notification columns to the User table.
"""
import os
import sys
import logging
from app import app, db
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add phone_number and sms_notifications_enabled columns to the User table."""
    try:
        # Create a connection directly to execute raw SQL
        with db.engine.connect() as connection:
            # Check if columns already exist
            result = connection.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'phone_number'
            """))
            phone_number_exists = bool(result.fetchone())
            
            result = connection.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'sms_notifications_enabled'
            """))
            sms_enabled_exists = bool(result.fetchone())
            
            # Add the columns if they don't exist
            if not phone_number_exists:
                logger.info("Adding phone_number column to User table")
                connection.execute(text("""
                    ALTER TABLE "user" ADD COLUMN phone_number VARCHAR(20)
                """))
            else:
                logger.info("phone_number column already exists")
                
            if not sms_enabled_exists:
                logger.info("Adding sms_notifications_enabled column to User table")
                connection.execute(text("""
                    ALTER TABLE "user" ADD COLUMN sms_notifications_enabled BOOLEAN DEFAULT FALSE
                """))
            else:
                logger.info("sms_notifications_enabled column already exists")
            
            # Commit the transaction
            connection.commit()
            
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        success = run_migration()
        sys.exit(0 if success else 1)
"""
Script to add referral fields to the user table.
This is a one-time migration to add the referral_code and referred_by columns.
"""
import os
import sys
import logging
from app import app, db
from flask import Flask
from sqlalchemy import Column, String, Integer, text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_referral_columns():
    """Add referral_code and referred_by columns to the user table."""
    try:
        # Check if the columns already exist
        with db.engine.connect() as conn:
            # Check for referral_code column
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'user' AND column_name = 'referral_code'"
            ))
            referral_code_exists = result.fetchone() is not None
            
            # Check for referred_by column
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'user' AND column_name = 'referred_by'"
            ))
            referred_by_exists = result.fetchone() is not None
        
        # Add missing columns
        with db.engine.begin() as conn:
            if not referral_code_exists:
                logger.info("Adding referral_code column to user table...")
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN referral_code VARCHAR(8) UNIQUE"))
                logger.info("Successfully added referral_code column")
            else:
                logger.info("referral_code column already exists, skipping...")
                
            if not referred_by_exists:
                logger.info("Adding referred_by column to user table...")
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN referred_by INTEGER REFERENCES \"user\" (id)"))
                logger.info("Successfully added referred_by column")
            else:
                logger.info("referred_by column already exists, skipping...")
        
        return True
    except Exception as e:
        logger.error(f"Error adding referral columns: {str(e)}")
        return False

def main():
    """Main function to run the migration."""
    logger.info("Starting migration to add referral fields...")
    
    with app.app_context():
        success = add_referral_columns()
        
        if success:
            logger.info("Migration completed successfully!")
        else:
            logger.error("Migration failed, see logs for details")
            sys.exit(1)

if __name__ == "__main__":
    main()
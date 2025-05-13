import os
import logging
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """
    Migrate the database schema to support Replit Auth.
    This script drops and recreates tables to ensure compatibility.
    """
    # Get database connection string
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to the database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Drop existing tables in reverse order of dependency
        logger.info("Dropping existing tables...")
        cursor.execute("""
        DROP TABLE IF EXISTS mood_log CASCADE;
        DROP TABLE IF EXISTS cbt_recommendation CASCADE;
        DROP TABLE IF EXISTS journal_entry CASCADE;
        DROP TABLE IF EXISTS flask_dance_oauth CASCADE;
        DROP TABLE IF EXISTS "user" CASCADE;
        """)
        
        # Create user table with string ID
        logger.info("Creating user table...")
        cursor.execute("""
        CREATE TABLE "user" (
            id VARCHAR PRIMARY KEY,
            username VARCHAR(64) UNIQUE,
            email VARCHAR(120) UNIQUE,
            password_hash VARCHAR(256),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            first_name VARCHAR(64),
            last_name VARCHAR(64),
            profile_image_url VARCHAR(256),
            notifications_enabled BOOLEAN DEFAULT TRUE,
            notification_time TIME DEFAULT '09:00:00',
            phone_number VARCHAR(20),
            sms_notifications_enabled BOOLEAN DEFAULT FALSE
        );
        """)
        
        # Create journal_entry table
        logger.info("Creating journal_entry table...")
        cursor.execute("""
        CREATE TABLE journal_entry (
            id SERIAL PRIMARY KEY,
            title VARCHAR(120) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_analyzed BOOLEAN DEFAULT FALSE,
            anxiety_level INTEGER,
            initial_insight TEXT,
            user_reflection TEXT,
            followup_insight TEXT,
            second_reflection TEXT,
            closing_message TEXT,
            conversation_complete BOOLEAN DEFAULT FALSE,
            user_id VARCHAR NOT NULL REFERENCES "user" (id)
        );
        """)
        
        # Create cbt_recommendation table
        logger.info("Creating cbt_recommendation table...")
        cursor.execute("""
        CREATE TABLE cbt_recommendation (
            id SERIAL PRIMARY KEY,
            thought_pattern VARCHAR(255) NOT NULL,
            recommendation TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            journal_entry_id INTEGER NOT NULL REFERENCES journal_entry (id)
        );
        """)
        
        # Create mood_log table
        logger.info("Creating mood_log table...")
        cursor.execute("""
        CREATE TABLE mood_log (
            id SERIAL PRIMARY KEY,
            mood_score INTEGER NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id VARCHAR NOT NULL REFERENCES "user" (id)
        );
        """)
        
        # Create flask_dance_oauth table for Replit auth
        logger.info("Creating flask_dance_oauth table...")
        cursor.execute("""
        CREATE TABLE flask_dance_oauth (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR REFERENCES "user" (id),
            browser_session_key VARCHAR NOT NULL,
            provider VARCHAR(50) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            token JSON NOT NULL,
            CONSTRAINT uq_user_browser_session_key_provider UNIQUE (user_id, browser_session_key, provider)
        );
        """)
        
        logger.info("Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error migrating database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
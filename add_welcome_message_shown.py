"""
Add welcome_message_shown column to user table
"""
import logging
from app import db, app
from sqlalchemy import text

def add_welcome_message_shown_column():
    """Add welcome_message_shown column to the user table if it doesn't exist"""
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Check if column exists
                result = connection.execute(
                    text("SELECT column_name FROM information_schema.columns "
                         "WHERE table_name = 'user' AND column_name = 'welcome_message_shown';")
                )
                column_exists = result.scalar() is not None
                
                if not column_exists:
                    logging.info("Adding welcome_message_shown column to user table...")
                    connection.execute(
                        text("ALTER TABLE \"user\" ADD COLUMN welcome_message_shown BOOLEAN DEFAULT FALSE;")
                    )
                    connection.commit()
                    logging.info("Added welcome_message_shown column to user table")
                else:
                    logging.info("welcome_message_shown column already exists in user table")
                    
        except Exception as e:
            logging.error(f"Error adding welcome_message_shown column: {e}")
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    add_welcome_message_shown_column()
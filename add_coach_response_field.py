
#!/usr/bin/env python3
"""
Add coach_response field to journal_entry table
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import JournalEntry

def add_coach_response_field():
    """Add coach_response field to existing journal entries"""
    with app.app_context():
        try:
            # Check if column exists using modern SQLAlchemy syntax
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SELECT column_name FROM information_schema.columns WHERE table_name='journal_entry' AND column_name='coach_response'"))
                if not result.fetchone():
                    # Add the column
                    conn.execute(db.text("ALTER TABLE journal_entry ADD COLUMN coach_response TEXT"))
                    conn.commit()
                    print("✅ Added coach_response column to journal_entry table")
                else:
                    print("✅ coach_response column already exists")
                
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            
if __name__ == "__main__":
    add_coach_response_field()

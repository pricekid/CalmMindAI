
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
            # Check if column exists
            result = db.engine.execute("SELECT column_name FROM information_schema.columns WHERE table_name='journal_entry' AND column_name='coach_response'")
            if not result.fetchone():
                # Add the column
                db.engine.execute("ALTER TABLE journal_entry ADD COLUMN coach_response TEXT")
                print("✅ Added coach_response column to journal_entry table")
            else:
                print("✅ coach_response column already exists")
                
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            
if __name__ == "__main__":
    add_coach_response_field()

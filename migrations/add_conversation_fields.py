
from app import db
from models import JournalEntry

def upgrade():
    """Add conversation fields to journal entries table"""
    with db.engine.connect() as conn:
        conn.execute('ALTER TABLE journal_entry ADD COLUMN initial_insight TEXT')
        conn.execute('ALTER TABLE journal_entry ADD COLUMN followup_insight TEXT')
        conn.execute('ALTER TABLE journal_entry ADD COLUMN second_reflection TEXT')
        conn.execute('ALTER TABLE journal_entry ADD COLUMN closing_message TEXT')
        conn.execute('ALTER TABLE journal_entry ADD COLUMN conversation_complete BOOLEAN DEFAULT FALSE')

if __name__ == '__main__':
    upgrade()

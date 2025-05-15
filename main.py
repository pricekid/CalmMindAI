from app import app, db
import logging
from flask import redirect
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Ensure database tables exist
with app.app_context():
    db.create_all()
    
    # Register notification test routes
    # This needs to be done here rather than in app.py to avoid circular imports
    try:
        # Import and register the notification test routes
        import notifications_test_routes
        logging.info("Notification test routes registered successfully")
    except Exception as e:
        logging.error(f"Error registering notification test routes: {e}")
    
    # Start the journal reminder scheduler
    try:
        from journal_reminder_scheduler import start_journal_reminder_scheduler
        start_journal_reminder_scheduler()
        logging.info("Journal reminder scheduler started")
    except Exception as e:
        logging.error(f"Error starting journal reminder scheduler: {e}")

# No Auth integration is required in main.py
# Authentication is handled in app.py and routes.py

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
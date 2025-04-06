from app import app
import subprocess
import logging
import os
from start_scheduler import start_scheduler, find_scheduler_process
from journal_routes import journal_bp
from notification_routes import notification_bp
import startup  # Import the startup script to ensure scheduler is running

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(journal_bp)
app.register_blueprint(notification_bp)

# Import admin_routes but don't register the blueprint again since it's imported in app.py
import admin_routes

if __name__ == "__main__":
    # The scheduler is already started by the startup module
    logger.info("Scheduler status checked by startup module")
    
    # Start the web application
    app.run(host="0.0.0.0", port=5000, debug=True)

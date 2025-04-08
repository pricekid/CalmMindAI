from app import app
import subprocess
import logging
import os
from start_scheduler import start_scheduler, find_scheduler_process
# Don't import blueprints here as they're already imported and registered in app.py
import startup  # Import the startup script to ensure scheduler is running

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import admin_routes but don't register the blueprint again since it's imported in app.py
import admin_routes

if __name__ == "__main__":
    # The scheduler is already started by the startup module
    logger.info("Scheduler status checked by startup module")
    
    # Import journal_routes but don't register the blueprint again since it's imported in app.py
    # This ensures the blueprint is available
    import journal_routes
    
    # Start the web application
    app.run(host="0.0.0.0", port=5000, debug=True)

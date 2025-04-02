from app import app
import subprocess
import logging
import os
from start_scheduler import start_scheduler, find_scheduler_process
from journal_routes import journal_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(journal_bp)

if __name__ == "__main__":
    # Start the scheduler if it's not already running
    if not find_scheduler_process():
        logger.info("Starting notification scheduler on application startup...")
        try:
            # Start the scheduler in a separate process to avoid blocking the main application
            subprocess.Popen(
                ["python3", "start_scheduler.py", "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setpgrp
            )
            logger.info("Scheduler startup command initiated")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
    else:
        logger.info("Scheduler is already running")
    
    # Start the web application
    app.run(host="0.0.0.0", port=5000, debug=True)

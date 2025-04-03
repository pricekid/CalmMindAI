from start_scheduler import start_scheduler, find_scheduler_process, stop_scheduler
import logging
import os
import time
import datetime
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_scheduler_running():
    """Make sure the scheduler is running, restart it if necessary."""
    # Check if PID file exists but process is not running
    if os.path.exists("scheduler.pid"):
        pid = None
        try:
            with open("scheduler.pid", "r") as f:
                pid = int(f.read().strip())
            
            # Check if process is running
            try:
                os.kill(pid, 0)  # Signal 0 tests if process exists
                logger.info(f"Scheduler already running with PID {pid}")
                return True
            except OSError:
                # Process not running, remove stale PID file
                logger.warning(f"Found stale PID file for scheduler (PID {pid}). Removing.")
                os.remove("scheduler.pid")
        except Exception as e:
            logger.error(f"Error checking scheduler PID: {str(e)}")
            # Try to remove the PID file if it exists
            try:
                os.remove("scheduler.pid")
            except:
                pass
    
    # Start the scheduler
    logger.info("Starting notification scheduler...")
    start_scheduler()
    return True

def scheduler_health_check():
    """Periodically check if the scheduler is running and restart if needed."""
    while True:
        try:
            # Sleep for 1 hour between checks
            time.sleep(3600)
            
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[{current_time}] Running scheduler health check...")
            
            # Check if scheduler is running
            if not find_scheduler_process():
                logger.warning("Scheduler is not running. Restarting...")
                ensure_scheduler_running()
            else:
                logger.info("Scheduler is running properly.")
        except Exception as e:
            logger.error(f"Error in scheduler health check: {str(e)}")

# Start a background thread to periodically check scheduler health
health_check_thread = threading.Thread(target=scheduler_health_check, daemon=True)
health_check_thread.start()

# Run when imported
ensure_scheduler_running()
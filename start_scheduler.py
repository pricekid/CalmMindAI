import subprocess
import logging
import os
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler():
    """Start the scheduler as a background process."""
    try:
        # Check if there's already a scheduler running
        running_process = find_scheduler_process()
        if running_process:
            logger.info(f"Scheduler is already running with PID {running_process}")
            return
        
        logger.info("Starting notification scheduler as a background process...")
        # Start the scheduler as a background process
        process = subprocess.Popen(
            ["python3", "scheduler.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setpgrp  # This prevents the process from being killed when the parent exits
        )
        
        # Check if the process started successfully
        if process.poll() is None:  # None means the process is still running
            logger.info(f"Scheduler started successfully with PID {process.pid}")
            
            # Write the PID to a file for later reference
            with open("scheduler.pid", "w") as f:
                f.write(str(process.pid))
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Failed to start scheduler. Error: {stderr.decode()}")
    
    except Exception as e:
        logger.error(f"An error occurred while starting the scheduler: {str(e)}")
        sys.exit(1)

def find_scheduler_process():
    """Find if the scheduler is already running."""
    try:
        # Check if the PID file exists
        if os.path.exists("scheduler.pid"):
            with open("scheduler.pid", "r") as f:
                pid = int(f.read().strip())
                
            # Check if the process with that PID is running
            try:
                # Sending signal 0 checks if the process exists without actually sending a signal
                os.kill(pid, 0)
                return pid
            except OSError:
                # Process doesn't exist
                os.remove("scheduler.pid")
                return None
        return None
    except Exception as e:
        logger.error(f"Error checking for running scheduler: {str(e)}")
        return None

def stop_scheduler():
    """Stop the scheduler if it's running."""
    try:
        pid = find_scheduler_process()
        if pid:
            logger.info(f"Stopping scheduler with PID {pid}...")
            os.kill(pid, signal.SIGTERM)
            os.remove("scheduler.pid")
            logger.info("Scheduler stopped successfully")
        else:
            logger.info("No running scheduler found")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    if command == "start":
        start_scheduler()
    elif command == "stop":
        stop_scheduler()
    elif command == "restart":
        stop_scheduler()
        start_scheduler()
    else:
        logger.error(f"Unknown command: {command}")
        print("Usage: python start_scheduler.py [start|stop|restart]")
        sys.exit(1)
from start_scheduler import start_scheduler, find_scheduler_process, stop_scheduler
import logging
import os
import time
import datetime
import threading
from scheduler_logs import log_scheduler_activity
import socket

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
                log_scheduler_activity("startup_check", f"Scheduler already running with PID {pid}")
                return True
            except OSError:
                # Process not running, remove stale PID file
                logger.warning(f"Found stale PID file for scheduler (PID {pid}). Removing.")
                log_scheduler_activity("startup_check", f"Found stale PID file for scheduler (PID {pid}). Removing.", success=False)
                os.remove("scheduler.pid")
        except Exception as e:
            logger.error(f"Error checking scheduler PID: {str(e)}")
            log_scheduler_activity("startup_check", f"Error checking scheduler PID: {str(e)}", success=False)
            # Try to remove the PID file if it exists
            try:
                os.remove("scheduler.pid")
            except:
                pass
    
    # Start the scheduler
    logger.info("Starting notification scheduler...")
    success = start_scheduler()
    
    # Log the startup attempt
    hostname = socket.gethostname()
    log_scheduler_activity(
        "scheduler_startup", 
        f"Started scheduler on host {hostname} at {datetime.datetime.now()}",
        success=success is not None
    )
    
    return success is not None

def scheduler_health_check():
    """Periodically check if the scheduler is running and restart if needed."""
    # Further reduced interval to 5 minutes for more reliability
    check_interval = 5 * 60  # 5 minutes in seconds
    
    # Track consecutive failures for more aggressive intervention
    consecutive_failures = 0
    max_failures_before_restart = 3
    
    while True:
        try:
            # Sleep between checks
            time.sleep(check_interval)
            
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[{current_time}] Running scheduler health check...")
            
            # Check if scheduler is running
            pid = find_scheduler_process()
            if not pid:
                consecutive_failures += 1
                logger.warning(f"Scheduler is not running. Restarting... (Failure {consecutive_failures}/{max_failures_before_restart})")
                log_scheduler_activity(
                    "health_check", 
                    f"Scheduler not running at {current_time}. Attempt {consecutive_failures} to restart.", 
                    success=False
                )
                
                # If we've had multiple consecutive failures, try a more aggressive approach
                if consecutive_failures >= max_failures_before_restart:
                    logger.error(f"Multiple consecutive scheduler failures ({consecutive_failures}). Performing forceful restart.")
                    log_scheduler_activity(
                        "health_check_critical", 
                        f"Critical: {consecutive_failures} consecutive failures. Performing forceful restart.",
                        success=False
                    )
                    # Try to stop any lingering processes first
                    stop_scheduler()
                    time.sleep(2)  # Wait for cleanup
                    start_result = start_scheduler()
                    if start_result:
                        consecutive_failures = 0  # Reset on success
                else:
                    # Regular restart attempt
                    restart_success = ensure_scheduler_running()
                    if restart_success:
                        consecutive_failures = 0  # Reset counter on successful restart
            else:
                consecutive_failures = 0  # Reset counter when scheduler is running
                logger.info(f"Scheduler is running properly with PID {pid}.")
                log_scheduler_activity(
                    "health_check", 
                    f"Scheduler running with PID {pid} at {current_time}"
                )
            
            # Enhanced monitoring around 6 AM notification time (5:30 AM - 6:30 AM)
            now = datetime.datetime.now()
            
            # Special check 30 minutes before 6 AM to ensure scheduler is ready
            if now.hour == 5 and now.minute >= 30:
                logger.info("Pre-6AM check to ensure scheduler is ready for morning notifications")
                pid = find_scheduler_process()
                if not pid:
                    logger.warning("Scheduler not running before 6 AM notifications! Restarting...")
                    log_scheduler_activity(
                        "pre_6am_check", 
                        "Critical: Scheduler not running before 6 AM notifications! Restarting...", 
                        success=False
                    )
                    # Stop any existing process and start fresh
                    stop_scheduler()
                    time.sleep(2)
                    ensure_scheduler_running()
                else:
                    logger.info(f"Pre-6AM check passed: Scheduler running with PID {pid}")
                    log_scheduler_activity(
                        "pre_6am_check", 
                        f"Scheduler ready for 6 AM notifications with PID {pid}"
                    )
            
            # Additional check right at 6 AM to verify notifications are being sent
            if now.hour == 6 and now.minute < 10:
                logger.info("6AM critical check: Verifying scheduler is running during notification time")
                pid = find_scheduler_process()
                if not pid:
                    logger.critical("CRITICAL: Scheduler not running during 6 AM notification window!")
                    log_scheduler_activity(
                        "notification_time_check", 
                        "CRITICAL: Scheduler not running during 6 AM notification window!", 
                        success=False
                    )
                    # Emergency restart
                    stop_scheduler()
                    time.sleep(2)
                    start_scheduler()
                else:
                    logger.info(f"6AM notification time check passed: Scheduler running with PID {pid}")
                    log_scheduler_activity(
                        "notification_time_check", 
                        f"6AM notifications should be sending. Scheduler running with PID {pid}"
                    )
        except Exception as e:
            error_msg = f"Error in scheduler health check: {str(e)}"
            logger.error(error_msg)
            log_scheduler_activity("health_check_error", error_msg, success=False)

# Start a background thread to periodically check scheduler health
health_check_thread = threading.Thread(target=scheduler_health_check, daemon=True)
health_check_thread.start()

# Run when imported
ensure_scheduler_running()
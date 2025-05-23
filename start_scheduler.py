import subprocess
import logging
import os
import signal
import sys
import time
import datetime
from scheduler_logs import log_scheduler_activity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler():
    """
    Start the scheduler as a background process.
    
    Returns:
        int: The PID of the scheduler process if successful, None otherwise
    """
    try:
        # Check if there's already a scheduler running
        running_process = find_scheduler_process()
        if running_process:
            logger.info(f"Scheduler is already running with PID {running_process}")
            return running_process
        
        logger.info("Starting notification scheduler as a background process...")
        
        # Start the scheduler as a background process
        process = subprocess.Popen(
            ["python3", "scheduler.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setpgrp  # This prevents the process from being killed when the parent exits
        )
        
        # Wait briefly to make sure the process starts
        time.sleep(1)
        
        # Check if the process started successfully
        if process.poll() is None:  # None means the process is still running
            logger.info(f"Scheduler started successfully with PID {process.pid}")
            log_scheduler_activity("process_start", f"Scheduler started successfully with PID {process.pid}")
            
            # Write the PID to a file for later reference
            with open("scheduler.pid", "w") as f:
                f.write(str(process.pid))
                
            # Try to verify the process
            try:
                # Additional verification using 'ps'
                ps_output = subprocess.check_output(['ps', '-p', str(process.pid), '-o', 'command='])
                ps_output = ps_output.decode('utf-8').strip()
                
                if 'scheduler.py' in ps_output or 'python' in ps_output:
                    logger.info(f"Verified scheduler process {process.pid} is running: {ps_output}")
                else:
                    logger.warning(f"Process {process.pid} may not be running scheduler.py: {ps_output}")
            except Exception as e:
                logger.warning(f"Could not verify scheduler process details: {str(e)}")
                
            return process.pid
        else:
            stdout, stderr = process.communicate()
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Failed to start scheduler. Error: {error_msg}")
            log_scheduler_activity("process_start_error", f"Failed to start scheduler. Error: {error_msg}", success=False)
            return None
    
    except Exception as e:
        logger.error(f"An error occurred while starting the scheduler: {str(e)}")
        log_scheduler_activity("process_start_exception", f"An error occurred while starting the scheduler: {str(e)}", success=False)
        return None

def find_scheduler_process():
    """
    Find if the scheduler is already running.
    
    Returns:
        int: The PID of the scheduler process if running, None otherwise
    """
    try:
        # Check if the PID file exists
        if os.path.exists("scheduler.pid"):
            with open("scheduler.pid", "r") as f:
                pid = int(f.read().strip())
                
            # Check if the process with that PID is running
            try:
                # Sending signal 0 checks if the process exists without actually sending a signal
                os.kill(pid, 0)
                
                # Try to verify if it's a Python or scheduler process using ps
                try:
                    ps_output = subprocess.check_output(['ps', '-p', str(pid), '-o', 'command='], stderr=subprocess.DEVNULL)
                    ps_output = ps_output.decode('utf-8').strip()
                    
                    if 'scheduler.py' in ps_output or 'python' in ps_output:
                        logger.debug(f"Verified scheduler process {pid} is running")
                        return pid
                    else:
                        logger.warning(f"Process {pid} exists but doesn't appear to be scheduler.py: {ps_output}")
                        log_scheduler_activity("process_check", f"Process {pid} exists but doesn't appear to be scheduler.py: {ps_output}", success=False)
                        # Since the PID exists but it's not our process, remove the stale PID file
                        os.remove("scheduler.pid")
                        return None
                except subprocess.CalledProcessError:
                    # ps command failed, but process exists (from os.kill check)
                    # Assume it's our scheduler process
                    return pid
                except Exception as e:
                    # If we can't verify with ps, assume it's the scheduler if it's running
                    logger.debug(f"Could not verify process details: {str(e)}")
                    return pid
            except OSError:
                # Process doesn't exist
                logger.warning(f"Process {pid} from PID file doesn't exist. Removing stale file.")
                log_scheduler_activity("process_check", f"Process {pid} from PID file doesn't exist. Removing stale file.", success=False)
                os.remove("scheduler.pid")
                return None
        return None
    except Exception as e:
        logger.error(f"Error checking for running scheduler: {str(e)}")
        log_scheduler_activity("process_check_error", f"Error checking for running scheduler: {str(e)}", success=False)
        return None

def stop_scheduler():
    """
    Stop the scheduler if it's running.
    
    Returns:
        bool: True if the scheduler was stopped or wasn't running, False if there was an error
    """
    try:
        pid = find_scheduler_process()
        if pid:
            logger.info(f"Stopping scheduler with PID {pid}...")
            try:
                os.kill(pid, signal.SIGTERM)
                
                # Wait briefly to ensure process terminates
                for _ in range(5):  # Wait up to 5 seconds
                    try:
                        os.kill(pid, 0)  # Check if process still exists
                        time.sleep(1)
                    except OSError:
                        break  # Process terminated
                
                # Force kill if still running
                try:
                    os.kill(pid, 0)
                    logger.warning(f"Process {pid} didn't terminate with SIGTERM, using SIGKILL")
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass  # Process already terminated
                
                if os.path.exists("scheduler.pid"):
                    os.remove("scheduler.pid")
                    
                logger.info("Scheduler stopped successfully")
                log_scheduler_activity("process_stop", f"Scheduler with PID {pid} stopped successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to stop scheduler: {str(e)}")
                log_scheduler_activity("process_stop_error", f"Failed to stop scheduler with PID {pid}: {str(e)}", success=False)
                return False
        else:
            logger.info("No running scheduler found")
            log_scheduler_activity("process_stop", "No running scheduler found to stop")
            return True
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        log_scheduler_activity("process_stop_exception", f"Error stopping scheduler: {str(e)}", success=False)
        return False

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    # Log the command being executed
    log_scheduler_activity("command_execution", f"Executing command: {command}")
    
    if command == "start":
        pid = start_scheduler()
        result_success = pid is not None
        log_scheduler_activity(
            "command_result", 
            f"Command 'start' completed with {'success' if result_success else 'failure'}", 
            success=result_success
        )
        sys.exit(0 if pid else 1)
    elif command == "stop":
        success = stop_scheduler()
        log_scheduler_activity(
            "command_result", 
            f"Command 'stop' completed with {'success' if success else 'failure'}", 
            success=success
        )
        sys.exit(0 if success else 1)
    elif command == "restart":
        stop_success = stop_scheduler()
        pid = start_scheduler()
        result_success = stop_success and pid is not None
        log_scheduler_activity(
            "command_result", 
            f"Command 'restart' completed with {'success' if result_success else 'failure'}", 
            success=result_success
        )
        sys.exit(0 if result_success else 1)
    elif command == "status":
        pid = find_scheduler_process()
        status_msg = f"Scheduler is {'running' if pid else 'not running'}"
        if pid:
            print(f"Scheduler is running with PID {pid}")
            log_scheduler_activity("status_check", f"Status check: {status_msg} with PID {pid}")
            sys.exit(0)
        else:
            print("Scheduler is not running")
            log_scheduler_activity("status_check", f"Status check: {status_msg}")
            sys.exit(1)
    else:
        logger.error(f"Unknown command: {command}")
        log_scheduler_activity("command_error", f"Unknown command: {command}", success=False)
        print("Usage: python start_scheduler.py [start|stop|restart|status]")
        sys.exit(1)
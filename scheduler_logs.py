import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the data directory exists
def ensure_data_directory():
    os.makedirs("data", exist_ok=True)

def log_scheduler_activity(activity_type, message, success=True):
    """
    Log scheduler activity to help diagnose issues.
    
    Args:
        activity_type: Type of activity (startup, health_check, daily_notification, etc.)
        message: Description of the activity
        success: Whether the activity was successful
    """
    try:
        ensure_data_directory()
        log_file = "data/scheduler_activity.json"
        
        # Create the file with an empty list if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, "w") as f:
                json.dump([], f)
        
        # Read existing logs
        with open(log_file, "r") as f:
            logs = json.load(f)
        
        # Add new log entry
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,
            "message": message,
            "success": success
        })
        
        # Keep only the most recent 100 logs to prevent file growth
        if len(logs) > 100:
            logs = logs[-100:]
        
        # Write updated logs
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)
            
        return True
    except Exception as e:
        logger.error(f"Failed to log scheduler activity: {str(e)}")
        return False

def get_latest_scheduler_logs(count=10):
    """Get the most recent scheduler activity logs."""
    try:
        log_file = "data/scheduler_activity.json"
        
        if not os.path.exists(log_file):
            return []
        
        with open(log_file, "r") as f:
            logs = json.load(f)
        
        # Return the most recent logs
        return logs[-count:] if logs else []
    except Exception as e:
        logger.error(f"Failed to get scheduler logs: {str(e)}")
        return []
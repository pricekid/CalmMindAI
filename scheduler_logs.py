"""
Scheduler logging service for tracking notification system activity.
This helps diagnose notification issues by providing a detailed log of scheduler activity.
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = "data"
SCHEDULER_LOGS_FILE = os.path.join(DATA_DIR, "scheduler_logs.json")

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"Created data directory: {DATA_DIR}")

def log_scheduler_activity(activity_type: str, message: str, success: bool = True):
    """
    Log scheduler activity to help diagnose issues.
    
    Args:
        activity_type: Type of activity (startup, health_check, daily_notification, etc.)
        message: Description of the activity
        success: Whether the activity was successful
    """
    ensure_data_directory()
    
    # Create the log entry
    log_entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "type": activity_type,
        "message": message,
        "success": success
    }
    
    try:
        # Load existing logs
        logs = []
        if os.path.exists(SCHEDULER_LOGS_FILE):
            with open(SCHEDULER_LOGS_FILE, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Could not parse {SCHEDULER_LOGS_FILE}, creating new log file")
                    logs = []
        
        # Add new log entry
        logs.append(log_entry)
        
        # Truncate logs if they get too large (keep last 1000 entries)
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        # Save updated logs
        with open(SCHEDULER_LOGS_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
        
        logger.info(f"Logged scheduler activity: {activity_type} - {message} (success: {success})")
    except Exception as e:
        logger.error(f"Failed to log scheduler activity: {str(e)}")

def get_latest_scheduler_logs(count: int = 50) -> List[Dict[str, Any]]:
    """
    Get the most recent scheduler activity logs.
    
    Args:
        count: Maximum number of logs to return
        
    Returns:
        List of log entries sorted by timestamp (newest first)
    """
    ensure_data_directory()
    
    logs = []
    if os.path.exists(SCHEDULER_LOGS_FILE):
        try:
            with open(SCHEDULER_LOGS_FILE, 'r') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading scheduler logs: {str(e)}")
            return []
    
    # Sort logs by timestamp (newest first) and limit to count
    sorted_logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)
    return sorted_logs[:count]
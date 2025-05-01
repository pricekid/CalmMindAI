
"""Scheduler functionality disabled"""
import logging
import os
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log the shutdown
shutdown_msg = {
    "timestamp": datetime.now().isoformat(),
    "type": "scheduler_disabled",
    "message": f"Scheduler deliberately disabled on host {os.uname()[1]} at {datetime.now()} to prevent unwanted notifications",
    "success": True
}

# Add shutdown message to logs
try:
    with open('data/scheduler_logs.json', 'r') as f:
        logs = json.load(f)
    logs.append(shutdown_msg)
    with open('data/scheduler_logs.json', 'w') as f:
        json.dump(logs, f, indent=2)
except Exception as e:
    logger.error(f"Error logging shutdown: {str(e)}")

logger.info("Scheduler permanently disabled")

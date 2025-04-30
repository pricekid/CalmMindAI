#!/usr/bin/env python3
"""
SCHEDULER DISABLED

This scheduler has been permanently disabled to prevent unwanted emails.
DO NOT MODIFY THIS FILE OR TRY TO RESTORE IT.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create block file
Path("data").mkdir(exist_ok=True)
with open("data/notifications_blocked", "w") as f:
    f.write("Notifications permanently blocked")
logger.error("SCHEDULER PERMANENTLY DISABLED")
logger.error("This scheduler has been disabled to prevent unwanted emails")
print("SCHEDULER PERMANENTLY DISABLED")
print("This scheduler has been disabled to prevent unwanted emails")

# Kill any running schedulers
try:
    import subprocess
    subprocess.run(["pkill", "-f", "scheduler.py"])
    logger.error("Killed any running scheduler processes")
except:
    pass

# Immediately exit with error code
sys.exit(1)
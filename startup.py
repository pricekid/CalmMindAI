import logging
import os
import datetime
import socket
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CRITICAL: Override environment variables at the module level
# This is the first thing that happens on startup
os.environ["SENDGRID_API_KEY"] = "PERMANENTLY-DISABLED"
os.environ["TWILIO_ACCOUNT_SID"] = "PERMANENTLY-DISABLED"
os.environ["TWILIO_AUTH_TOKEN"] = "PERMANENTLY-DISABLED"

def log_scheduler_activity(activity_type, message, success=True):
    """Simple implementation to avoid dependencies on scheduler_logs module"""
    logger.info(f"SCHEDULER DISABLED: {activity_type} - {message}")

# Create a permanent notification block
def create_permanent_notification_block():
    """Create a permanent block file that prevents notifications from being sent"""
    try:
        Path("data").mkdir(exist_ok=True)
        block_file = "data/notifications_blocked"
        with open(block_file, "w") as f:
            f.write(f"Notifications permanently blocked at {datetime.datetime.now()}")
        logger.info(f"Created permanent notification block file: {block_file}")
    except Exception as e:
        logger.error(f"Error creating notification block: {e}")

# Block notifications at startup
create_permanent_notification_block()

def ensure_scheduler_not_running():
    """Make sure the scheduler is NOT running, stop it if it is."""
    # Check if PID file exists
    if os.path.exists("scheduler.pid"):
        try:
            # Remove the PID file
            os.remove("scheduler.pid")
            logger.info("Removed scheduler PID file")
        except Exception as e:
            logger.error(f"Error removing scheduler PID file: {str(e)}")
    
    # Kill any scheduler processes
    try:
        # Find processes with 'scheduler.py' in the command line
        import subprocess
        process = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        lines = process.stdout.split("\n")
        
        # Kill any scheduler processes
        for line in lines:
            if "scheduler.py" in line and "grep" not in line:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        os.kill(pid, 9)  # SIGKILL
                        logger.info(f"Stopped scheduler process with PID {pid}")
                    except Exception as e:
                        logger.error(f"Error stopping scheduler process: {e}")
    except Exception as e:
        logger.error(f"Error finding scheduler processes: {e}")

# Stop any running scheduler processes at startup
logger.info("NOTIFICATIONS PERMANENTLY DISABLED")
logger.info("Ensuring no schedulers are running...")
ensure_scheduler_not_running()
logger.info("Scheduler has been disabled to prevent unwanted notifications.")

# Log that scheduler is disabled
hostname = socket.gethostname()
logger.info(f"Scheduler deliberately disabled on host {hostname} at {datetime.datetime.now()} to prevent unwanted notifications")

# Ensure no scheduler can start
try:
    # Make scheduler.py non-executable as an extra precaution
    if os.path.exists("scheduler.py"):
        os.chmod("scheduler.py", 0o444)  # read-only for all
        logger.info("Made scheduler.py read-only to prevent execution")
    
    # Also disable start_scheduler.py
    if os.path.exists("start_scheduler.py"):
        os.chmod("start_scheduler.py", 0o444)  # read-only for all
        logger.info("Made start_scheduler.py read-only to prevent execution")
except Exception as e:
    logger.error(f"Error securing scheduler files: {e}")
    
# Create the blocking modules
try:
    # Create fake sendgrid and twilio modules
    from pathlib import Path
    
    # Ensure twilio directory exists
    Path("twilio").mkdir(exist_ok=True)
    
    # Create fake sendgrid.py to block emails
    with open("sendgrid.py", "w") as f:
        f.write('''"""
Fake SendGrid module that blocks all email sending attempts.
This will override the actual SendGrid module when imported locally.
"""
import logging
logger = logging.getLogger("sendgrid_blocker")
logger.warning("SendGrid module overridden to block all emails")
print("SENDGRID EMAILS PERMANENTLY BLOCKED")

class SendGridAPIClient:
    """Fake client that blocks all sends"""
    def __init__(self, api_key=None, **kwargs):
        print("BLOCKED: SendGrid initialization")
    def send(self, message):
        """Block all send attempts"""
        print("BLOCKED: SendGrid send attempt")
        return None

class helpers:
    """Fake helpers module"""
    class mail:
        """Fake mail module"""
        class Mail: 
            def __init__(self, **kwargs): pass
        class Email: 
            def __init__(self, email=None): pass
        class To: 
            def __init__(self, email=None): pass
        class Content: 
            def __init__(self, mime_type=None, content=None): pass
        class Personalization: 
            def __init__(self): pass
''')
    
    # Create fake twilio/__init__.py to block SMS
    with open("twilio/__init__.py", "w") as f:
        f.write('''"""
Fake Twilio module that blocks all SMS sending attempts.
"""
import logging
logger = logging.getLogger("twilio_blocker")
logger.warning("Twilio module overridden to block all SMS")
print("TWILIO SMS PERMANENTLY BLOCKED")

class rest:
    """Fake rest module"""
    class Client:
        """Fake Client class"""
        def __init__(self, username=None, password=None, **kwargs):
            print("BLOCKED: Twilio initialization")
            self.messages = self.Messages()
        class Messages:
            """Fake Messages class"""
            def create(self, to=None, from_=None, body=None, **kwargs):
                """Block all send attempts"""
                print(f"BLOCKED: Twilio message to {to}")
                return None
''')
    
    logger.info("Created fake SendGrid and Twilio modules to block all notification attempts")
except Exception as e:
    logger.error(f"Error creating fake modules: {e}")

logger.info("NOTIFICATIONS COMPLETELY DISABLED - The application will not send any emails or SMS")
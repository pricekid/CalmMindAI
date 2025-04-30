"""
Fake Twilio module that blocks all SMS sending attempts.
This will override the actual Twilio module when imported locally.
"""
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("twilio_blocker")

# Log the block
logger.warning("Twilio module has been overridden to block all SMS sending")
print("TWILIO SMS BLOCKED: Module has been overridden to prevent all SMS")

# Environment variable nullification
os.environ["TWILIO_ACCOUNT_SID"] = "PERMANENTLY-DISABLED"
os.environ["TWILIO_AUTH_TOKEN"] = "PERMANENTLY-DISABLED"

# Create a fake client
class rest:
    """Fake rest module"""
    class Client:
        """Fake Client class"""
        def __init__(self, username=None, password=None, **kwargs):
            logger.warning(f"Blocked Twilio Client initialization with username: {username}")
            print(f"TWILIO BLOCKED: Client initialization attempt blocked")
            self.messages = self.Messages()
            
        class Messages:
            """Fake Messages class"""
            def create(self, to=None, from_=None, body=None, **kwargs):
                """Block all send attempts"""
                logger.warning(f"Blocked Twilio message creation to: {to}")
                print(f"TWILIO BLOCKED: Message creation to {to} blocked")
                return None

# Export fake classes
__all__ = ['rest']
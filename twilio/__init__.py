"""
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

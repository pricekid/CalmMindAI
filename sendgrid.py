"""
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

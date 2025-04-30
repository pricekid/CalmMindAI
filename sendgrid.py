"""
Fake SendGrid module that blocks all email sending attempts.
This will override the actual SendGrid module when imported locally.
"""
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sendgrid_blocker")

# Log the block
logger.warning("SendGrid module has been overridden to block all email sending")
print("SENDGRID EMAILS BLOCKED: Module has been overridden to prevent all emails")

# Environment variable nullification
os.environ["SENDGRID_API_KEY"] = "PERMANENTLY-DISABLED"

class SendGridAPIClient:
    """Fake SendGrid API client that blocks all sends"""
    def __init__(self, api_key=None, **kwargs):
        logger.warning(f"Blocked SendGrid initialization with API key: {api_key}")
        print(f"SENDGRID BLOCKED: Initialization attempt blocked")
        
    def send(self, message):
        """Block all send attempts"""
        logger.warning(f"Blocked SendGrid send attempt")
        print("SENDGRID BLOCKED: Send attempt blocked")
        return None

# Helper module for imports like "from sendgrid.helpers.mail import Mail"
class helpers:
    """Fake helpers module"""
    class mail:
        """Fake mail module"""
        class Mail:
            """Fake Mail class"""
            def __init__(self, **kwargs):
                logger.warning("Blocked SendGrid Mail creation")
                
        class Email:
            """Fake Email class"""
            def __init__(self, email=None):
                logger.warning(f"Blocked SendGrid Email creation for: {email}")
                
        class To:
            """Fake To class"""
            def __init__(self, email=None):
                logger.warning(f"Blocked SendGrid To creation for: {email}")
                
        class Content:
            """Fake Content class"""
            def __init__(self, mime_type=None, content=None):
                logger.warning(f"Blocked SendGrid Content creation")
                
        class Personalization:
            """Fake Personalization class"""
            def __init__(self):
                logger.warning(f"Blocked SendGrid Personalization creation")

# Export fake classes
__all__ = ['SendGridAPIClient', 'helpers']
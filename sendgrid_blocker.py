"""
This script creates a fake SendGrid module that blocks all attempts to send email.
It will be placed in the Python path to intercept any attempts to use SendGrid.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sendgrid_blocker")

def create_fake_sendgrid_module():
    """Create a fake SendGrid module to block all email sending attempts"""
    try:
        # Find site-packages directory
        site_packages = None
        for path in sys.path:
            if "site-packages" in path and os.path.isdir(path):
                site_packages = path
                break
        
        if not site_packages:
            for path in sys.path:
                if "dist-packages" in path and os.path.isdir(path):
                    site_packages = path
                    break
        
        if not site_packages:
            logger.error("Could not find site-packages directory")
            return False
        
        # Create sendgrid directory if it doesn't exist
        sendgrid_dir = os.path.join(site_packages, "sendgrid")
        Path(sendgrid_dir).mkdir(exist_ok=True)
        
        # Create fake __init__.py
        init_file = os.path.join(sendgrid_dir, "__init__.py")
        with open(init_file, "w") as f:
            f.write("""
# Fake SendGrid module to block all email sending
import logging

logger = logging.getLogger("sendgrid_blocker")
logger.warning("Blocked attempt to import SendGrid")

class SendGridAPIClient:
    def __init__(self, api_key=None, **kwargs):
        logger.warning(f"Blocked SendGrid initialization attempt")
        
    def send(self, message):
        logger.warning(f"Blocked SendGrid send attempt")
        return None
        
# Export the fake class
__all__ = ['SendGridAPIClient']
""")
        
        # Create helpers directory
        helpers_dir = os.path.join(sendgrid_dir, "helpers")
        Path(helpers_dir).mkdir(exist_ok=True)
        
        # Create fake helpers/__init__.py
        helpers_init = os.path.join(helpers_dir, "__init__.py")
        with open(helpers_init, "w") as f:
            f.write("# Fake SendGrid helpers module")
        
        # Create fake helpers/mail.py
        mail_file = os.path.join(helpers_dir, "mail.py")
        with open(mail_file, "w") as f:
            f.write("""
# Fake SendGrid mail module to block all email sending
import logging

logger = logging.getLogger("sendgrid_blocker")

class Mail:
    def __init__(self, from_email=None, to_emails=None, subject=None, plain_text_content=None, html_content=None):
        logger.warning(f"Blocked SendGrid Mail creation")
        
class Email:
    def __init__(self, email=None):
        logger.warning(f"Blocked SendGrid Email creation")
        
class To:
    def __init__(self, email=None):
        logger.warning(f"Blocked SendGrid To creation")
        
class Content:
    def __init__(self, mime_type=None, content=None):
        logger.warning(f"Blocked SendGrid Content creation")
        
class Personalization:
    def __init__(self):
        logger.warning(f"Blocked SendGrid Personalization creation")
        
# Export the fake classes
__all__ = ['Mail', 'Email', 'To', 'Content', 'Personalization']
""")
        
        logger.info(f"Successfully created fake SendGrid module at {sendgrid_dir}")
        return True
    except Exception as e:
        logger.error(f"Error creating fake SendGrid module: {e}")
        return False

# Execute directly
if __name__ == "__main__":
    print("Creating fake SendGrid module to block all email sending...")
    if create_fake_sendgrid_module():
        print("✓ Successfully blocked SendGrid at the module level")
    else:
        print("✗ Failed to block SendGrid at the module level")
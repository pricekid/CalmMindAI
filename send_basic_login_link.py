"""
Script to send a basic login link to a user using our direct email sending method.
This bypasses Flask-Mail to solve environment variable access issues.
"""
import os
import logging
import sys
import time
import random
import string
from notification_service import send_login_link

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_token(length=32):
    """Generate a random token for login links"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def get_base_url():
    """Get the base URL for links in emails"""
    # Use environment variable if available, otherwise use default
    return os.environ.get('BASE_URL', 'https://calm-mind-ai-naturalarts.replit.app')

def main():
    # Check for command line argument
    if len(sys.argv) < 2:
        print("Usage: python3 send_basic_login_link.py [email_address]")
        return
    
    email = sys.argv[1]
    print(f"Sending login link to {email}...")
    
    # Generate token
    token = generate_token()
    
    # Generate login link
    base_url = get_base_url()
    expiry = int(time.time()) + 600  # 10 minutes
    link = f"{base_url}/login/token/{token}?email={email}&expires={expiry}"
    
    # Send login link
    result = send_login_link(email, link)
    
    if result:
        print("✅ Login link sent successfully!")
        print(f"\nToken: {token}")
        print(f"Expiry: {expiry} ({int((expiry - time.time()) / 60)} minutes from now)")
        print(f"Link: {link}")
    else:
        print("❌ Failed to send login link.")

if __name__ == "__main__":
    main()
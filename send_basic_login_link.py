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
        print("Usage: python3 send_basic_login_link.py [email_address] [optional_message]")
        print("Example: python3 send_basic_login_link.py user@example.com \"Welcome back to Calm Journey!\"")
        return
    
    email = sys.argv[1]
    
    # Optional custom message
    custom_message = None
    if len(sys.argv) >= 3:
        custom_message = sys.argv[2]
    
    print(f"Sending login link to {email}...")
    if custom_message:
        print(f"Custom message: {custom_message}")
    
    # Generate token
    token = generate_token()
    
    # Generate login link
    base_url = get_base_url()
    expiry = int(time.time()) + 600  # 10 minutes
    link = f"{base_url}/login/token/{token}?email={email}&expires={expiry}"
    
    # Send login link
    result = send_login_link(email, link, custom_message)
    
    if result:
        print("\n✅ Login link sent successfully!")
        print(f"Token: {token}")
        print(f"Expiry: {expiry} ({int((expiry - time.time()) / 60)} minutes from now)")
        print(f"Link: {link}")
        print("\nNotes:")
        print("* If the email doesn't arrive, check spam/junk folders")
        print("* The link will work once the user account with this email exists in the system")
        print("* Login links expire after 10 minutes for security")
    else:
        print("\n❌ Failed to send login link.")
        print("Possible reasons:")
        print("* Email server connection issues")
        print("* Invalid email address format")
        print("* Environment variables for email not properly configured")

if __name__ == "__main__":
    main()
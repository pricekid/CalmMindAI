"""
Script to test the update notification email on a specific email address.
"""
import sys
import logging
from send_update_notification import send_update_notification

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Check for command line argument
    if len(sys.argv) < 2:
        print("Usage: python3 test_update_notification.py [email_address] [optional_username]")
        print("Example: python3 test_update_notification.py user@example.com John")
        return
    
    email = sys.argv[1]
    username = "there"
    
    if len(sys.argv) >= 3:
        username = sys.argv[2]
    
    print(f"Sending test update notification to {email} with username '{username}'...")
    
    # Send update notification
    result = send_update_notification(email, username)
    
    if result:
        print("\n✅ Update notification sent successfully!")
        print("\nNotes:")
        print("* If the email doesn't arrive, check spam/junk folders")
        print("* The email contains information about new app features and a journaling reminder")
        print("* It includes links to the journal and dashboard pages")
    else:
        print("\n❌ Failed to send update notification.")
        print("Possible reasons:")
        print("* Email server connection issues")
        print("* Invalid email address format")
        print("* Environment variables for email not properly configured")

if __name__ == "__main__":
    main()
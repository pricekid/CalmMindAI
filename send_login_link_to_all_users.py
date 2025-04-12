"""
Script to send login links to all users with notifications enabled.
This uses our direct email sending method to bypass Flask-Mail.
"""
import os
import logging
import time
import random
import string
import json
from notification_service import send_login_link, ensure_data_directory

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

def load_users():
    """Load users from the data/users.json file"""
    ensure_data_directory()
    if not os.path.exists('data/users.json'):
        logger.error("data/users.json not found")
        return []
    
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Error decoding users.json file")
        return []
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return []

def send_to_all_users(custom_message=None):
    """
    Send login links to all users with notifications enabled.
    
    Args:
        custom_message: Optional custom message to include in the emails
    
    Returns:
        dict: Statistics about the sending process
    """
    # Load users
    users = load_users()
    logger.info(f"Loaded {len(users)} users")
    
    # Stats
    total_users = len(users)
    sent_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Base URL for login links
    base_url = get_base_url()
    
    for user in users:
        # Only send login links to users with notifications enabled
        if not user.get('notifications_enabled', False):
            logger.info(f"Skipping user {user.get('id')} ({user.get('email')}): Notifications disabled")
            skipped_count += 1
            continue
        
        # Get user email
        email = user.get('email')
        if not email:
            logger.warning(f"Skipping user {user.get('id')}: No email address")
            skipped_count += 1
            continue
        
        # Generate token
        token = generate_token()
        
        # Generate login link with a 24-hour expiration
        expiry = int(time.time()) + 86400  # 24 hours
        link = f"{base_url}/login/token/{token}?email={email}&expires={expiry}"
        
        # Send login link with custom message if provided
        logger.info(f"Sending login link to {email}...")
        try:
            # Pass custom message to the email function (will be handled in notification_service.py)
            result = send_login_link(email, link, custom_message)
            
            if result:
                logger.info(f"Login link sent to {email}")
                sent_count += 1
            else:
                logger.error(f"Failed to send login link to {email}")
                failed_count += 1
        except Exception as e:
            logger.error(f"Error sending login link to {email}: {str(e)}")
            failed_count += 1
        
        # Sleep briefly between emails to avoid rate limiting
        time.sleep(1)
    
    # Return stats
    stats = {
        "total_users": total_users,
        "sent_count": sent_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return stats

def main():
    print("Calm Journey - Send Login Links to All Users")
    print("------------------------------------------")
    
    # Ask if there's a custom message to include
    print("\nWould you like to include a custom message in the emails? (y/n)")
    choice = input("> ").strip().lower()
    
    custom_message = None
    if choice == 'y' or choice == 'yes':
        print("\nEnter your custom message (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if not line and lines and not lines[-1]:
                # Two consecutive empty lines means we're done
                break
            lines.append(line)
        custom_message = "\n".join(lines)
        print(f"\nCustom message set:\n---\n{custom_message}\n---")
    
    # Confirm before sending
    print("\nReady to send login links to all users with notifications enabled.")
    print("Are you sure you want to continue? (y/n)")
    confirm = input("> ").strip().lower()
    
    if confirm != 'y' and confirm != 'yes':
        print("Operation cancelled.")
        return
    
    # Send login links
    stats = send_to_all_users(custom_message)
    
    # Print stats
    print("\nSending complete!")
    print(f"Total users: {stats['total_users']}")
    print(f"Login links sent: {stats['sent_count']}")
    print(f"Users skipped: {stats['skipped_count']}")
    print(f"Failed to send: {stats['failed_count']}")

if __name__ == "__main__":
    main()
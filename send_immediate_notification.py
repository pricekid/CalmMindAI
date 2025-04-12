"""
Script to send an immediate notification to users with notifications enabled.
This uses the direct email sending method to bypass Flask-Mail.
"""
import logging
from notification_service import send_immediate_notification_to_all_users

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("Sending immediate notifications to users...")
    stats = send_immediate_notification_to_all_users()
    
    print("\nNotification Statistics:")
    print(f"Total users: {stats['total_users']}")
    print(f"Emails sent: {stats['sent_count']}")
    print(f"Emails failed: {stats['failed_count']}")
    print(f"Users skipped (notifications disabled): {stats['skipped_count']}")
    
    if stats['sent_count'] > 0:
        print("\n✅ Successfully sent notifications to some users!")
    else:
        print("\n❌ Failed to send notifications to any users.")
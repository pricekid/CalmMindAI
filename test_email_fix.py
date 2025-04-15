"""
Script to test the fixed email notification system.
"""
import os
import logging
import json
from datetime import datetime
from notification_service import send_test_email, send_immediate_notification_to_all_users

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')

def log_notification_result(result):
    """Log the result of a notification attempt to a file"""
    ensure_data_directory()
    log_file = 'data/email_notifications_sent.json'
    
    # Load existing log if it exists
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    else:
        logs = []
    
    # Add the new log entry
    logs.append({
        'timestamp': datetime.now().isoformat(),
        'result': result
    })
    
    # Save the updated log
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    logger.info(f"Notification result logged to {log_file}")

def test_environment_variables():
    """Test that all required environment variables are set"""
    mail_vars = [
        'MAIL_SERVER',
        'MAIL_PORT',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER'
    ]
    
    missing = []
    for var in mail_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        logger.warning(f"Missing environment variables: {', '.join(missing)}")
        logger.info("Checking for defaults in notification_service.py...")
    else:
        logger.info("All required mail environment variables are set.")
    
    # Print all mail environment variables
    for var in mail_vars:
        value = os.environ.get(var)
        if var == 'MAIL_PASSWORD' and value:
            logger.info(f"{var}: [Set but not displayed]")
        else:
            logger.info(f"{var}: {value}")

def main():
    """Main function to test the email notification system"""
    logger.info("Starting email notification system test...")
    
    # Check environment variables
    test_environment_variables()
    
    # Send a test email to the system admin
    admin_email = os.environ.get('MAIL_USERNAME', 'calmjourney7@gmail.com')
    logger.info(f"Sending test email to admin: {admin_email}")
    success = send_test_email(admin_email)
    
    if success:
        logger.info("Test email sent successfully!")
    else:
        logger.error("Failed to send test email.")
    
    # Log the notification attempt
    log_notification_result({
        'admin_test': success
    })
    
    # Test sending to all users with notifications enabled
    logger.info("Testing notification to all enabled users...")
    stats = send_immediate_notification_to_all_users()
    
    logger.info(f"Notification stats: {json.dumps(stats, indent=2)}")
    
    # Log the notification results
    log_notification_result({
        'mass_notification': stats
    })
    
    return 0

if __name__ == "__main__":
    main()
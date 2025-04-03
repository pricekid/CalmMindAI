import sys
import logging
from app import app, db, mail
import os
from notification_service import send_daily_reminder
from sms_notification_service import send_daily_sms_reminder, send_immediate_sms_to_all_users
from admin_utils import load_twilio_config
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_notifications():
    """Test sending email notifications to all eligible users."""
    logger.info("Testing email notifications...")
    
    # Test if email settings are configured
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_sender = os.environ.get('MAIL_DEFAULT_SENDER')
    
    if not all([mail_username, mail_password, mail_sender]):
        logger.error("Email settings are not properly configured.")
        logger.error(f"MAIL_USERNAME: {'Set' if mail_username else 'Not set'}")
        logger.error(f"MAIL_PASSWORD: {'Set' if mail_password else 'Not set'}")
        logger.error(f"MAIL_DEFAULT_SENDER: {'Set' if mail_sender else 'Not set'}")
        return False
    
    # Count eligible users
    with app.app_context():
        from models import User
        users = User.query.filter_by(notifications_enabled=True).all()
        logger.info(f"Found {len(users)} users with email notifications enabled")
        
        if not users:
            logger.warning("No users have email notifications enabled.")
            return False
        
        # Send notifications
        send_daily_reminder()
        logger.info("Email notifications sent successfully")
        return True

def test_sms_notifications():
    """Test sending SMS notifications to all eligible users."""
    logger.info("Testing SMS notifications...")
    
    # Check if Twilio credentials are configured
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
    
    # If environment variables are not set, try loading from config
    if not all([twilio_sid, twilio_token, twilio_phone]):
        logger.info("Twilio credentials not found in environment, checking config file...")
        
        with app.app_context():
            twilio_config = load_twilio_config()
            
            if twilio_config:
                # Set environment variables if values found in config
                if not twilio_sid and twilio_config.get("account_sid"):
                    os.environ["TWILIO_ACCOUNT_SID"] = twilio_config["account_sid"]
                    twilio_sid = twilio_config["account_sid"]
                
                if not twilio_token and twilio_config.get("auth_token"):
                    os.environ["TWILIO_AUTH_TOKEN"] = twilio_config["auth_token"]
                    twilio_token = twilio_config["auth_token"]
                
                if not twilio_phone and twilio_config.get("phone_number"):
                    os.environ["TWILIO_PHONE_NUMBER"] = twilio_config["phone_number"]
                    twilio_phone = twilio_config["phone_number"]
                    
                logger.info("Successfully loaded Twilio credentials from configuration")
            else:
                logger.error("No Twilio configuration found.")
    
    if not all([twilio_sid, twilio_token, twilio_phone]):
        logger.error("Twilio credentials are not properly configured.")
        logger.error(f"TWILIO_ACCOUNT_SID: {'Set' if twilio_sid else 'Not set'}")
        logger.error(f"TWILIO_AUTH_TOKEN: {'Set' if twilio_token else 'Not set'}")
        logger.error(f"TWILIO_PHONE_NUMBER: {'Set' if twilio_phone else 'Not set'}")
        return False
    
    # Count eligible users
    with app.app_context():
        from models import User
        users = User.query.filter_by(sms_notifications_enabled=True).filter(User.phone_number.isnot(None)).all()
        logger.info(f"Found {len(users)} users with SMS notifications enabled")
        
        if not users:
            logger.warning("No users have SMS notifications enabled with a valid phone number.")
            return False
        
        # Send immediate SMS notifications to eligible users
        result = send_immediate_sms_to_all_users()
        logger.info(f"SMS test results: {json.dumps(result)}")
        
        if result['success_count'] > 0:
            logger.info("SMS notifications sent successfully")
            return True
        else:
            logger.error("Failed to send any SMS notifications")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_notifications.py [email|sms|both]")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "email":
        test_email_notifications()
    elif mode == "sms":
        test_sms_notifications()
    elif mode == "both":
        email_result = test_email_notifications()
        sms_result = test_sms_notifications()
        print(f"Email test: {'Success' if email_result else 'Failed'}")
        print(f"SMS test: {'Success' if sms_result else 'Failed'}")
    else:
        print("Invalid mode. Use 'email', 'sms', or 'both'.")
        sys.exit(1)
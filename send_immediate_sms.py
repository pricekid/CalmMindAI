import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sms_notification_service import send_immediate_sms_to_all_users

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app context for database access
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Need to import models after db is initialized
from models import User

def main():
    """Send an immediate SMS notification to all users with SMS notifications enabled."""
    with app.app_context():
        # First try to get Twilio credentials from environment variables
        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
        
        # If not found in environment, try to load from saved configuration
        if not all([twilio_sid, twilio_token, twilio_phone]):
            try:
                # Import admin utils to load Twilio config
                from admin_utils import load_twilio_config
                
                twilio_config = load_twilio_config()
                if twilio_config:
                    twilio_sid = twilio_sid or twilio_config.get("account_sid", "")
                    twilio_token = twilio_token or twilio_config.get("auth_token", "")
                    twilio_phone = twilio_phone or twilio_config.get("phone_number", "")
                    
                    # Set environment variables for the SMS service to use
                    if twilio_sid:
                        os.environ["TWILIO_ACCOUNT_SID"] = twilio_sid
                    if twilio_token:
                        os.environ["TWILIO_AUTH_TOKEN"] = twilio_token
                    if twilio_phone:
                        os.environ["TWILIO_PHONE_NUMBER"] = twilio_phone
                        
                    logger.info("Loaded Twilio credentials from saved configuration.")
            except Exception as e:
                logger.error(f"Error loading Twilio config: {str(e)}")
        
        # Final check if credentials are available
        if not all([twilio_sid, twilio_token, twilio_phone]):
            logger.error("Twilio credentials are not set. Please configure Twilio in the admin panel or set environment variables.")
            return 1
        
        # Count eligible users
        eligible_count = User.query.filter_by(
            sms_notifications_enabled=True
        ).filter(User.phone_number.isnot(None)).count()
        
        logger.info(f"Found {eligible_count} users eligible for SMS notifications")
        
        if eligible_count == 0:
            logger.info("No users with SMS notifications enabled. Exiting.")
            return 0
        
        # Send SMS notifications
        try:
            result = send_immediate_sms_to_all_users()
            
            logger.info(f"SMS notification results: {result}")
            logger.info(f"Successfully sent {result['success_count']} SMS notifications")
            
            if result['failure_count'] > 0:
                logger.warning(f"Failed to send {result['failure_count']} SMS notifications")
            
            return 0
        except Exception as e:
            logger.error(f"Error sending SMS notifications: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
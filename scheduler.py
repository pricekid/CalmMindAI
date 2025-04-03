
from apscheduler.schedulers.blocking import BlockingScheduler
from notification_service import send_daily_reminder
from sms_notification_service import send_daily_sms_reminder
import logging
import os
import flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Flask app context for database access
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Create BlockingScheduler
scheduler = BlockingScheduler()

# Run email reminders every day at 6 AM with a 1-hour grace time
# This will ensure that if the scheduler is down at 6 AM, it will still run the job when it comes back up
scheduler.add_job(send_daily_reminder, 'cron', hour='6', minute=0, misfire_grace_time=3600)

# Run SMS reminders every day at 6 AM with a 1-hour grace time
scheduler.add_job(send_daily_sms_reminder, 'cron', hour='6', minute=0, misfire_grace_time=3600)

# Function to load Twilio credentials before SMS job runs
def load_twilio_credentials():
    """Load Twilio credentials from saved configuration file before sending SMS notifications"""
    try:
        # First check environment variables
        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
        
        # If not set, try to load from configuration
        if not all([twilio_sid, twilio_token, twilio_phone]):
            try:
                # Import here to avoid circular imports
                from admin_utils import load_twilio_config
                
                with app.app_context():
                    twilio_config = load_twilio_config()
                    
                    if twilio_config:
                        # Set environment variables if values found in config
                        if not twilio_sid and twilio_config.get("account_sid"):
                            os.environ["TWILIO_ACCOUNT_SID"] = twilio_config["account_sid"]
                        
                        if not twilio_token and twilio_config.get("auth_token"):
                            os.environ["TWILIO_AUTH_TOKEN"] = twilio_config["auth_token"]
                        
                        if not twilio_phone and twilio_config.get("phone_number"):
                            os.environ["TWILIO_PHONE_NUMBER"] = twilio_config["phone_number"]
                        
                        logger.info("Successfully loaded Twilio credentials from configuration")
            except Exception as e:
                logger.error(f"Error loading Twilio configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Error in load_twilio_credentials: {str(e)}")

# Run load_twilio_credentials before SMS job
scheduler.add_job(load_twilio_credentials, 'cron', hour='5', minute=59)

if __name__ == '__main__':
    # Load Twilio credentials at startup
    load_twilio_credentials()
    
    logging.info("Starting notification scheduler...")
    scheduler.start()

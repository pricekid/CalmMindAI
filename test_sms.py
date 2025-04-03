import os
import sys
import logging
from twilio.rest import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sms(phone_number):
    """Send a test SMS to a specific phone number"""
    message = "Calm Journey: This is a test SMS message from your journal app."
    logger.info(f"Sending test SMS to {phone_number}...")
    
    # Try sending the SMS
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
    
    # Log Twilio info (without showing actual credentials)
    logger.info(f"Twilio SID exists: {bool(twilio_sid)}")
    logger.info(f"Twilio token exists: {bool(twilio_token)}")
    logger.info(f"Twilio phone exists: {bool(twilio_phone)}")
    
    if all([twilio_sid, twilio_token, twilio_phone]):
        logger.info(f"Using Twilio phone number: {twilio_phone}")
        
        try:
            # Direct Twilio usage for maximum debug info
            client = Client(twilio_sid, twilio_token)
            sent_message = client.messages.create(
                body=message,
                from_=twilio_phone,
                to=phone_number
            )
            logger.info(f"SMS sent successfully! Message SID: {sent_message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send test SMS: {str(e)}")
            return False
    else:
        logger.error("Missing Twilio credentials. Cannot send test SMS.")
        return False

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) != 2:
        print("Usage: python test_sms.py +1XXXXXXXXXX")
        return 1
    
    phone_number = sys.argv[1]
    
    if not phone_number.startswith('+'):
        print("Phone number must be in international format starting with '+'")
        return 1
    
    success = test_sms(phone_number)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
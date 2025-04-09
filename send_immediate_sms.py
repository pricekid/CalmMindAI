"""
Script to send immediate SMS notifications to specific users or all users with SMS enabled.
"""
import os
import sys
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app import app, db
from models import User
from admin_utils import load_twilio_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_twilio_client():
    """Get the Twilio client with credentials from environment or config file."""
    # First try to get credentials from environment
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
    
    # If not in environment, try to load from file
    if not all([account_sid, auth_token, phone_number]):
        twilio_config = load_twilio_config()
        
        if twilio_config:
            if not account_sid and 'account_sid' in twilio_config:
                account_sid = twilio_config['account_sid']
                os.environ["TWILIO_ACCOUNT_SID"] = account_sid
            
            if not auth_token and 'auth_token' in twilio_config:
                auth_token = twilio_config['auth_token']
                os.environ["TWILIO_AUTH_TOKEN"] = auth_token
            
            if not phone_number and 'phone_number' in twilio_config:
                phone_number = twilio_config['phone_number']
                os.environ["TWILIO_PHONE_NUMBER"] = phone_number
    
    # Check if we have all required credentials
    if not all([account_sid, auth_token, phone_number]):
        missing = []
        if not account_sid: missing.append("TWILIO_ACCOUNT_SID")
        if not auth_token: missing.append("TWILIO_AUTH_TOKEN")
        if not phone_number: missing.append("TWILIO_PHONE_NUMBER")
        
        logger.error(f"Missing Twilio credentials: {', '.join(missing)}")
        return None, None
    
    try:
        client = Client(account_sid, auth_token)
        return client, phone_number
    except Exception as e:
        logger.error(f"Error creating Twilio client: {str(e)}")
        return None, None

def test_sms(to_phone_number):
    """Send a test SMS to a specific phone number."""
    client, from_phone = get_twilio_client()
    
    if not client:
        return {"success": False, "error": "Failed to initialize Twilio client. Check credentials."}
    
    try:
        logger.info(f"Sending test SMS to {to_phone_number}")
        
        message = client.messages.create(
            body="This is a test message from Calm Journey. If you're receiving this, SMS notifications are working correctly!",
            from_=from_phone,
            to=to_phone_number
        )
        
        logger.info(f"Test SMS sent successfully with SID: {message.sid}")
        return {"success": True, "message_sid": message.sid}
    
    except TwilioRestException as e:
        logger.error(f"Twilio error sending test SMS: {str(e)}")
        return {"success": False, "error": str(e)}
    
    except Exception as e:
        logger.error(f"Error sending test SMS: {str(e)}")
        return {"success": False, "error": str(e)}

def send_sms_to_user(user_id):
    """Send an SMS notification to a specific user."""
    with app.app_context():
        # Get the user
        user = User.query.get(user_id)
        
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return {"success": False, "error": f"User with ID {user_id} not found"}
        
        # Check if user has SMS notifications enabled and a phone number
        if not user.sms_notifications_enabled:
            logger.warning(f"User {user.username} (ID: {user_id}) has SMS notifications disabled")
            return {"success": False, "error": "SMS notifications are disabled for this user"}
        
        if not user.phone_number:
            logger.warning(f"User {user.username} (ID: {user_id}) has no phone number")
            return {"success": False, "error": "User has no phone number"}
        
        # Send the SMS
        client, from_phone = get_twilio_client()
        
        if not client:
            return {"success": False, "error": "Failed to initialize Twilio client. Check credentials."}
        
        try:
            # Get the base URL from the app configuration or use a default
            if 'BASE_URL' in app.config and app.config['BASE_URL']:
                base_url = app.config['BASE_URL']
                journal_url = f"{base_url}/journal/new"
            else:
                # For deployed apps, use the REPL_ID to ensure we get the correct URL
                repl_id = os.environ.get('REPL_ID', None)
                repl_owner = os.environ.get('REPL_OWNER', None)
                
                if repl_id and repl_owner:
                    # Use the proper Replit deployed URL format
                    journal_url = f"https://{repl_owner}-calm-journey.replit.app/journal/new"
                else:
                    # Fallback to a relative URL only if running locally
                    journal_url = "/journal/new"
            
            # Create the message text
            message_text = f"Hello {user.username}! Take a moment to journal today. Writing can help reduce stress and gain clarity. Visit {journal_url} to write. - Calm Journey"
            
            # Send the message
            logger.info(f"Sending SMS to {user.username} ({user.phone_number})")
            
            message = client.messages.create(
                body=message_text,
                from_=from_phone,
                to=user.phone_number
            )
            
            logger.info(f"SMS sent successfully to {user.username} with SID: {message.sid}")
            return {"success": True, "message_sid": message.sid}
        
        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS to {user.username}: {str(e)}")
            return {"success": False, "error": str(e)}
        
        except Exception as e:
            logger.error(f"Error sending SMS to {user.username}: {str(e)}")
            return {"success": False, "error": str(e)}

def send_immediate_sms_to_all():
    """Send SMS notifications to all users with SMS notifications enabled."""
    with app.app_context():
        # Get all users with SMS notifications enabled and a phone number
        users = User.query.filter(
            User.sms_notifications_enabled == True,
            User.phone_number != None,
            User.phone_number != ''
        ).all()
        
        if not users:
            logger.warning("No users with SMS notifications enabled and phone numbers found")
            return {"success_count": 0, "failure_count": 0, "error": "No eligible users found"}
        
        logger.info(f"Sending SMS notifications to {len(users)} users")
        
        success_count = 0
        failure_count = 0
        
        for user in users:
            result = send_sms_to_user(user.id)
            
            if result.get("success"):
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(f"SMS notification sending complete. Success: {success_count}, Failures: {failure_count}")
        return {"success_count": success_count, "failure_count": failure_count}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If an argument is provided, it's either a user ID or a phone number for testing
        arg = sys.argv[1]
        
        try:
            # Try to parse as user ID
            user_id = int(arg)
            print(f"Sending SMS to user with ID {user_id}")
            with app.app_context():
                result = send_sms_to_user(user_id)
                if result.get("success"):
                    print("SMS sent successfully!")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
        except ValueError:
            # If it's not a valid integer, treat it as a phone number for testing
            print(f"Sending test SMS to phone number {arg}")
            result = test_sms(arg)
            if result.get("success"):
                print("Test SMS sent successfully!")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
    else:
        # No arguments, send to all users with SMS notifications enabled
        print("Sending SMS to all users with SMS notifications enabled")
        with app.app_context():
            result = send_immediate_sms_to_all()
            print(f"Success: {result['success_count']}, Failures: {result['failure_count']}")
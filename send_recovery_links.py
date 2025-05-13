"""
Send password recovery links to all existing users.
This allows users to regain access to their accounts without knowing their old passwords.
"""
import os
import sys
import logging
from app import app, db
from models import User
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_reset_token(email):
    """Generate a secure token for password reset"""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def send_password_reset(user, reset_url):
    """Send a password reset email to a user"""
    mail = Mail(app)
    msg = Message(
        'Recover Your Calm Journey Account',
        sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
        recipients=[user.email]
    )
    msg.body = f"""Hello,

We've updated our authentication system at Calm Journey. To regain access to your account and journal entries, please click the link below to reset your password:

{reset_url}

This link will expire in 24 hours.

If you didn't request this, you can safely ignore this email.

The Calm Journey Team
"""
    try:
        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {user.email}: {str(e)}")
        return False

def send_recovery_to_all_users():
    """Send recovery emails to all users with valid emails"""
    base_url = os.environ.get('BASE_URL', 'https://calmjourney.replit.app')
    recovery_route = '/reset-password/'
    
    with app.app_context():
        # Get all users with email addresses
        users = User.query.filter(User.email.isnot(None)).all()
        
        logging.info(f"Found {len(users)} users with email addresses")
        sent_count = 0
        error_count = 0
        
        for user in users:
            # Skip users with invalid emails
            if not user.email or '@' not in user.email:
                logging.warning(f"User {user.id} has invalid email: {user.email}")
                continue
                
            # Generate reset token and URL
            token = generate_reset_token(user.email)
            reset_url = f"{base_url}{recovery_route}{token}"
            
            # Send the email
            if send_password_reset(user, reset_url):
                sent_count += 1
                logging.info(f"Sent recovery email to {user.email}")
            else:
                error_count += 1
        
        logging.info(f"Completed sending {sent_count} recovery emails with {error_count} errors")
        return sent_count, error_count

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--run':
        sent, errors = send_recovery_to_all_users()
        print(f"Sent {sent} recovery emails with {errors} errors")
    else:
        print("This script will send password recovery emails to all users.")
        print("To run this script, use --run flag:")
        print("python send_recovery_links.py --run")
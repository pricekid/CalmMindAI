"""
Script to send an email to all users with the new basic login link to the app.
This script uses the improved_email_service module for reliable email delivery.
"""
import os
import sys
import logging
from app import app, db
from models import User
from improved_email_service import send_email

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_login_link_to_all_users(login_url=None):
    """
    Send an email with the new login URL to all users.
    
    Args:
        login_url: Optional custom URL for the login page. If not provided, 
                   a default URL will be used based on environment variables.
    
    Returns:
        dict: Statistics about the email sending process
    """
    with app.app_context():
        # Get all users (active accounts)
        users = User.query.all()
        
        if not users:
            logger.info("No users found in the database.")
            return {"success": 0, "errors": 0, "total": 0}
        
        logger.info(f"Sending login link to {len(users)} users...")
        
        success_count = 0
        error_count = 0
        
        # Get the base URL from the app configuration or use a default replit URL
        if login_url:
            # Use the provided URL
            url = login_url
        elif 'BASE_URL' in app.config and app.config['BASE_URL']:
            url = f"{app.config['BASE_URL']}/basic-login"
        else:
            # For deployed apps on Replit, use the standardized URL
            url = "https://calm-mind-ai-naturalarts.replit.app/basic-login"
        
        for user in users:
            subject = 'Important: New Login Link for Calm Journey'
            html_body = f"""
            <html>
            <body>
                <h2>Hello {user.username}!</h2>
                <p>We're reaching out to provide you with the new login link for the Calm Journey application.</p>
                <p>Please use the following link to access your account:</p>
                <p><a href="{url}" style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px;">Login to Calm Journey</a></p>
                <p>If the button above doesn't work, you can copy and paste this URL into your browser:</p>
                <p>{url}</p>
                <p>Thank you for being part of the Calm Journey community.</p>
                <p>Warm regards,<br>The Calm Journey Team</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Hello {user.username}!
            
            We're reaching out to provide you with the new login link for the Calm Journey application.
            
            Please use the following link to access your account:
            {url}
            
            Thank you for being part of the Calm Journey community.
            
            Warm regards,
            The Calm Journey Team
            """
            
            try:
                result = send_email(user.email, subject, html_body, text_body)
                
                if result.get("success"):
                    success_count += 1
                    logger.info(f"Sent login link to {user.email}")
                else:
                    error_count += 1
                    logger.error(f"Failed to send login link to {user.email}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                error_count += 1
                logger.error(f"Unexpected error sending to {user.email}: {str(e)}", exc_info=True)
        
        logger.info(f"Email sending complete. Success: {success_count}, Errors: {error_count}, Total Users: {len(users)}")
        return {"success": success_count, "errors": error_count, "total": len(users)}

def send_login_link_to_one_user(email, login_url=None):
    """
    Send an email with the login link to a specific user for testing.
    
    Args:
        email: Email address of the recipient
        login_url: Optional custom URL for the login page
    
    Returns:
        dict: Result with success flag and error message if applicable
    """
    with app.app_context():
        # Get the user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            error_msg = f"No user found with email: {email}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Get the base URL from the app configuration or use a default replit URL
        if login_url:
            # Use the provided URL
            url = login_url
        elif 'BASE_URL' in app.config and app.config['BASE_URL']:
            url = f"{app.config['BASE_URL']}/basic-login"
        else:
            # For deployed apps on Replit, use the standardized URL
            url = "https://calm-mind-ai-naturalarts.replit.app/basic-login"
        
        subject = 'Important: New Login Link for Calm Journey'
        html_body = f"""
        <html>
        <body>
            <h2>Hello {user.username}!</h2>
            <p>We're reaching out to provide you with the new login link for the Calm Journey application.</p>
            <p>Please use the following link to access your account:</p>
            <p><a href="{url}" style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px;">Login to Calm Journey</a></p>
            <p>If the button above doesn't work, you can copy and paste this URL into your browser:</p>
            <p>{url}</p>
            <p>Thank you for being part of the Calm Journey community.</p>
            <p>Warm regards,<br>The Calm Journey Team</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Hello {user.username}!
        
        We're reaching out to provide you with the new login link for the Calm Journey application.
        
        Please use the following link to access your account:
        {url}
        
        Thank you for being part of the Calm Journey community.
        
        Warm regards,
        The Calm Journey Team
        """
        
        try:
            return send_email(user.email, subject, html_body, text_body)
        except Exception as e:
            error_msg = f"Unexpected error sending to {user.email}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}

if __name__ == "__main__":
    # Check for command-line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python send_basic_login_link.py all [login_url]           - Send login link to all users")
        print("  python send_basic_login_link.py test <email> [login_url]  - Send login link to one user for testing")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "all":
        # Send to all users
        login_url = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"Sending login link to all users{'with custom URL: ' + login_url if login_url else ''}...")
        result = send_login_link_to_all_users(login_url)
        print(f"Successfully sent: {result['success']}/{result['total']} emails")
        print(f"Failed to send: {result['errors']}/{result['total']} emails")
        
    elif command == "test" and len(sys.argv) > 2:
        # Send to one user for testing
        email = sys.argv[2]
        login_url = sys.argv[3] if len(sys.argv) > 3 else None
        print(f"Sending test login link to {email}{'with custom URL: ' + login_url if login_url else ''}...")
        result = send_login_link_to_one_user(email, login_url)
        
        if result.get("success"):
            print(f"Successfully sent login link to {email}")
        else:
            print(f"Failed to send login link: {result.get('error', 'Unknown error')}")
            
    else:
        print("Invalid command")
        print("Usage:")
        print("  python send_basic_login_link.py all [login_url]          - Send login link to all users")
        print("  python send_basic_login_link.py test <email> [login_url] - Send login link to one user for testing")
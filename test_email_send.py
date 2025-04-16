"""
Test script to send an email and diagnose why scheduled emails aren't being sent.
"""
import os
import logging
import sys
import datetime
from notification_service import send_email, get_mail_config

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_email_connection():
    """Test the email connection and send a test email."""
    
    # First check mail configuration
    mail_config = get_mail_config()
    logger.info("Mail configuration:")
    for key in mail_config:
        if key == 'MAIL_PASSWORD':
            logger.info(f"{key}: {'Set' if mail_config[key] else 'Not set'}")
        else:
            logger.info(f"{key}: {mail_config[key]}")
    
    if not mail_config['MAIL_PASSWORD']:
        logger.error("MAIL_PASSWORD is not set. Cannot send email.")
        return False
    
    # Make sure environment variables are set
    if not os.environ.get('MAIL_SERVER'):
        os.environ['MAIL_SERVER'] = mail_config['MAIL_SERVER']
        logger.info(f"Set MAIL_SERVER environment variable to {mail_config['MAIL_SERVER']}")
    
    if not os.environ.get('MAIL_PORT'):
        os.environ['MAIL_PORT'] = str(mail_config['MAIL_PORT'])
        logger.info(f"Set MAIL_PORT environment variable to {mail_config['MAIL_PORT']}")
    
    # Attempt to send a test email
    recipient = "naturalarts@gmail.com"  # Use a valid recipient email
    subject = "Calm Journey - Test Email from Scheduler Debug"
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_body = f"""
    <html>
    <body>
        <h2>Calm Journey - Test Email</h2>
        <p>This is a test email sent at {current_time} to debug why scheduled emails are not being sent.</p>
        <p>If you're seeing this email, it means the email system is working!</p>
        <hr>
        <p><em>The Calm Journey Team</em></p>
    </body>
    </html>
    """
    
    text_body = f"""Calm Journey - Test Email
    
    This is a test email sent at {current_time} to debug why scheduled emails are not being sent.
    
    If you're seeing this email, it means the email system is working!
    
    The Calm Journey Team
    """
    
    logger.info(f"Attempting to send test email to {recipient}...")
    result = send_email(recipient, subject, html_body, text_body)
    
    if result.get('success'):
        logger.info("Test email sent successfully!")
        return True
    else:
        logger.error(f"Failed to send test email: {result.get('error')}")
        return False

def check_scheduler_status():
    """Check the status of the scheduler."""
    try:
        with open('scheduler.pid', 'r') as f:
            pid = f.read().strip()
            logger.info(f"Scheduler PID from file: {pid}")
        
        # Check if process is running
        import psutil
        try:
            process = psutil.Process(int(pid))
            logger.info(f"Scheduler process {pid} is running: {process.cmdline()}")
            return True
        except psutil.NoSuchProcess:
            logger.error(f"Scheduler process {pid} is not running!")
            return False
    except Exception as e:
        logger.error(f"Error checking scheduler status: {str(e)}")
        return False

def main():
    """Main function to test and diagnose email issues."""
    logger.info("=" * 80)
    logger.info("TESTING EMAIL SYSTEM")
    logger.info("=" * 80)
    
    # Check scheduler status
    logger.info("\nChecking scheduler status...")
    scheduler_running = check_scheduler_status()
    
    if not scheduler_running:
        logger.warning("Scheduler is not running! This could explain why no emails are being sent.")
    
    # Test email connection
    logger.info("\nTesting email connection...")
    email_working = test_email_connection()
    
    if email_working:
        logger.info("\nDiagnosis: Email system is working properly!")
        logger.info("The issue may be in the scheduler configuration or job execution.")
    else:
        logger.error("\nDiagnosis: Email system is NOT working properly!")
        logger.error("The issue is with the email configuration or connectivity.")
    
    logger.info("=" * 80)
    
    if email_working and not scheduler_running:
        logger.info("Recommended action: Restart the scheduler")
        return 1
    elif not email_working:
        logger.info("Recommended action: Fix email configuration")
        return 2
    else:
        logger.info("Recommended action: Check scheduler logs and job configuration")
        return 3

if __name__ == "__main__":
    sys.exit(main())
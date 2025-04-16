"""
Send out the morning emails that were missing.
This script will immediately send the daily emails that should have gone out this morning.
"""
import os
import sys
import logging
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_mail_config():
    """Ensure mail server configuration is set."""
    if not os.environ.get('MAIL_SERVER'):
        os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
        logger.info("Set MAIL_SERVER to smtp.gmail.com")
    
    if not os.environ.get('MAIL_PORT'):
        os.environ['MAIL_PORT'] = '587'
        logger.info("Set MAIL_PORT to 587")
    
    return True

def run_email_job():
    """Run the daily email job manually."""
    try:
        # Import the job function from scheduler
        from scheduler import safe_send_daily_reminder
        
        # Make sure environment variables are set
        ensure_mail_config()
        
        # Run the job function
        logger.info("Running the morning email notification job now...")
        result = safe_send_daily_reminder()
        
        if result and isinstance(result, dict):
            sent_count = result.get('sent_count', 0)
            skipped_count = result.get('skipped_count', 0)
            total_users = result.get('total_users', 0)
            
            logger.info(f"Email job completed successfully!")
            logger.info(f"Total users: {total_users}")
            logger.info(f"Emails sent: {sent_count}")
            logger.info(f"Users skipped: {skipped_count}")
            
            return True
        else:
            logger.error(f"Failed to run email job: {result}")
            return False
    except Exception as e:
        logger.error(f"Error running email job: {str(e)}")
        return False

def main():
    """Main function to send morning emails."""
    logger.info("=" * 80)
    logger.info("SENDING MORNING EMAILS")
    logger.info("=" * 80)
    
    success = run_email_job()
    
    if success:
        logger.info("The morning emails have been sent successfully!")
    else:
        logger.error("Failed to send the morning emails. Check the logs for details.")
    
    logger.info("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
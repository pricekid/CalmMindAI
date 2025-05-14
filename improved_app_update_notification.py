"""
Improved script to send app update notification to all users.
This informs users about the name change from Calm Journey to Dear Teddy
and requests them to reset their passwords.

Includes enhanced deliverability testing and logging.
"""
import os
import logging
import argparse
import time
import json
from datetime import datetime
from flask import render_template, Flask
from updated_notification_service import load_users

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up SendGrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Initialize Flask app for template rendering only
app = Flask(__name__)

# Constants
SENDER_EMAIL = "dearteddybb@gmail.com"
DELAY_BETWEEN_SENDS = 1.0  # seconds
MAX_EMAILS_PER_BATCH = 50
TEST_RECIPIENT = "teddy.leon@alumni.uwi.edu"  # Known working address for verification

def prepare_email_content():
    """Prepare the email content from the template"""
    with app.app_context():
        html_content = render_template('emails/app_update_notification.html')
        text_content = render_template('emails/app_update_notification.txt')
        return html_content, text_content

def save_email_status(email_id, recipient, status, status_code=None, error=None):
    """Save email sending status to a log file for tracking"""
    status_dir = "data/email_status"
    os.makedirs(status_dir, exist_ok=True)
    
    status_data = {
        "email_id": email_id,
        "recipient": recipient,
        "status": status,
        "status_code": status_code,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    filename = f"{status_dir}/email_{email_id}_{status}.json"
    with open(filename, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Email status saved to {filename}")

def send_update_notification(email, email_id=None, dry_run=True):
    """
    Send app update notification to a specific email with enhanced tracking.
    
    Args:
        email: Recipient's email address
        email_id: Unique identifier for this email
        dry_run: If True, only simulate sending (don't actually send)
        
    Returns:
        dict: Result with success status
    """
    if email_id is None:
        email_id = int(time.time())
    
    subject = "Important Update: Calm Journey is now Dear Teddy"
    html_content, text_content = prepare_email_content()
    
    if dry_run:
        logger.info(f"[DRY RUN] Would send notification to {email} (ID: {email_id})")
        return {"success": True, "dry_run": True, "email_id": email_id}
    
    try:
        # Get API key
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SendGrid API key not found in environment variables")
            save_email_status(email_id, email, "failed", error="API key not configured")
            return {"success": False, "error": "API key not configured", "email_id": email_id}
        
        # Create message
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=email,
            subject=subject,
            html_content=html_content
        )
        
        # Note: We're not using custom headers as they are not compatible with the current Mail object
        
        # Send email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        status_code = response.status_code
        logger.info(f"Email {email_id} sent to {email} with status code {status_code}")
        
        # Save status
        if status_code == 202:
            save_email_status(email_id, email, "sent", status_code=status_code)
            return {"success": True, "status_code": status_code, "email_id": email_id}
        else:
            save_email_status(email_id, email, "failed", status_code=status_code)
            return {"success": False, "status_code": status_code, "email_id": email_id}
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending email {email_id} to {email}: {error_msg}")
        save_email_status(email_id, email, "failed", error=error_msg)
        return {"success": False, "error": error_msg, "email_id": email_id}

def verify_delivery_to_test_recipient():
    """Send a verification email to our known working recipient"""
    logger.info(f"Sending verification email to known working address: {TEST_RECIPIENT}")
    
    verification_id = f"verify_{int(time.time())}"
    result = send_update_notification(TEST_RECIPIENT, email_id=verification_id, dry_run=False)
    
    if result.get('success'):
        logger.info(f"✓ Verification email {verification_id} sent successfully")
        return True
    else:
        logger.error(f"✗ Verification email failed: {result.get('error') or result.get('status_code')}")
        return False

def send_to_all_users(dry_run=True, delay=DELAY_BETWEEN_SENDS, preview_email=None):
    """
    Send app update notification to all users.
    
    Args:
        dry_run: If True, only simulate sending (don't actually send)
        delay: Delay between emails in seconds (to avoid rate limits)
        preview_email: If provided, only send to this email for preview
        
    Returns:
        dict: Result with success/failure counts
    """
    # Send preview if requested
    if preview_email:
        logger.info(f"Sending preview email to {preview_email}")
        
        # Save preview to a file for inspection
        html_content, text_content = prepare_email_content()
        preview_path = f"app_update_preview_{int(time.time())}.html"
        text_preview_path = f"app_update_preview_{int(time.time())}.txt"
        
        with open(preview_path, 'w') as f:
            f.write(html_content)
            
        with open(text_preview_path, 'w') as f:
            f.write(text_content)
        
        logger.info(f"HTML preview saved to {preview_path}")
        logger.info(f"Text preview saved to {text_preview_path}")
        
        preview_id = f"preview_{int(time.time())}"
        result = send_update_notification(preview_email, email_id=preview_id, dry_run=False)
        
        if result.get('success'):
            logger.info(f"✓ Preview sent successfully to {preview_email}")
        else:
            logger.error(f"✗ Failed to send preview to {preview_email}: {result.get('error')}")
        
        return {
            "success": result.get('success'),
            "preview_to": preview_email,
            "preview_file": preview_path
        }
    
    # Verify delivery to test recipient first
    if not dry_run:
        if not verify_delivery_to_test_recipient():
            logger.error("Verification email failed! Aborting batch send.")
            return {"success": False, "error": "Verification email failed"}
    
    # Load users from data store
    users = load_users()
    if not isinstance(users, list):
        logger.error("Failed to load users")
        return {"success": False, "error": "Failed to load users"}
    
    logger.info(f"Found {len(users)} users")
    
    # Apply safety limit for batch size
    active_users = [user for user in users if user.get('email')]
    if len(active_users) > MAX_EMAILS_PER_BATCH and not dry_run:
        logger.warning(f"Found {len(active_users)} active users, limiting to {MAX_EMAILS_PER_BATCH} for safety")
        active_users = active_users[:MAX_EMAILS_PER_BATCH]
    
    success_count = 0
    failure_count = 0
    skipped_count = 0
    results = []
    
    # Create batch ID for this run
    batch_id = int(time.time())
    
    for i, user in enumerate(users):
        # Skip users without email addresses
        if not user.get('email'):
            logger.warning(f"User {user.get('id')} has no email, skipping")
            skipped_count += 1
            continue
        
        email = user.get('email')
        user_id = user.get('id')
        
        # Create a unique email ID for tracking
        email_id = f"{batch_id}_{user_id}"
        
        # Log progress
        logger.info(f"Processing user {i+1}/{len(users)}: {email} (ID: {email_id})")
        
        # Send notification
        result = send_update_notification(email, email_id=email_id, dry_run=dry_run)
        
        results.append({
            'user_id': user_id,
            'email': email,
            'email_id': email_id,
            'success': result.get('success'),
            'error': result.get('error'),
            'status_code': result.get('status_code')
        })
        
        if result.get('success'):
            success_count += 1
            logger.info(f"✓ {'[DRY RUN] ' if dry_run else ''}Successfully sent to {email}")
        else:
            failure_count += 1
            logger.error(f"✗ Failed to send to {email}: {result.get('error')}")
        
        # Add delay between sends to avoid rate limits
        if i < len(users) - 1 and not dry_run:
            time.sleep(delay)
    
    # Save results to a batch report
    results_file = f"data/email_batches/batch_{batch_id}.json"
    os.makedirs("data/email_batches", exist_ok=True)
    
    batch_results = {
        "batch_id": batch_id,
        "success_count": success_count,
        "failure_count": failure_count,
        "skipped_count": skipped_count,
        "total_users": len(users),
        "dry_run": dry_run,
        "timestamp": datetime.utcnow().isoformat(),
        "results": results
    }
    
    with open(results_file, 'w') as f:
        json.dump(batch_results, f, indent=2)
    
    logger.info(f"Batch results saved to {results_file}")
    
    return batch_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send app update notification to users')
    parser.add_argument('--send', action='store_true', help='Actually send emails (default: dry run)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between sends in seconds')
    parser.add_argument('--preview', type=str, help='Send preview to this email only')
    parser.add_argument('--max-emails', type=int, default=50, help='Maximum number of emails to send in one batch')
    
    args = parser.parse_args()
    
    # Update globals from args
    DELAY_BETWEEN_SENDS = args.delay
    MAX_EMAILS_PER_BATCH = args.max_emails
    
    if args.preview:
        result = send_to_all_users(dry_run=not args.send, delay=args.delay, preview_email=args.preview)
        if result.get('success'):
            logger.info(f"Preview sent successfully to {args.preview}")
            logger.info(f"Preview saved to {result.get('preview_file')}")
        else:
            logger.error(f"Failed to send preview: {result}")
    else:
        result = send_to_all_users(dry_run=not args.send, delay=args.delay)
        
        logger.info("=" * 50)
        logger.info(f"{'ACTUAL SEND' if args.send else 'DRY RUN'} COMPLETED")
        logger.info(f"Success: {result['success_count']}")
        logger.info(f"Failure: {result['failure_count']}")
        logger.info(f"Skipped: {result['skipped_count']}")
        logger.info(f"Total users: {result['total_users']}")
        logger.info("=" * 50)
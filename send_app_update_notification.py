"""
Script to send app update notification to all users.
This informs users about the name change from Calm Journey to Dear Teddy
and requests them to reset their passwords.
"""
import os
import logging
import argparse
import time
from datetime import datetime
from flask import render_template, Flask
from updated_notification_service import send_email, load_users

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app for template rendering only
app = Flask(__name__)

def prepare_email_content():
    """Prepare the email content from the template"""
    with app.app_context():
        html_content = render_template('emails/app_update_notification.html')
        text_content = render_template('emails/app_update_notification.txt')
        return html_content, text_content

def send_update_notification(email, dry_run=True):
    """
    Send app update notification to a specific email.
    
    Args:
        email: Recipient's email address
        dry_run: If True, only simulate sending (don't actually send)
        
    Returns:
        dict: Result with success status
    """
    subject = "Important Update: Calm Journey is now Dear Teddy"
    html_content, text_content = prepare_email_content()
    
    if dry_run:
        logger.info(f"[DRY RUN] Would send notification to {email}")
        return {"success": True, "dry_run": True}
    
    return send_email(email, subject, html_content, text_content)

def send_to_all_users(dry_run=True, delay=1, preview_email=None):
    """
    Send app update notification to all users.
    
    Args:
        dry_run: If True, only simulate sending (don't actually send)
        delay: Delay between emails in seconds (to avoid rate limits)
        preview_email: If provided, only send to this email for preview
        
    Returns:
        dict: Result with success/failure counts
    """
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
        
        result = send_update_notification(preview_email, dry_run=False)
        
        if result.get('success'):
            logger.info(f"✓ Preview sent successfully to {preview_email}")
        else:
            logger.error(f"✗ Failed to send preview to {preview_email}: {result.get('error')}")
        
        return {
            "success": result.get('success'),
            "preview_to": preview_email,
            "preview_file": preview_path
        }
    
    # Load users from data store
    users = load_users()
    if not isinstance(users, list):
        logger.error("Failed to load users")
        return {"success": False, "error": "Failed to load users"}
    
    logger.info(f"Found {len(users)} users")
    
    success_count = 0
    failure_count = 0
    skipped_count = 0
    results = []
    
    for i, user in enumerate(users):
        # Skip users without email addresses
        if not user.get('email'):
            logger.warning(f"User {user.get('id')} has no email, skipping")
            skipped_count += 1
            continue
        
        email = user.get('email')
        
        # Log progress
        logger.info(f"Processing user {i+1}/{len(users)}: {email}")
        
        # Send notification
        result = send_update_notification(email, dry_run=dry_run)
        
        results.append({
            'user_id': user.get('id'),
            'email': email,
            'success': result.get('success'),
            'error': result.get('error')
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
    
    return {
        "success_count": success_count,
        "failure_count": failure_count,
        "skipped_count": skipped_count,
        "total_users": len(users),
        "dry_run": dry_run,
        "timestamp": datetime.utcnow().isoformat(),
        "results": results
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send app update notification to users')
    parser.add_argument('--send', action='store_true', help='Actually send emails (default: dry run)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between sends in seconds')
    parser.add_argument('--preview', type=str, help='Send preview to this email only')
    
    args = parser.parse_args()
    
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
"""
Fallback email functionality for when SendGrid is not available.
This module provides a simple fallback mechanism to log emails that would be sent.
"""
import logging
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_fallback_directory():
    """Ensure the fallback directory exists"""
    if not os.path.exists('data/fallback_emails'):
        os.makedirs('data/fallback_emails', exist_ok=True)

def save_fallback_email(recipient, subject, content, email_type="general"):
    """
    Save an email that would have been sent to a fallback file.
    
    Args:
        recipient: The intended recipient's email address
        subject: The email subject
        content: The email content (HTML)
        email_type: The type of email (password_reset, notification, etc.)
    
    Returns:
        str: Path to the saved fallback email file
    """
    ensure_fallback_directory()
    
    # Create a timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"data/fallback_emails/{email_type}_{timestamp}_{recipient.replace('@', '_at_')}.json"
    
    # Save the email details to a file
    email_data = {
        "recipient": recipient,
        "subject": subject,
        "content": content,
        "type": email_type,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(filename, 'w') as f:
        json.dump(email_data, f, indent=2)
    
    logger.info(f"[FALLBACK] Email saved to {filename}")
    
    # Also log to console for visibility during debugging
    print(f"\n==== FALLBACK EMAIL ({email_type}) ====")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print(f"Saved to: {filename}")
    print("============================\n")
    
    return filename

def get_recent_emails(limit=10):
    """
    Get the most recent fallback emails.
    
    Args:
        limit: Maximum number of emails to return
        
    Returns:
        list: List of email details
    """
    ensure_fallback_directory()
    
    email_files = []
    for root, _, files in os.walk('data/fallback_emails'):
        for file in files:
            if file.endswith('.json'):
                email_files.append(os.path.join(root, file))
    
    # Sort by modification time (newest first)
    email_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Load email details from files
    emails = []
    for file in email_files[:limit]:
        try:
            with open(file, 'r') as f:
                email_data = json.load(f)
                email_data['file'] = file
                emails.append(email_data)
        except Exception as e:
            logger.error(f"Error loading email from {file}: {str(e)}")
    
    return emails

def clear_fallback_emails():
    """Clear all fallback emails"""
    ensure_fallback_directory()
    
    for root, _, files in os.walk('data/fallback_emails'):
        for file in files:
            if file.endswith('.json'):
                os.remove(os.path.join(root, file))
    
    logger.info("Cleared all fallback emails")
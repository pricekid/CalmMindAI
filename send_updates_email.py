"""
Script to send a test email with the latest updates added to the Calm Journey app.
"""
import os
import logging
from notification_service import send_email

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_updates_email(recipient_email):
    """
    Send an email with the latest updates to the app.
    
    Args:
        recipient_email: Email address to send the test to
        
    Returns:
        dict: Result with success flag and error message if applicable
    """
    subject = "Calm Journey - Latest App Updates"
    
    html_body = """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="color: #5f9ea0; margin: 0;">Calm Journey</h1>
            <p style="font-size: 18px; margin: 5px 0 0;">Latest Application Updates</p>
        </div>
        
        <div style="padding: 20px; background-color: #fff; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #5f9ea0; border-bottom: 1px solid #eee; padding-bottom: 10px;">Recent Improvements</h2>
            
            <h3 style="color: #6495ed;">Enhanced Voice Experience</h3>
            <ul>
                <li><strong>Default Voice Change:</strong> We've updated the default voice from Alloy to Shimmer for a gentler, more optimistic tone that better matches Coach Mira's supportive personality.</li>
                <li><strong>Simplified Voice Options:</strong> We've focused exclusively on OpenAI's premium neural voices for the highest quality experience.</li>
                <li><strong>Improved Text-to-Speech:</strong> The TTS functionality now provides more natural-sounding audio for both journal entries and Mira's responses.</li>
            </ul>
            
            <h3 style="color: #6495ed;">User Interface Improvements</h3>
            <ul>
                <li><strong>Text Justification:</strong> Fixed journal entry text justification issues for better readability.</li>
                <li><strong>Streamlined Controls:</strong> Removed redundant "Read Aloud" buttons in favor of the higher-quality OpenAI TTS options.</li>
                <li><strong>Responsive Design:</strong> Improved layout works better across all device sizes.</li>
            </ul>
            
            <h3 style="color: #6495ed;">Email Notifications</h3>
            <ul>
                <li><strong>Improved Email System:</strong> Enhanced email notification reliability to ensure you receive important updates and reminders.</li>
                <li><strong>Direct Email Configuration:</strong> Redesigned the email system for more reliable delivery of notifications.</li>
            </ul>
            
            <p style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee;">
                We're constantly working to improve your Calm Journey experience. Thank you for being part of our community!
            </p>
            
            <p>
                <a href="https://calm-mind-ai-naturalarts.replit.app/journal/new" style="display: inline-block; background-color: #5f9ea0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px;">Create a New Journal Entry</a>
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
            <p>The Calm Journey Team</p>
            <p style="font-size: 10px;">
                If you'd like to update your notification preferences, you can do so in your account settings.
            </p>
        </div>
    </body>
    </html>
    """
    
    text_body = """Calm Journey - Latest App Updates

RECENT IMPROVEMENTS

Enhanced Voice Experience:
* Default Voice Change: We've updated the default voice from Alloy to Shimmer for a gentler, more optimistic tone that better matches Coach Mira's supportive personality.
* Simplified Voice Options: We've focused exclusively on OpenAI's premium neural voices for the highest quality experience.
* Improved Text-to-Speech: The TTS functionality now provides more natural-sounding audio for both journal entries and Mira's responses.

User Interface Improvements:
* Text Justification: Fixed journal entry text justification issues for better readability.
* Streamlined Controls: Removed redundant "Read Aloud" buttons in favor of the higher-quality OpenAI TTS options.
* Responsive Design: Improved layout works better across all device sizes.

Email Notifications:
* Improved Email System: Enhanced email notification reliability to ensure you receive important updates and reminders.
* Direct Email Configuration: Redesigned the email system for more reliable delivery of notifications.

We're constantly working to improve your Calm Journey experience. Thank you for being part of our community!

Visit https://calm-mind-ai-naturalarts.replit.app/journal/new to create a new journal entry.

The Calm Journey Team

--
If you'd like to update your notification preferences, you can do so in your account settings.
"""
    
    return send_email(recipient_email, subject, html_body, text_body)

def main():
    import sys
    print("Calm Journey - Send Updates Email")
    print("--------------------------------")
    
    if len(sys.argv) < 2:
        print("Usage: python3 send_updates_email.py [email_address]")
        return
    
    recipient = sys.argv[1]
    print(f"Sending updates email to {recipient}...")
    result = send_updates_email(recipient)
    
    if result["success"]:
        print("✅ Updates email sent successfully!")
    else:
        print(f"❌ Error sending email: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()

import os
from datetime import datetime
from app import app, db, mail
from models import User
from flask_mail import Message
import logging

JOURNALING_TIPS = [
    "Writing helps process emotions and reduce anxiety",
    "Regular journaling can improve mental clarity",
    "Track your progress and identify patterns",
    "Express yourself freely without judgment",
    "Build self-awareness through reflection"
]

def send_daily_reminder():
    # Send daily reminders to all users who have notifications enabled
    # Previously this was filtering by notification_time, but now we'll send to all users at 6 AM
    users = User.query.filter_by(
        notifications_enabled=True
    ).all()
    
    for user in users:
        try:
            msg = Message(
                'Time to Journal - Calm Journey',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            
            tip = JOURNALING_TIPS[datetime.now().day % len(JOURNALING_TIPS)]
            
            # Get the base URL from the app configuration or use a default replit URL
            if 'BASE_URL' in app.config and app.config['BASE_URL']:
                base_url = app.config['BASE_URL']
                journal_url = f"{base_url}/journal/new"
            else:
                # If BASE_URL isn't set, use the Replit domain if available
                replit_domain = os.environ.get('REPL_SLUG', None)
                if replit_domain:
                    journal_url = f"https://{replit_domain}.replit.app/journal/new"
                else:
                    # Fallback to a relative URL only if running locally
                    journal_url = "/journal/new"
                    
            # Log the URL for debugging
            logging.info(f"Generated journal URL: {journal_url}")
            
            msg.html = f"""
            <h2>Good morning {user.username}!</h2>
            <p>Take a moment to reflect and journal your thoughts today.</p>
            <p><strong>Daily Tip:</strong> {tip}</p>
            <p><a href="{journal_url}">Start Writing</a></p>
            """
            
            mail.send(msg)
            logging.info(f"Sent reminder to {user.email}")
            
        except Exception as e:
            logging.error(f"Failed to send reminder to {user.email}: {str(e)}")

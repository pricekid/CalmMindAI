
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
    # Since this is scheduled to run at 6:00 AM, we'll send to all users who have 
    # notifications enabled and have chosen 6:00 AM as their notification time
    target_time = datetime.strptime('06:00', '%H:%M').time()
    users = User.query.filter_by(
        notifications_enabled=True,
        notification_time=target_time
    ).all()
    
    for user in users:
        try:
            msg = Message(
                'Time to Journal - Calm Journey',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            
            tip = JOURNALING_TIPS[datetime.now().day % len(JOURNALING_TIPS)]
            
            msg.html = f"""
            <h2>Good morning {user.username}!</h2>
            <p>Take a moment to reflect and journal your thoughts today.</p>
            <p><strong>Daily Tip:</strong> {tip}</p>
            <p><a href="https://calm-journey.repl.co/journal/new">Start Writing</a></p>
            """
            
            mail.send(msg)
            logging.info(f"Sent reminder to {user.email}")
            
        except Exception as e:
            logging.error(f"Failed to send reminder to {user.email}: {str(e)}")

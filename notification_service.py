
from datetime import datetime
from app import app, db
from models import User
from flask_mail import Mail, Message
import logging

mail = Mail(app)

JOURNALING_TIPS = [
    "Writing helps process emotions and reduce anxiety",
    "Regular journaling can improve mental clarity",
    "Track your progress and identify patterns",
    "Express yourself freely without judgment",
    "Build self-awareness through reflection"
]

def send_daily_reminder():
    current_time = datetime.now().time()
    users = User.query.filter_by(
        notifications_enabled=True,
        notification_time=current_time.replace(minute=0, second=0, microsecond=0)
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

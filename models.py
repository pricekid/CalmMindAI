from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Email notification settings
    notifications_enabled = db.Column(db.Boolean, default=True)
    notification_time = db.Column(db.Time, default=datetime.strptime('09:00', '%H:%M').time())
    
    # SMS notification settings
    phone_number = db.Column(db.String(20), nullable=True)
    sms_notifications_enabled = db.Column(db.Boolean, default=False)
    
    # Relationships
    journal_entries = db.relationship('JournalEntry', backref='author', lazy='dynamic')
    mood_logs = db.relationship('MoodLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_weekly_summary(self):
        """Get mood summary for the past week"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_moods = self.mood_logs.filter(MoodLog.created_at >= week_ago).all()
        
        if not weekly_moods:
            return None
            
        avg_mood = sum(log.mood_score for log in weekly_moods) / len(weekly_moods)
        mood_trend = 'stable'
        if len(weekly_moods) >= 2:
            first_half = weekly_moods[:len(weekly_moods)//2]
            second_half = weekly_moods[len(weekly_moods)//2:]
            first_avg = sum(log.mood_score for log in first_half) / len(first_half)
            second_avg = sum(log.mood_score for log in second_half) / len(second_half)
            if second_avg - first_avg > 0.5:
                mood_trend = 'improving'
            elif first_avg - second_avg > 0.5:
                mood_trend = 'declining'
                
        return {
            'average_mood': round(avg_mood, 1),
            'number_of_logs': len(weekly_moods),
            'trend': mood_trend,
            'highest_mood': max(log.mood_score for log in weekly_moods),
            'lowest_mood': min(log.mood_score for log in weekly_moods)
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_analyzed = db.Column(db.Boolean, default=False)
    anxiety_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    # Using deferred=True will make this column not be loaded by default
    # Only when specifically accessed will SQLAlchemy try to load it
    from sqlalchemy.orm import deferred
    user_reflection = deferred(db.Column(db.Text, nullable=True))   # User's reflection to Mira's prompt
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    recommendations = db.relationship('CBTRecommendation', backref='journal_entry', lazy=True)
    
    def __repr__(self):
        return f'<JournalEntry {self.title}>'

class CBTRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thought_pattern = db.Column(db.String(255), nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=False)
    
    def __repr__(self):
        return f'<CBTRecommendation {self.id}>'

class MoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<MoodLog {self.mood_score}>'

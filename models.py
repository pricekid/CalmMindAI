from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import deferred, load_only
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import UniqueConstraint

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile information from Replit Auth
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    profile_image_url = db.Column(db.String(256), nullable=True)
    
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
    __tablename__ = "journal_entry"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_analyzed = db.Column(db.Boolean, default=False)
    anxiety_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    
    # Conversation fields
    initial_insight = db.Column(db.Text, nullable=True)  # Mira's first analysis
    user_reflection = db.Column(db.Text, nullable=True, info={'deferred': True})  # User's first reflection
    followup_insight = db.Column(db.Text, nullable=True)  # Mira's second insight
    second_reflection = db.Column(db.Text, nullable=True, info={'deferred': True})  # User's second reflection
    closing_message = db.Column(db.Text, nullable=True)  # Mira's closing statement
    conversation_complete = db.Column(db.Boolean, default=False)  # Track if conversation is done
    
    # Foreign key
    user_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    recommendations = db.relationship('CBTRecommendation', backref='journal_entry', lazy=True)
    
    def __repr__(self):
        return f'<JournalEntry {self.title}>'

class CBTRecommendation(db.Model):
    __tablename__ = "cbt_recommendation"
    id = db.Column(db.Integer, primary_key=True)
    thought_pattern = db.Column(db.String(255), nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=False)
    
    def __repr__(self):
        return f'<CBTRecommendation {self.id}>'

class MoodLog(db.Model):
    __tablename__ = "mood_log"
    id = db.Column(db.Integer, primary_key=True)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<MoodLog {self.mood_score}>'

# Required for Replit Auth - OAuth model for storing tokens
class FlaskDanceOAuth(OAuthConsumerMixin, db.Model):
    __tablename__ = "flask_dance_oauth"
    # Override the mixin's tablename
    
    user_id = db.Column(db.String, db.ForeignKey("user.id"))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Dear Teddy - Core Components Export

## Key Application Files

### 1. Main Application Files

#### app.py - Core Flask Application
```python
import os
import logging
from flask import Flask, render_template, request, redirect, flash, session
from flask_login import LoginManager, current_user
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the database
db.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Import models after app initialization
with app.app_context():
    import models
    db.create_all()
```

#### models.py - Database Models
```python
import uuid
from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import deferred, load_only
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import UniqueConstraint

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile information
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    profile_image_url = db.Column(db.String(256), nullable=True)
    
    # Notification settings
    notifications_enabled = db.Column(db.Boolean, default=True)
    notification_time = db.Column(db.Time, default=datetime.strptime('09:00', '%H:%M').time())
    morning_reminder_enabled = db.Column(db.Boolean, default=True)
    morning_reminder_time = db.Column(db.Time, default=datetime.strptime('08:00', '%H:%M').time())
    evening_reminder_enabled = db.Column(db.Boolean, default=True)
    evening_reminder_time = db.Column(db.Time, default=datetime.strptime('20:00', '%H:%M').time())
    
    # SMS settings
    phone_number = db.Column(db.String(20), nullable=True)
    sms_notifications_enabled = db.Column(db.Boolean, default=False)
    
    # UI state
    welcome_message_shown = db.Column(db.Boolean, default=False)
    
    # Demographics for AI personalization
    age_range = db.Column(db.String(20), nullable=True)
    relationship_status = db.Column(db.String(50), nullable=True)
    has_children = db.Column(db.Boolean, nullable=True)
    life_focus = db.Column(db.Text, nullable=True)
    
    # Relationships
    journal_entries = db.relationship('JournalEntry', backref='author', lazy='dynamic')
    mood_logs = db.relationship('MoodLog', backref='user', lazy='dynamic')
    push_subscriptions = db.relationship('PushSubscription', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class JournalEntry(db.Model):
    __tablename__ = "journal_entry"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_analyzed = db.Column(db.Boolean, default=False)
    anxiety_level = db.Column(db.Integer, nullable=True)
    
    # Multi-turn conversation fields
    initial_insight = db.Column(db.Text, nullable=True)
    user_reflection = db.Column(db.Text, nullable=True)
    followup_insight = db.Column(db.Text, nullable=True)
    second_reflection = db.Column(db.Text, nullable=True)
    closing_message = db.Column(db.Text, nullable=True)
    conversation_complete = db.Column(db.Boolean, default=False)
    
    user_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    
    recommendations = db.relationship('CBTRecommendation', backref='journal_entry', lazy=True)

class CBTRecommendation(db.Model):
    __tablename__ = "cbt_recommendation"
    id = db.Column(db.Integer, primary_key=True)
    thought_pattern = db.Column(db.String(255), nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=False)

class MoodLog(db.Model):
    __tablename__ = "mood_log"
    id = db.Column(db.Integer, primary_key=True)
    mood_score = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
```

### 2. AI Integration Components

#### journal_service.py - OpenAI Integration
```python
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_therapeutic_response(entry_content, anxiety_level, user_demographics=None):
    """Generate initial therapeutic response using OpenAI GPT-4o"""
    
    # Build context from user demographics
    context = build_user_context(user_demographics)
    
    prompt = f"""You are Mira, an emotionally intelligent CBT-based journaling coach. 
    
    User context: {context}
    
    The user has shared: "{entry_content}"
    Their anxiety level is: {anxiety_level}/10
    
    Provide a warm, empathetic response that:
    1. Validates their feelings
    2. Offers CBT-based insights
    3. Suggests practical coping strategies
    4. Asks a thoughtful follow-up question
    
    Keep response to 150-200 words. Be supportive and professional."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def generate_followup_response(original_entry, user_reflection, user_demographics=None):
    """Generate follow-up response based on user's reflection"""
    
    context = build_user_context(user_demographics)
    
    prompt = f"""Continue as Mira, the CBT-based journaling coach.
    
    User context: {context}
    
    Original entry: "{original_entry}"
    User's reflection: "{user_reflection}"
    
    Provide a thoughtful follow-up that:
    1. Acknowledges their reflection
    2. Builds on their insights
    3. Offers deeper therapeutic guidance
    4. Suggests next steps for growth
    
    Keep response to 150-200 words."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def build_user_context(demographics):
    """Build personalized context from user demographics"""
    if not demographics:
        return "No specific demographic information provided."
    
    context_parts = []
    
    if demographics.get('age_range'):
        context_parts.append(f"Age range: {demographics['age_range']}")
    
    if demographics.get('relationship_status'):
        context_parts.append(f"Relationship status: {demographics['relationship_status']}")
    
    if demographics.get('has_children'):
        context_parts.append("Has children" if demographics['has_children'] else "No children")
    
    if demographics.get('life_focus'):
        context_parts.append(f"Life focus: {demographics['life_focus']}")
    
    return "; ".join(context_parts) if context_parts else "No specific demographic information provided."
```

### 3. Notification Services

#### email_service.py - SendGrid Integration
```python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_journal_reminder(user_email, user_name=None):
    """Send journal reminder email via SendGrid"""
    
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        raise ValueError("SendGrid API key not configured")
    
    sg = SendGridAPIClient(api_key)
    
    subject = "Time for your daily reflection with Dear Teddy"
    
    html_content = f"""
    <html>
    <body>
        <h2>Hello {user_name or 'there'}!</h2>
        <p>It's time for your daily check-in with Mira, your AI journaling companion.</p>
        <p>Taking a few minutes to reflect can help you process your thoughts and emotions.</p>
        <a href="https://your-app-url.com/new-entry" style="background-color: #4CAF50; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px;">Start Journaling</a>
        <p>Remember, every small step toward self-awareness is valuable.</p>
        <p>With care,<br>Your Dear Teddy Team</p>
    </body>
    </html>
    """
    
    message = Mail(
        from_email='noreply@dearteddy.com',
        to_emails=user_email,
        subject=subject,
        html_content=html_content
    )
    
    try:
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def send_welcome_email(user_email, user_name=None):
    """Send welcome email to new users"""
    
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        return False
    
    sg = SendGridAPIClient(api_key)
    
    subject = "Welcome to Dear Teddy - Your Mental Wellness Journey Begins"
    
    html_content = f"""
    <html>
    <body>
        <h2>Welcome to Dear Teddy, {user_name or 'friend'}!</h2>
        <p>We're so glad you've joined our community focused on mental wellness and personal growth.</p>
        <p>Here's what you can expect:</p>
        <ul>
            <li>🤖 Conversations with Mira, your AI therapist companion</li>
            <li>📊 Mood tracking and progress insights</li>
            <li>💡 Personalized CBT-based recommendations</li>
            <li>🔔 Gentle reminders to check in with yourself</li>
        </ul>
        <a href="https://your-app-url.com/dashboard" style="background-color: #4CAF50; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px;">Get Started</a>
        <p>Remember, this is your safe space for reflection and growth.</p>
    </body>
    </html>
    """
    
    message = Mail(
        from_email='welcome@dearteddy.com',
        to_emails=user_email,
        subject=subject,
        html_content=html_content
    )
    
    try:
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"Welcome email failed: {e}")
        return False
```

#### sms_service.py - Twilio Integration
```python
import os
from twilio.rest import Client

def send_sms_reminder(phone_number, user_name=None):
    """Send SMS reminder via Twilio"""
    
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, from_number]):
        raise ValueError("Twilio credentials not properly configured")
    
    client = Client(account_sid, auth_token)
    
    message_body = f"Hi {user_name or 'there'}! 🌟 Time for your daily reflection with Dear Teddy. Take a moment to check in with yourself today. https://your-app-url.com/new-entry"
    
    try:
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return False
```

### 4. Text-to-Speech Service

#### tts_service.py - Azure TTS Integration
```python
import os
import azure.cognitiveservices.speech as speechsdk

def generate_speech(text, voice_name="en-US-AriaNeural", output_file=None):
    """Generate speech using Azure Cognitive Services"""
    
    speech_key = os.environ.get('AZURE_SPEECH_KEY')
    speech_region = os.environ.get('AZURE_SPEECH_REGION')
    
    if not speech_key or not speech_region:
        raise ValueError("Azure Speech credentials not configured")
    
    # Configure speech service
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = voice_name
    
    # Set output format
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    
    if output_file:
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
    else:
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    
    # Create synthesizer
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    # Generate SSML for more natural speech
    ssml = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="{voice_name}">
            <prosody rate="0.9" pitch="+2Hz">
                {text}
            </prosody>
        </voice>
    </speak>
    """
    
    try:
        result = synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return True
        else:
            print(f"Speech synthesis failed: {result.reason}")
            return False
            
    except Exception as e:
        print(f"TTS generation failed: {e}")
        return False

# Available voice options
AVAILABLE_VOICES = {
    'aria': 'en-US-AriaNeural',
    'jenny': 'en-US-JennyNeural',
    'guy': 'en-US-GuyNeural',
    'jane': 'en-US-JaneNeural'
}
```

### 5. Form Definitions

#### forms.py - WTForms Configuration
```python
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange

class OnboardingDemographicsForm(FlaskForm):
    age_range = SelectField('Age Range', choices=[
        ('', 'Prefer not to say'),
        ('18-24', '18-24'),
        ('25-34', '25-34'),
        ('35-44', '35-44'),
        ('45-54', '45-54'),
        ('55-64', '55-64'),
        ('65+', '65+')
    ])
    
    relationship_status = SelectField('Relationship Status', choices=[
        ('', 'Prefer not to say'),
        ('single', 'Single'),
        ('relationship', 'In a relationship'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed')
    ])
    
    has_children = SelectField('Do you have children?', choices=[
        ('', 'Prefer not to say'),
        ('yes', 'Yes'),
        ('no', 'No')
    ])
    
    life_focus = SelectField('What\'s your primary life focus right now?', choices=[
        ('', 'Prefer not to say'),
        ('career', 'Career and professional growth'),
        ('family', 'Family and relationships'),
        ('health', 'Health and wellness'),
        ('education', 'Education and learning'),
        ('creativity', 'Creative pursuits'),
        ('spirituality', 'Spiritual growth'),
        ('financial', 'Financial security'),
        ('adventure', 'Travel and new experiences')
    ])
    
    submit = SubmitField('Continue to Dear Teddy')

class JournalEntryForm(FlaskForm):
    content = TextAreaField('What\'s on your mind today?', 
                           validators=[DataRequired(), Length(min=10, max=5000)],
                           render_kw={"placeholder": "Share your thoughts, feelings, or what's happening in your life...", "rows": 8})
    
    anxiety_level = SelectField('How would you rate your anxiety level today?', 
                               choices=[(str(i), f'{i} - {"Very calm" if i <= 2 else "Mild anxiety" if i <= 4 else "Moderate anxiety" if i <= 6 else "High anxiety" if i <= 8 else "Very anxious"}') for i in range(1, 11)],
                               validators=[DataRequired()])
    
    submit = SubmitField('Share with Mira')

class UserReflectionForm(FlaskForm):
    reflection = TextAreaField('Your thoughts on Mira\'s response',
                              validators=[DataRequired(), Length(min=5, max=2000)],
                              render_kw={"placeholder": "How does this resonate with you? What additional thoughts or feelings come up?", "rows": 5})
    
    submit = SubmitField('Continue Conversation')

class MoodLogForm(FlaskForm):
    mood_score = SelectField('How are you feeling today?',
                            choices=[(str(i), f'{i} - {"Very low" if i <= 2 else "Low" if i <= 4 else "Neutral" if i <= 6 else "Good" if i <= 8 else "Very good"}') for i in range(1, 11)],
                            validators=[DataRequired()])
    
    notes = TextAreaField('Any additional notes about your mood?',
                         render_kw={"placeholder": "Optional: What contributed to this mood?", "rows": 3})
    
    submit = SubmitField('Log Mood')
```

This export provides all the core components needed to recreate the Dear Teddy application on any platform. Each component is self-contained and can be adapted to different deployment environments while maintaining the core functionality.
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, BooleanField, TelField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional, Regexp
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        # Convert to lowercase for case-insensitive email matching
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class JournalEntryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=120)])
    content = TextAreaField('What\'s on your mind today?', validators=[DataRequired()])
    anxiety_level = IntegerField('Anxiety Level (1-10)', validators=[NumberRange(min=1, max=10)])
    submit = SubmitField('Save Entry')

class MoodLogForm(FlaskForm):
    mood_score = IntegerField('Current Mood (1-10)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    notes = TextAreaField('Notes (optional)')
    submit = SubmitField('Log Mood')

class AccountUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    # Email notification settings
    notifications_enabled = BooleanField('Enable Email Notifications')
    
    # SMS notification settings
    phone_number = TelField('Phone Number (with country code, e.g. +1234567890)', 
                           validators=[Optional(), 
                                      Regexp(r'^\+[1-9]\d{1,14}$', 
                                             message='Phone number must be in international format (e.g., +1234567890)')])
    sms_notifications_enabled = BooleanField('Enable SMS Notifications')
    
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Length(min=6)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Update Account')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if email.data.lower() != self.original_email.lower():
            # Convert to lowercase for case-insensitive email matching
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError('That email is already registered. Please use a different one.')

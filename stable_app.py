import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect, FlaskForm
from flask_wtf.csrf import validate_csrf
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
import uuid

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

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'stable_login'

# Simple User model
class User(db.Model):
    __tablename__ = "stable_user"
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Demographics
    age_range = db.Column(db.String(20), nullable=True)
    relationship_status = db.Column(db.String(50), nullable=True)
    has_children = db.Column(db.Boolean, nullable=True)
    life_focus = db.Column(db.Text, nullable=True)
    demographics_completed = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def is_authenticated(self):
        return True
        
    def is_active(self):
        return True
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)

# Journal Entry model
class JournalEntry(db.Model):
    __tablename__ = "stable_journal"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    anxiety_level = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_response = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.String, db.ForeignKey('stable_user.id'), nullable=False)

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create Account')

class DemographicsForm(FlaskForm):
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
    life_focus = SelectField('Primary life focus', choices=[
        ('', 'Prefer not to say'),
        ('career', 'Career growth'),
        ('family', 'Family and relationships'),
        ('health', 'Health and wellness'),
        ('education', 'Education and learning'),
        ('creativity', 'Creative pursuits'),
        ('spirituality', 'Spiritual growth')
    ])
    submit = SubmitField('Continue')

class JournalForm(FlaskForm):
    content = TextAreaField('What\'s on your mind today?', validators=[DataRequired()])
    anxiety_level = SelectField('Anxiety Level (1-10)', choices=[(str(i), str(i)) for i in range(1, 11)])
    submit = SubmitField('Share with Mira')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if not current_user.demographics_completed:
            return redirect(url_for('demographics'))
        return redirect(url_for('dashboard'))
    return render_template('stable_landing.html')

@app.route('/stable-login', methods=['GET', 'POST'])
def stable_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('stable_login.html', form=form)

@app.route('/stable-signup', methods=['GET', 'POST'])
def stable_signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered')
            return render_template('stable_signup.html', form=form)
        
        user = User()
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('demographics'))
    return render_template('stable_signup.html', form=form)

@app.route('/demographics', methods=['GET', 'POST'])
@login_required
def demographics():
    if current_user.demographics_completed:
        return redirect(url_for('dashboard'))
        
    form = DemographicsForm()
    if form.validate_on_submit():
        current_user.age_range = form.age_range.data or None
        current_user.relationship_status = form.relationship_status.data or None
        current_user.has_children = form.has_children.data == 'yes' if form.has_children.data else None
        current_user.life_focus = form.life_focus.data or None
        current_user.demographics_completed = True
        db.session.commit()
        
        flash('Welcome to Dear Teddy! Your preferences help us provide better support.')
        return redirect(url_for('dashboard'))
    return render_template('stable_demographics.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    recent_entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).limit(5).all()
    return render_template('stable_dashboard.html', entries=recent_entries)

@app.route('/new-entry', methods=['GET', 'POST'])
@login_required
def new_entry():
    form = JournalForm()
    if form.validate_on_submit():
        entry = JournalEntry()
        entry.content = form.content.data
        entry.anxiety_level = int(form.anxiety_level.data)
        entry.user_id = current_user.id
        
        # Simple AI response placeholder
        entry.ai_response = generate_ai_response(form.content.data, form.anxiety_level.data, current_user)
        
        db.session.add(entry)
        db.session.commit()
        
        flash('Your journal entry has been saved and analyzed.')
        return redirect(url_for('view_entry', entry_id=entry.id))
    return render_template('stable_journal.html', form=form)

@app.route('/entry/<int:entry_id>')
@login_required
def view_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    return render_template('stable_entry.html', entry=entry)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def generate_ai_response(content, anxiety_level, user):
    """Generate a simple AI response based on user input and demographics"""
    
    # Personalization based on demographics
    context = ""
    if user.age_range:
        context += f"As someone in the {user.age_range} age range, "
    if user.relationship_status and user.relationship_status != '':
        context += f"being {user.relationship_status}, "
    if user.has_children:
        context += "as a parent, "
    if user.life_focus and user.life_focus != '':
        context += f"with a focus on {user.life_focus}, "
    
    # Basic response templates based on anxiety level
    anxiety = int(anxiety_level)
    
    if anxiety <= 3:
        base_response = "I'm glad to hear you're feeling relatively calm today. "
    elif anxiety <= 6:
        base_response = "I notice you're experiencing some anxiety. "
    else:
        base_response = "I can sense you're feeling quite anxious right now. "
    
    # Add personalized context
    if context:
        base_response += context.rstrip(", ") + " often brings unique perspectives to these feelings. "
    
    # Add supportive message
    base_response += "Remember that your feelings are valid, and it's okay to take things one step at a time. "
    
    # Add suggestion based on content keywords
    content_lower = content.lower()
    if any(word in content_lower for word in ['work', 'job', 'career']):
        base_response += "Consider taking short breaks during your workday to center yourself."
    elif any(word in content_lower for word in ['relationship', 'family', 'friend']):
        base_response += "Healthy communication and setting boundaries can be helpful in relationships."
    elif any(word in content_lower for word in ['stress', 'pressure', 'overwhelmed']):
        base_response += "Try the 4-7-8 breathing technique: breathe in for 4, hold for 7, exhale for 8."
    else:
        base_response += "What small step could you take today to care for yourself?"
    
    return base_response

# Create tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
"""
Routes for journal reminder settings and management.
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TimeField, SubmitField
from wtforms.validators import DataRequired, Optional
from app import db
from models import User
from csrf_utils import get_csrf_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
journal_reminder_bp = Blueprint('journal_reminder', __name__)

class JournalReminderForm(FlaskForm):
    """Form for journal reminder settings"""
    morning_reminder_enabled = BooleanField('Enable Morning Reminders')
    morning_reminder_time = TimeField('Morning Reminder Time', validators=[Optional()])
    
    evening_reminder_enabled = BooleanField('Enable Evening Reminders')
    evening_reminder_time = TimeField('Evening Reminder Time', validators=[Optional()])
    
    submit = SubmitField('Save Settings')

@journal_reminder_bp.route('/journal-reminder-settings', methods=['GET'])
@login_required
def journal_reminder_settings():
    """Show journal reminder settings page"""
    form = JournalReminderForm()
    
    # Pre-populate form with current settings if available
    if current_user.morning_reminder_time:
        form.morning_reminder_time.data = current_user.morning_reminder_time
    if current_user.evening_reminder_time:
        form.evening_reminder_time.data = current_user.evening_reminder_time
        
    form.morning_reminder_enabled.data = current_user.morning_reminder_enabled
    form.evening_reminder_enabled.data = current_user.evening_reminder_enabled
    
    return render_template('journal_reminder_settings.html', form=form, user=current_user)

@journal_reminder_bp.route('/save-journal-reminder-settings', methods=['POST'])
@login_required
def save_journal_reminder_settings():
    """Save journal reminder settings"""
    form = JournalReminderForm()
    
    if not form.validate_on_submit():
        flash('There was an error with your form submission. Please try again.', 'danger')
        return redirect(url_for('journal_reminder.journal_reminder_settings'))
    
    try:
        # Update user settings
        current_user.morning_reminder_enabled = 'morning_reminder_enabled' in request.form
        current_user.evening_reminder_enabled = 'evening_reminder_enabled' in request.form
        
        # Parse time inputs
        if request.form.get('morning_reminder_time'):
            time_str = request.form.get('morning_reminder_time')
            current_user.morning_reminder_time = datetime.strptime(time_str, '%H:%M').time()
            
        if request.form.get('evening_reminder_time'):
            time_str = request.form.get('evening_reminder_time')
            current_user.evening_reminder_time = datetime.strptime(time_str, '%H:%M').time()
        
        # Save changes
        db.session.commit()
        
        flash('Journal reminder settings saved successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error saving journal reminder settings: {e}")
        db.session.rollback()
        flash('An error occurred while saving your settings. Please try again.', 'danger')
    
    return redirect(url_for('journal_reminder.journal_reminder_settings'))

@journal_reminder_bp.route('/test-journal-reminder/<reminder_type>')
@login_required
def test_journal_reminder(reminder_type):
    """Send a test journal reminder immediately"""
    from journal_reminder_service import send_journal_reminder, get_random_prompt
    
    if reminder_type not in ['morning', 'evening']:
        flash('Invalid reminder type.', 'danger')
        return redirect(url_for('journal_reminder.journal_reminder_settings'))
    
    try:
        # Get a random prompt
        prompt = get_random_prompt(reminder_type)
        
        # Send the reminder
        send_journal_reminder(current_user, prompt, reminder_type)
        
        flash(f'Test {reminder_type} reminder sent! Check your notifications.', 'success')
        
    except Exception as e:
        logger.error(f"Error sending test journal reminder: {e}")
        flash('An error occurred while sending the test reminder.', 'danger')
    
    return redirect(url_for('journal_reminder.journal_reminder_settings'))
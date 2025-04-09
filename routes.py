from flask import render_template, url_for, flash, redirect, request, jsonify, abort
from flask_login import login_user, current_user, logout_user
from app import login_required
from app import app, db
from models import User, JournalEntry, CBTRecommendation, MoodLog
from forms import RegistrationForm, LoginForm, JournalEntryForm, MoodLogForm, AccountUpdateForm
from openai_service import analyze_journal_entry, generate_coping_statement
from werkzeug.security import check_password_hash
from sqlalchemy import desc
import logging
import traceback
import json
from datetime import datetime, timedelta

# Home page
@app.route('/')
def index():
    return render_template('index.html', title='Welcome to Calm Journey')

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Convert email to lowercase for case-insensitive matching
        user = User(username=form.username.data, email=form.email.data.lower())
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Intentionally remove the admin route check to fix the cycle
    # We'll rely on the login_manager.unauthorized_handler instead
    
    # Check if user is already logged in
    if current_user.is_authenticated:
        # If logged in as admin, redirect to admin dashboard
        if hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
            return redirect(url_for('admin.dashboard'))
        # Otherwise, go to the regular dashboard
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Convert email to lowercase for case-insensitive matching
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            # Don't redirect to admin pages from regular login
            if next_page and next_page.startswith('/admin'):
                flash('You need admin privileges to access that page.', 'warning')
                return redirect(url_for('dashboard'))
            return redirect(next_page if next_page and not next_page.startswith('/admin') else url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

# User logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Make sure we're not logged in as admin trying to access regular dashboard
    if hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
        return redirect(url_for('admin.dashboard'))
        
    # Get weekly mood summary
    weekly_summary = current_user.get_weekly_summary()
        
    # Get recent journal entries
    recent_entries = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(desc(JournalEntry.created_at)).limit(5).all()
    
    # Get mood data for chart (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    mood_logs = MoodLog.query.filter(
        MoodLog.user_id == current_user.id,
        MoodLog.created_at >= seven_days_ago
    ).order_by(MoodLog.created_at).all()
    
    # Format mood data for chart.js
    mood_dates = [log.created_at.strftime('%Y-%m-%d') for log in mood_logs]
    mood_scores = [log.mood_score for log in mood_logs]
    
    # Get latest journal entry for coping statement
    latest_entry = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(desc(JournalEntry.created_at)).first()
    
    # Default coping statement that doesn't require API
    coping_statement = "Mira suggests: Take a moment to breathe deeply. Remember that your thoughts don't define you, and this moment will pass."
    
    # Only try to get a personalized one if we have a journal entry
    if latest_entry:
        try:
            # Use a simplified version of the journal content for the coping statement
            context = latest_entry.title or "anxiety management"
            
            try:
                # Generate coping statement with improved error handling
                api_statement = generate_coping_statement(context)
                
                # Only use API statement if it's valid
                if api_statement and len(api_statement.strip()) > 10:
                    coping_statement = api_statement
                    
            except Exception as api_error:
                # Log the specific API error, but continue with default statement
                logging.error(f"OpenAI API error in dashboard: {str(api_error)}")
                
        except Exception as e:
            # Log any other errors but don't crash 
            logging.error(f"General error generating coping statement: {str(e)}")
    
    # Get form for mood logging
    mood_form = MoodLogForm()
    
    return render_template('dashboard.html', 
                          title='Dashboard',
                          recent_entries=recent_entries,
                          mood_dates=mood_dates,
                          mood_scores=mood_scores,
                          coping_statement=coping_statement,
                          mood_form=mood_form,
                          weekly_summary=weekly_summary)

# Redirect to journal list
@app.route('/journal')
@login_required
def journal():
    # Redirect to the journal blueprint route
    return redirect(url_for('journal_blueprint.journal_list'))
    
    # Get all entries for visualization (limiting to last 30 for performance)
    all_entries = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(desc(JournalEntry.created_at))\
        .limit(30).all()
    
    # Format the entry data for visualization
    journal_data = [{
        'id': entry.id,
        'title': entry.title,
        'anxiety_level': entry.anxiety_level,
        'created_at': entry.created_at.isoformat(),
        'content': entry.content[:100],  # Only send snippet for privacy/performance
        'is_analyzed': entry.is_analyzed
    } for entry in all_entries]
    
    # Calculate trend and statistics
    anxiety_avg = None
    anxiety_trend = None
    
    if all_entries:
        anxiety_levels = [entry.anxiety_level for entry in all_entries]
        anxiety_avg = sum(anxiety_levels) / len(anxiety_levels)
        
        # Calculate trend if we have enough entries
        if len(all_entries) >= 5:
            recent_entries = all_entries[:5]
            older_entries = all_entries[-5:] if len(all_entries) > 10 else all_entries[:5]
            
            recent_avg = sum(entry.anxiety_level for entry in recent_entries) / len(recent_entries)
            older_avg = sum(entry.anxiety_level for entry in older_entries) / len(older_entries)
            
            anxiety_trend = recent_avg - older_avg
    
    # Pass statistics to the template
    stats = {
        'total_entries': len(all_entries),
        'anxiety_avg': round(anxiety_avg, 1) if anxiety_avg is not None else None,
        'anxiety_trend': anxiety_trend
    }
    
    return render_template('journal.html', 
                          title='Journal', 
                          entries=entries, 
                          journal_data=journal_data,
                          stats=stats)

# Direct new journal entry page (no redirect)
@app.route('/journal/new', methods=['GET', 'POST'])
@login_required
def new_journal_entry():
    # Use blueprint function directly to avoid redirect loop
    from journal_routes import new_journal_entry as blueprint_new
    return blueprint_new()

# Direct view for journal entry (no redirect)
@app.route('/journal/<int:entry_id>')
@login_required
def view_journal_entry(entry_id):
    # Use blueprint function directly to avoid redirect loop
    from journal_routes import view_journal_entry as blueprint_view
    return blueprint_view(entry_id)

# Direct update for journal entry (no redirect)
@app.route('/journal/<int:entry_id>/update', methods=['GET', 'POST'])
@login_required
def update_journal_entry(entry_id):
    # Use blueprint function directly to avoid redirect loop
    from journal_routes import update_journal_entry as blueprint_update
    return blueprint_update(entry_id)

# Direct delete for journal entry (no redirect)
@app.route('/journal/<int:entry_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_journal_entry(entry_id):
    # Use blueprint function directly to avoid redirect loop
    from journal_routes import delete_journal_entry as blueprint_delete
    return blueprint_delete(entry_id)

# Breathing exercise page
@app.route('/breathing')
@login_required
def breathing():
    return render_template('breathing.html', title='Breathing Exercise')

# User account management
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    import logging, traceback, json
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Create the form first - before we do anything else
    form = None
    
    try:
        # Add detailed debug information for troubleshooting
        logging.debug("------ ACCOUNT SETTINGS DEBUG ------")
        logging.debug(f"Current user: {current_user.id} - {current_user.username}")
        
        # Log the request method
        logging.debug(f"Request method: {request.method}")
        if request.form:
            logging.debug(f"Form data present with {len(request.form)} fields")
        else:
            logging.debug("No form data present")
            
        # Create form with user's current data
        form = AccountUpdateForm(current_user.username, current_user.email)
        
        if form.validate_on_submit():
            try:
                # Verify current password with explicit debugging
                logging.debug("Checking password...")
                password_valid = current_user.check_password(form.current_password.data)
                logging.debug(f"Password valid: {password_valid}")
                
                if not password_valid:
                    flash('Current password is incorrect.', 'danger')
                    return render_template('account.html', title='Account', form=form)
                
                # Log before updating
                logging.debug(f"Updating user: {current_user.id}, {current_user.username}")
                
                # Handle form data with safety checks
                username = form.username.data
                email = form.email.data.lower() if form.email.data else current_user.email
                
                # Debug display the data being used
                logging.debug(f"New username: {username}")
                logging.debug(f"New email: {email}")
                
                # Update basic info
                current_user.username = username
                current_user.email = email
                
                # Update email notification settings with safety check
                current_user.notifications_enabled = bool(form.notifications_enabled.data)
                logging.debug(f"Email notifications: {current_user.notifications_enabled}")
                
                # Update SMS notification settings (handle potential None values)
                current_user.phone_number = form.phone_number.data if form.phone_number.data else None
                current_user.sms_notifications_enabled = bool(form.sms_notifications_enabled.data)
                logging.debug(f"Phone number: {current_user.phone_number}")
                logging.debug(f"SMS notifications: {current_user.sms_notifications_enabled}")
                
                # Update password if provided
                if form.new_password.data:
                    logging.debug("Setting new password")
                    current_user.set_password(form.new_password.data)
                
                db.session.commit()
                logging.debug("Account updated successfully")
                flash('Your account has been updated!', 'success')
                return redirect(url_for('account'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error updating account: {str(e)}")
                logging.error(traceback.format_exc())
                flash('There was an error updating your account. Please try again.', 'danger')
                return render_template('account.html', title='Account', form=form)
        
        elif request.method == 'GET':
            try:
                form.username.data = current_user.username
                form.email.data = current_user.email
                form.notifications_enabled.data = current_user.notifications_enabled
                form.phone_number.data = current_user.phone_number
                form.sms_notifications_enabled.data = current_user.sms_notifications_enabled
                logging.debug("Form populated with current user data for GET request")
            except Exception as e:
                logging.error(f"Error populating form data: {str(e)}")
                logging.error(traceback.format_exc())
        
        return render_template('account.html', title='Account', form=form)
    
    except json.decoder.JSONDecodeError as json_err:
        logging.error(f"JSON Decode Error in account page: {str(json_err)}")
        logging.error(traceback.format_exc())
        # Handle JSON error specifically
        error_message = f"Invalid JSON format detected: {str(json_err)}"
        return render_template('error.html', title="JSON Error", error=error_message, 
                              suggestion="This may be caused by corrupted data files. Please contact support.")
    
    except Exception as e:
        logging.error(f"Critical error in account page: {str(e)}")
        logging.error(traceback.format_exc())
        # Handle other errors
        if form is None:
            # If form creation failed, we need to create a blank one
            form = AccountUpdateForm("", "")
        
        error_message = f"An unexpected error occurred: {str(e)}"
        flash(error_message, 'danger')
        return render_template('account.html', title='Account', form=form)

# Log mood
@app.route('/log_mood', methods=['POST'])
@login_required
def log_mood():
    form = MoodLogForm()
    
    if form.validate_on_submit():
        mood_log = MoodLog(
            mood_score=form.mood_score.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        
        db.session.add(mood_log)
        db.session.commit()
        
        flash('Your mood has been logged!', 'success')
    else:
        flash('There was an error logging your mood. Please try again.', 'danger')
    
    return redirect(url_for('dashboard'))

# Direct API endpoint for getting coaching feedback
@app.route('/api/journal_coach/<int:entry_id>', methods=['GET', 'POST'])
@app.route('/api/journal-coach/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def api_journal_coach(entry_id):
    # Use blueprint function directly to avoid redirect loop
    from journal_routes import api_journal_coach as blueprint_coach
    return blueprint_coach(entry_id)

# Direct API endpoint for analyzing a journal entry
@app.route('/api/analyze_entry/<int:entry_id>', methods=['GET', 'POST'])
@app.route('/api/analyze-entry/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def api_analyze_entry(entry_id):
    # Use blueprint function directly to avoid redirect loop
    from journal_routes import api_analyze_entry as blueprint_analyze
    return blueprint_analyze(entry_id)

# Crisis Resources page
@app.route('/crisis')
def crisis():
    """
    Display mental health crisis resources in a calm, accessible format.
    This page is available to all users, whether logged in or not.
    """
    return render_template('crisis.html', title='Crisis Resources')

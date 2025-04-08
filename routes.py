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
    
    coping_statement = None
    if latest_entry:
        try:
            # Use a simplified version of the journal content for the coping statement
            context = latest_entry.title or "anxiety management"
            
            # Add a try-except block specifically for the API call
            try:
                # Generate coping statement with improved error handling
                coping_statement = generate_coping_statement(context)
                
                # Check for specific error messages in the response
                if coping_statement and any(err_type in coping_statement for err_type in ["API quota exceeded", "API_QUOTA_EXCEEDED"]):
                    # Add a flash message about API limits
                    flash('AI-generated coping statements are currently unavailable due to API usage limits.', 'info')
                
            except Exception as api_error:
                # Log the specific API error
                logging.error(f"OpenAI API error in dashboard: {str(api_error)}")
                
                # Use a fallback coping statement
                coping_statement = "Mira suggests: Take a moment to breathe deeply. Remember that your thoughts don't define you, and this moment will pass."
                
        except Exception as e:
            logging.error(f"General error generating coping statement: {str(e)}")
            
            # Provide a default statement that doesn't rely on API
            coping_statement = "In this moment of anxiety, remember that you have the tools and strength within you to navigate through these feelings."
    
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

# Journal entry list
@app.route('/journal')
@login_required
def journal():
    page = request.args.get('page', 1, type=int)
    entries = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(desc(JournalEntry.created_at))\
        .paginate(page=page, per_page=10)
    
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

# Create new journal entry
@app.route('/journal/new', methods=['GET', 'POST'])
@login_required
def new_journal_entry():
    form = JournalEntryForm()
    if form.validate_on_submit():
        # Save the journal entry immediately
        entry = JournalEntry(
            title=form.title.data,
            content=form.content.data,
            anxiety_level=form.anxiety_level.data,
            author=current_user,
            is_analyzed=False  # Start with is_analyzed=False, will be analyzed on view
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Redirect immediately after saving, analysis will happen when viewing the entry
        flash('Your journal entry has been saved! Analysis will be performed when you view the entry.', 'success')
        return redirect(url_for("journal.view_journal_entry", entry_id=entry.id))
    
    return render_template('journal_entry.html', title='New Journal Entry', 
                          form=form, legend='New Journal Entry')

# View journal entry
@app.route('/journal/<int:entry_id>')
@login_required
def view_journal_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)
    
    # If the entry hasn't been analyzed yet, analyze it now
    if not entry.is_analyzed:
        try:
            # Clear old recommendations if any
            CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()
            
            # Analyze the entry
            thought_patterns = analyze_journal_entry(entry.content, entry.anxiety_level)
            
            # Save the recommendations
            is_api_error = False
            is_config_error = False
            
            for pattern in thought_patterns:
                # Check for different error patterns
                if pattern["pattern"] == "API Quota Exceeded":
                    is_api_error = True
                elif pattern["pattern"] == "API Configuration Issue":
                    is_config_error = True
                
                # Save recommendation to database
                recommendation = CBTRecommendation(
                    thought_pattern=pattern["pattern"],
                    recommendation=f"{pattern['description']} - {pattern['recommendation']}",
                    journal_entry_id=entry.id
                )
                db.session.add(recommendation)
            
            entry.is_analyzed = True
            db.session.commit()
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error analyzing journal entry on view: {error_msg}")
            # We'll still show the entry without analysis
    
    # Generate coach response when viewing the entry
    coach_response = None
    try:
        from openai_service import generate_journaling_coach_response
        coach_response = generate_journaling_coach_response(entry)
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error generating automatic coach response: {error_msg}")
        
        # Provide different messages based on error type
        if "API_QUOTA_EXCEEDED" in error_msg:
            coach_response = "Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Remember that the act of journaling itself is a powerful tool for self-reflection and growth."
        elif "INVALID_API_KEY" in error_msg:
            coach_response = "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself."
        else:
            coach_response = None  # Use None to indicate we should still show the button
    
    # Add a flag to show the emergency call button when anxiety level is high (8 or higher)
    show_call_button = entry.anxiety_level >= 8
    
    return render_template('journal_entry.html', title=entry.title, 
                          entry=entry, view_only=True, coach_response=coach_response,
                          show_call_button=show_call_button)

# Update journal entry
@app.route('/journal/<int:entry_id>/update', methods=['GET', 'POST'])
@login_required
def update_journal_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)
    
    form = JournalEntryForm()
    if form.validate_on_submit():
        # Update the basic entry data
        entry.title = form.title.data
        entry.content = form.content.data
        entry.anxiety_level = form.anxiety_level.data
        entry.updated_at = datetime.utcnow()
        
        # Clear old recommendations
        CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()
        
        # Mark entry as not analyzed so it will be analyzed when viewed
        entry.is_analyzed = False
        
        # Save all changes
        db.session.commit()
        
        # Flash a message and redirect immediately
        flash('Your journal entry has been updated! Analysis will be performed when you view the entry.', 'success')
        
        # Redirect to view page - analysis will happen there
        return redirect(url_for("journal.view_journal_entry", entry_id=entry.id))
    
    elif request.method == 'GET':
        form.title.data = entry.title
        form.content.data = entry.content
        form.anxiety_level.data = entry.anxiety_level
    
    return render_template('journal_entry.html', title='Update Journal Entry', 
                          form=form, legend='Update Journal Entry')

# Delete journal entry - redirects to the blueprint route
@app.route('/journal/<int:entry_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_journal_entry(entry_id):
    # Directly handle the deletion here instead of redirecting
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)
    
    try:
        # Delete recommendations first (cascade doesn't work with SQLAlchemy without setup)
        CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()
        
        # Delete the entry from database
        db.session.delete(entry)
        db.session.commit()
        
        # Also delete from JSON storage to update insights/patterns
        from journal_service import delete_journal_entry as delete_json_entry
        delete_success = delete_json_entry(entry_id, current_user.id)
        
        flash('Your journal entry has been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting journal entry {entry_id}: {str(e)}")
        flash('An error occurred while deleting your journal entry. Please try again.', 'danger')
    
    return redirect(url_for('journal'))

# Breathing exercise page
@app.route('/breathing')
@login_required
def breathing():
    return render_template('breathing.html', title='Breathing Exercise')

# User account management
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = AccountUpdateForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('account.html', title='Account', form=form)
        
        current_user.username = form.username.data
        current_user.email = form.email.data.lower()
        
        # Update email notification settings
        current_user.notifications_enabled = form.notifications_enabled.data
        
        # Update SMS notification settings
        current_user.phone_number = form.phone_number.data
        current_user.sms_notifications_enabled = form.sms_notifications_enabled.data
        
        # Update password if provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
        
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.notifications_enabled.data = current_user.notifications_enabled
        form.phone_number.data = current_user.phone_number
        form.sms_notifications_enabled.data = current_user.sms_notifications_enabled
    
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

# API endpoint for getting coaching feedback
@app.route('/api/journal_coach/<int:entry_id>', methods=['POST'])
@login_required
def api_journal_coach(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized access'})
    
    try:
        from openai_service import generate_journaling_coach_response
        
        # Generate the coach response
        coach_response = generate_journaling_coach_response(entry)
        
        return jsonify({
            'success': True,
            'coach_response': coach_response
        })
        
    except Exception as e:
        app.logger.error(f"Error generating coach response: {str(e)}")
        
        # Return more specific error messages
        if "API_QUOTA_EXCEEDED" in str(e):
            return jsonify({
                'success': False,
                'status': 'API_LIMIT',
                'message': 'Coach feedback is currently unavailable due to API limits.'
            }), 429
        elif "INVALID_API_KEY" in str(e):
            return jsonify({
                'success': False,
                'status': 'CONFIG_ERROR',
                'message': 'Coach feedback is currently unavailable due to a configuration issue.'
            }), 500
        else:
            return jsonify({
                'success': False,
                'status': 'ERROR',
                'message': 'There was an error generating coach feedback. You can try again later.'
            }), 500

# API endpoint for analyzing a journal entry
@app.route('/api/analyze_entry/<int:entry_id>', methods=['POST'])
@login_required
def api_analyze_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)
    
    try:
        # Clear old recommendations
        CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()
        
        # Analyze the entry using OpenAI API
        thought_patterns = analyze_journal_entry(entry.content, entry.anxiety_level)
        
        # Save the recommendations
        is_api_error = False
        is_config_error = False
        
        for pattern in thought_patterns:
            # Check for different error patterns
            if pattern["pattern"] == "API Quota Exceeded":
                is_api_error = True
            elif pattern["pattern"] == "API Configuration Issue":
                is_config_error = True
                
            # Save recommendation to database
            recommendation = CBTRecommendation(
                thought_pattern=pattern["pattern"],
                recommendation=f"{pattern['description']} - {pattern['recommendation']}",
                journal_entry_id=entry.id
            )
            db.session.add(recommendation)
        
        entry.is_analyzed = True
        db.session.commit()
        
        # Return appropriate response based on error type
        if is_api_error:
            return jsonify({
                'success': True,
                'status': 'API_LIMIT',
                'message': 'Entry saved. AI analysis is currently unavailable due to API usage limits.',
                'recommendations': [{'pattern': r.thought_pattern, 'recommendation': r.recommendation} 
                                for r in entry.recommendations]
            })
        elif is_config_error:
            return jsonify({
                'success': True,
                'status': 'CONFIG_ERROR',
                'message': 'Entry saved. AI analysis is currently unavailable due to a configuration issue.',
                'recommendations': [{'pattern': r.thought_pattern, 'recommendation': r.recommendation} 
                                for r in entry.recommendations]
            })
        else:
            return jsonify({
                'success': True,
                'status': 'SUCCESS',
                'message': 'Entry analyzed successfully!',
                'recommendations': [{'pattern': r.thought_pattern, 'recommendation': r.recommendation} 
                                for r in entry.recommendations]
            })
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error analyzing journal entry: {error_msg}")
        
        # Save the entry even if analysis fails
        entry.is_analyzed = False
        db.session.commit()
        
        # Return more specific error messages
        if "API_QUOTA_EXCEEDED" in error_msg:
            return jsonify({
                'success': False,
                'status': 'API_LIMIT',
                'message': 'Your entry was saved, but AI analysis is currently unavailable due to API limits.'
            }), 429
        elif "INVALID_API_KEY" in error_msg:
            return jsonify({
                'success': False,
                'status': 'CONFIG_ERROR',
                'message': 'Your entry was saved, but AI analysis is currently unavailable due to a configuration issue.'
            }), 500
        else:
            return jsonify({
                'success': False,
                'status': 'ERROR',
                'message': 'Your entry was saved, but there was an error during analysis. You can try again later.'
            }), 500

# Crisis Resources page
@app.route('/crisis')
def crisis():
    """
    Display mental health crisis resources in a calm, accessible format.
    This page is available to all users, whether logged in or not.
    """
    return render_template('crisis.html', title='Crisis Resources')

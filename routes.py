from flask import render_template, url_for, flash, redirect, request, jsonify, abort
from flask_login import login_user, current_user, logout_user, login_required
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
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
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
        # Use a simplified version of the journal content for the coping statement
        context = latest_entry.title
        coping_statement = generate_coping_statement(context)
    
    # Get form for mood logging
    mood_form = MoodLogForm()
    
    return render_template('dashboard.html', 
                          title='Dashboard',
                          recent_entries=recent_entries,
                          mood_dates=mood_dates,
                          mood_scores=mood_scores,
                          coping_statement=coping_statement,
                          mood_form=mood_form)

# Journal entry list
@app.route('/journal')
@login_required
def journal():
    page = request.args.get('page', 1, type=int)
    entries = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(desc(JournalEntry.created_at))\
        .paginate(page=page, per_page=10)
    
    return render_template('journal.html', title='Journal', entries=entries)

# Create new journal entry
@app.route('/journal/new', methods=['GET', 'POST'])
@login_required
def new_journal_entry():
    form = JournalEntryForm()
    if form.validate_on_submit():
        entry = JournalEntry(
            title=form.title.data,
            content=form.content.data,
            anxiety_level=form.anxiety_level.data,
            author=current_user
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Analyze the entry using OpenAI
        try:
            thought_patterns = analyze_journal_entry(form.content.data, form.anxiety_level.data)
            
            # Save the recommendations
            for pattern in thought_patterns:
                recommendation = CBTRecommendation(
                    thought_pattern=pattern["pattern"],
                    recommendation=f"{pattern['description']} - {pattern['recommendation']}",
                    journal_entry_id=entry.id
                )
                db.session.add(recommendation)
            
            entry.is_analyzed = True
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Error analyzing journal entry: {str(e)}")
            flash('Entry saved, but analysis could not be completed. You can try analyzing it later.', 'warning')
        
        flash('Your journal entry has been created!', 'success')
        return redirect(url_for('view_journal_entry', entry_id=entry.id))
    
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
    
    return render_template('journal_entry.html', title=entry.title, 
                          entry=entry, view_only=True)

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
        entry.title = form.title.data
        entry.content = form.content.data
        entry.anxiety_level = form.anxiety_level.data
        entry.updated_at = datetime.utcnow()
        
        # Clear old recommendations
        CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()
        
        # Re-analyze the entry
        try:
            thought_patterns = analyze_journal_entry(form.content.data, form.anxiety_level.data)
            
            # Save the new recommendations
            for pattern in thought_patterns:
                recommendation = CBTRecommendation(
                    thought_pattern=pattern["pattern"],
                    recommendation=f"{pattern['description']} - {pattern['recommendation']}",
                    journal_entry_id=entry.id
                )
                db.session.add(recommendation)
            
            entry.is_analyzed = True
            
        except Exception as e:
            logging.error(f"Error analyzing journal entry: {str(e)}")
            entry.is_analyzed = False
            flash('Entry updated, but analysis could not be completed.', 'warning')
        
        db.session.commit()
        flash('Your journal entry has been updated!', 'success')
        return redirect(url_for('view_journal_entry', entry_id=entry.id))
    
    elif request.method == 'GET':
        form.title.data = entry.title
        form.content.data = entry.content
        form.anxiety_level.data = entry.anxiety_level
    
    return render_template('journal_entry.html', title='Update Journal Entry', 
                          form=form, legend='Update Journal Entry')

# Delete journal entry
@app.route('/journal/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_journal_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)
    
    # Delete associated recommendations first
    CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()
    
    # Delete the entry
    db.session.delete(entry)
    db.session.commit()
    
    flash('Your journal entry has been deleted!', 'success')
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
        current_user.email = form.email.data
        
        # Update password if provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
        
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
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
        
        # Analyze the entry
        thought_patterns = analyze_journal_entry(entry.content, entry.anxiety_level)
        
        # Save the recommendations
        for pattern in thought_patterns:
            recommendation = CBTRecommendation(
                thought_pattern=pattern["pattern"],
                recommendation=f"{pattern['description']} - {pattern['recommendation']}",
                journal_entry_id=entry.id
            )
            db.session.add(recommendation)
        
        entry.is_analyzed = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Entry analyzed successfully!',
            'recommendations': [{'pattern': r.thought_pattern, 'recommendation': r.recommendation} 
                              for r in entry.recommendations]
        })
        
    except Exception as e:
        logging.error(f"Error analyzing journal entry: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error analyzing entry. Please try again.'
        }), 500

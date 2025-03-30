from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user
from functools import wraps
from admin_models import Admin
from admin_forms import AdminLoginForm, AdminMessageForm, APIConfigForm

# Create a custom admin_required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated and is an admin
        if not current_user.is_authenticated or not isinstance(current_user._get_current_object(), Admin):
            flash('Please log in as admin to access this page.', 'danger')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
from admin_utils import (
    ensure_data_files_exist, get_admin_stats, export_journal_entries, 
    export_users, flag_journal_entry, is_entry_flagged, get_flagged_entries,
    save_admin_message, get_admin_messages, get_config, save_config
)
from models import User, JournalEntry, CBTRecommendation
from app import db
import logging
import traceback

# Set up logging
logger = logging.getLogger(__name__)

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Make sure data files exist
ensure_data_files_exist()

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login route"""
    try:
        logger.debug("Admin login route accessed")
        if current_user.is_authenticated:
            logger.debug("User already authenticated, redirecting to dashboard")
            return redirect(url_for('admin.dashboard'))
        
        form = AdminLoginForm()
        if form.validate_on_submit():
            logger.debug(f"Form submitted with username: {form.username.data}")
            # Check if it's our hardcoded admin
            if form.username.data == "admin":
                try:
                    admin = Admin.get(1)
                    logger.debug("Admin user retrieved")
                    
                    if admin and admin.check_password(form.password.data):
                        login_user(admin)
                        logger.debug("Admin login successful")
                        next_page = request.args.get('next')
                        return redirect(next_page if next_page else url_for('admin.dashboard'))
                    else:
                        logger.debug("Password check failed")
                        flash('Login unsuccessful. Please check your credentials.', 'danger')
                except Exception as e:
                    logger.error(f"Error retrieving admin: {str(e)}")
                    logger.error(traceback.format_exc())
                    flash('An error occurred. Please try again.', 'danger')
            else:
                logger.debug("Username is not admin")
                flash('Login unsuccessful. Please check your credentials.', 'danger')
        
        logger.debug("Rendering login template")
        return render_template('admin/login.html', title='Admin Login', form=form)
    except Exception as e:
        logger.error(f"Unhandled exception in admin login: {str(e)}")
        logger.error(traceback.format_exc())
        flash('An error occurred. Please try again.', 'danger')
        return render_template('admin/login.html', title='Admin Login', form=form)

@admin_bp.route('/logout')
@admin_required
def logout():
    """Admin logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    stats = get_admin_stats()
    
    # Export data to JSON files
    export_journal_entries()
    export_users()
    
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)

@admin_bp.route('/journals')
@admin_required
def journals():
    """View all journal entries"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Check if we should only show flagged entries
    show_flagged = request.args.get('flagged', 'false') == 'true'
    
    # Get all flagged journal IDs
    flagged_entries = get_flagged_entries()
    flagged_ids = [entry.get('journal_id') for entry in flagged_entries]
    
    # Query journal entries
    query = JournalEntry.query
    
    if show_flagged:
        query = query.filter(JournalEntry.id.in_(flagged_ids))
    
    entries = query.order_by(JournalEntry.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get user info for each entry
    users = {}
    for entry in entries.items:
        if entry.user_id not in users:
            user = User.query.get(entry.user_id)
            users[entry.user_id] = user.username if user else "Unknown"
    
    # Create a dict to track which entries are flagged
    is_flagged = {entry.id: entry.id in flagged_ids for entry in entries.items}
    
    return render_template('admin/journals.html', title='Journal Entries', 
                          entries=entries, users=users, is_flagged=is_flagged,
                          show_flagged=show_flagged)

@admin_bp.route('/journal/<int:journal_id>')
@admin_required
def view_journal(journal_id):
    """View a specific journal entry"""
    entry = JournalEntry.query.get_or_404(journal_id)
    
    # Get the user who wrote this entry
    user = User.query.get(entry.user_id)
    
    # Get CBT recommendations for this entry
    recommendations = CBTRecommendation.query.filter_by(journal_entry_id=entry.id).all()
    
    # Check if this entry is flagged
    flagged = is_entry_flagged(journal_id)
    
    # Get admin messages for this entry
    admin_messages = get_admin_messages()
    entry_messages = [m for m in admin_messages if m.get('journal_id') == journal_id]
    
    # Admin message form
    form = AdminMessageForm()
    form.user_id.data = entry.user_id
    form.journal_id.data = entry.id
    
    return render_template('admin/journal_entry.html', title=entry.title,
                          entry=entry, user=user, recommendations=recommendations,
                          flagged=flagged, messages=entry_messages, form=form)

@admin_bp.route('/journal/<int:journal_id>/flag', methods=['POST'])
@admin_required
def flag_journal(journal_id):
    """Flag a journal entry as having incorrect AI analysis"""
    reason = request.form.get('reason', 'No reason provided')
    
    flag_journal_entry(journal_id, reason)
    flash('Journal entry has been flagged for review.', 'success')
    
    return redirect(url_for('admin.view_journal', journal_id=journal_id))

@admin_bp.route('/journal/<int:journal_id>/message', methods=['POST'])
@admin_required
def send_message(journal_id):
    """Send an admin message about a journal entry"""
    form = AdminMessageForm()
    
    if form.validate_on_submit():
        user_id = form.user_id.data
        message = form.message.data
        
        save_admin_message(user_id, journal_id, message)
        flash('Message has been sent to the user.', 'success')
    
    return redirect(url_for('admin.view_journal', journal_id=journal_id))

@admin_bp.route('/users')
@admin_required
def users():
    """View all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get journal count for each user
    journal_counts = {}
    for user in users.items:
        journal_counts[user.id] = JournalEntry.query.filter_by(user_id=user.id).count()
    
    return render_template('admin/users.html', title='Users', 
                          users=users, journal_counts=journal_counts)

@admin_bp.route('/user/<int:user_id>')
@admin_required
def view_user(user_id):
    """View a specific user"""
    user = User.query.get_or_404(user_id)
    
    # Get user's journal entries
    entries = JournalEntry.query.filter_by(user_id=user.id).order_by(JournalEntry.created_at.desc()).all()
    
    # Get flagged entries for this user
    flagged_entries = get_flagged_entries()
    flagged_ids = [entry.get('journal_id') for entry in flagged_entries]
    
    # Create a dict to track which entries are flagged
    is_flagged = {entry.id: entry.id in flagged_ids for entry in entries}
    
    # Get admin messages for this user
    admin_messages = get_admin_messages(user_id)
    
    return render_template('admin/user_profile.html', title=user.username,
                          user=user, entries=entries, is_flagged=is_flagged,
                          messages=admin_messages)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Admin settings page"""
    config = get_config()
    
    form = APIConfigForm()
    
    if form.validate_on_submit():
        new_config = {
            "openai_api_key": form.api_key.data,
            "max_tokens": form.max_tokens.data,
            "model": form.model.data
        }
        
        save_config(new_config)
        flash('Configuration has been updated.', 'success')
        return redirect(url_for('admin.settings'))
    elif request.method == 'GET':
        form.api_key.data = config.get('openai_api_key', '')
        form.max_tokens.data = config.get('max_tokens', 800)
        form.model.data = config.get('model', 'gpt-4o')
    
    # Calculate some mock API usage stats
    total_entries = JournalEntry.query.count()
    avg_tokens_per_entry = 500
    estimated_tokens = total_entries * avg_tokens_per_entry
    estimated_cost = (estimated_tokens / 1000) * 0.03  # Approximate cost at $0.03 per 1K tokens
    
    api_stats = {
        'total_entries': total_entries,
        'estimated_tokens': estimated_tokens,
        'estimated_cost': estimated_cost
    }
    
    return render_template('admin/settings.html', title='Admin Settings',
                          form=form, api_stats=api_stats)

# Register these routes with the main app (to be added to app.py)
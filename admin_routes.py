from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user
from functools import wraps
import os
import logging
import traceback
from admin_models import Admin
from admin_forms import AdminLoginForm, AdminMessageForm, APIConfigForm, TwilioConfigForm
from app import login_required, db
from admin_utils import (
    ensure_data_files_exist, get_admin_stats, export_journal_entries, 
    export_users, flag_journal_entry, is_entry_flagged, get_flagged_entries,
    save_admin_message, get_admin_messages, get_config, save_config,
    save_twilio_config, load_twilio_config
)
from models import User, JournalEntry, CBTRecommendation

# Set up logging
logger = logging.getLogger(__name__)

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Create a custom admin_required decorator that builds on our main login_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated and is an admin
        if not current_user.is_authenticated:
            flash('Please log in as admin to access this page.', 'danger')
            return redirect(url_for('admin.login', next=request.url))
        # Check if user is an admin (user_id should start with "admin_")
        if not hasattr(current_user, 'get_id') or not current_user.get_id().startswith('admin_'):
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Make sure data files exist
ensure_data_files_exist()

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login route"""
    # If already logged in as admin, redirect to dashboard
    if current_user.is_authenticated and hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
        return redirect(url_for('admin.dashboard'))

    form = AdminLoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if username == "admin":
            admin = Admin.get(1)
            if admin and admin.check_password(password):
                login_user(admin)
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/admin'):
                    return redirect(next_page)
                return redirect(url_for('admin.dashboard'))
            else:
                logger.warning('Failed admin login attempt - invalid password')
                flash('Invalid password', 'danger')
        else:
            logger.warning('Failed admin login attempt - invalid username')
            flash('Invalid username', 'danger')
    elif request.method == 'POST':
        logger.warning('Form validation failed')
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')

    return render_template('admin/basic_login.html', form=form)

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

    # OpenAI API Form
    openai_form = APIConfigForm()

    # Twilio API Form
    twilio_form = TwilioConfigForm()

    # Handle OpenAI form submission
    if 'submit' in request.form and openai_form.submit.name in request.form and openai_form.validate_on_submit():
        new_config = {
            "openai_api_key": openai_form.api_key.data,
            "max_tokens": openai_form.max_tokens.data,
            "model": openai_form.model.data
        }

        save_config(new_config)
        flash('OpenAI configuration has been updated.', 'success')
        return redirect(url_for('admin.settings'))

    # Handle Twilio form submission
    if 'submit' in request.form and twilio_form.submit.name in request.form and twilio_form.validate_on_submit():
        # Store Twilio credentials as environment variables
        os.environ["TWILIO_ACCOUNT_SID"] = twilio_form.account_sid.data
        os.environ["TWILIO_AUTH_TOKEN"] = twilio_form.auth_token.data
        os.environ["TWILIO_PHONE_NUMBER"] = twilio_form.phone_number.data

        # Save Twilio configuration to file for persistence
        save_twilio_config(
            twilio_form.account_sid.data,
            twilio_form.auth_token.data,
            twilio_form.phone_number.data
        )

        flash('Twilio configuration has been updated.', 'success')
        return redirect(url_for('admin.settings'))

    elif request.method == 'GET':
        # Populate OpenAI form
        openai_form.api_key.data = config.get('openai_api_key', '')
        openai_form.max_tokens.data = config.get('max_tokens', 800)
        openai_form.model.data = config.get('model', 'gpt-4o')

        # Load Twilio configuration from saved file
        twilio_config = load_twilio_config()

        # Set environment variables from saved config if they don't exist
        if not os.environ.get("TWILIO_ACCOUNT_SID") and twilio_config.get("account_sid"):
            os.environ["TWILIO_ACCOUNT_SID"] = twilio_config.get("account_sid")
        if not os.environ.get("TWILIO_AUTH_TOKEN") and twilio_config.get("auth_token"):
            os.environ["TWILIO_AUTH_TOKEN"] = twilio_config.get("auth_token")
        if not os.environ.get("TWILIO_PHONE_NUMBER") and twilio_config.get("phone_number"):
            os.environ["TWILIO_PHONE_NUMBER"] = twilio_config.get("phone_number")

        # Populate Twilio form (prioritize environment variables, fallback to saved config)
        twilio_form.account_sid.data = os.environ.get("TWILIO_ACCOUNT_SID", twilio_config.get("account_sid", ""))
        twilio_form.auth_token.data = os.environ.get("TWILIO_AUTH_TOKEN", twilio_config.get("auth_token", ""))
        twilio_form.phone_number.data = os.environ.get("TWILIO_PHONE_NUMBER", twilio_config.get("phone_number", ""))

    # Calculate OpenAI API usage stats
    total_entries = JournalEntry.query.count()
    avg_tokens_per_entry = 500
    estimated_tokens = total_entries * avg_tokens_per_entry
    estimated_cost = (estimated_tokens / 1000) * 0.03  # Approximate cost at $0.03 per 1K tokens

    api_stats = {
        'total_entries': total_entries,
        'estimated_tokens': estimated_tokens,
        'estimated_cost': estimated_cost
    }

    # Get SMS notification stats
    sms_users_count = User.query.filter_by(sms_notifications_enabled=True).filter(User.phone_number.isnot(None)).count()
    sms_stats = {
        'sms_users_count': sms_users_count
    }

    # Get email notification stats
    email_users_count = User.query.filter_by(notifications_enabled=True).count()
    email_stats = {
        'email_users_count': email_users_count
    }

    return render_template('admin/settings.html', title='Admin Settings',
                          openai_form=openai_form, twilio_form=twilio_form, 
                          api_stats=api_stats, sms_stats=sms_stats, email_stats=email_stats)

# These routes have been moved to notification_routes.py
# The following routes have been migrated to the notification_bp blueprint:
# - /test_sms -> notification.test_sms_notification
# - /send_immediate_sms -> notification.send_immediate_sms_notification

# Add a route to view scheduler logs
@admin_bp.route('/scheduler-logs')
@admin_required
def scheduler_logs():
    """View scheduler activity logs to help diagnose notification issues"""
    try:
        from scheduler_logs import get_latest_scheduler_logs

        # Get the latest 50 logs by default, or use the count parameter if provided
        count = request.args.get('count', 50, type=int)
        logs = get_latest_scheduler_logs(count)

        # Group logs by type for easier analysis
        log_groups = {}
        for log in logs:
            log_type = log.get('type', 'unknown')
            if log_type not in log_groups:
                log_groups[log_type] = []
            log_groups[log_type].append(log)

        # Get counts for quick stats
        notification_count = sum(1 for log in logs if 'notification' in log.get('type', ''))
        error_count = sum(1 for log in logs if not log.get('success', True))
        health_check_count = sum(1 for log in logs if 'health' in log.get('type', ''))

        return render_template(
            'admin/scheduler_logs.html', 
            logs=logs,
            log_groups=log_groups,
            notification_count=notification_count,
            error_count=error_count,
            health_check_count=health_check_count,
            count=count
        )
    except Exception as e:
        flash(f'Failed to retrieve scheduler logs: {str(e)}', 'danger')
        logger.error(f"Error retrieving scheduler logs: {str(e)}")
        logger.error(traceback.format_exc())
        return redirect(url_for('admin.dashboard'))
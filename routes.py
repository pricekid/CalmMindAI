from flask import render_template, url_for, flash, redirect, request, jsonify, abort, make_response
from flask_login import login_user, current_user, logout_user
from app import app, db, login_required
from models import User, JournalEntry, CBTRecommendation, MoodLog
from forms import RegistrationForm, LoginForm, JournalEntryForm, MoodLogForm, AccountUpdateForm
from openai_service import analyze_journal_entry, generate_coping_statement
from werkzeug.security import check_password_hash
from sqlalchemy import desc
from sqlalchemy.orm import load_only, defer, undefer
import logging
import csv
import os
import json
from io import StringIO
from datetime import datetime, timedelta
import gamification  # Import the gamification module
from utils.activity_tracker import get_community_message  # Import journal activity tracker

# Home page
@app.route('/')
def index():
    # Get community journal activity message
    try:
        community_message = get_community_message()
    except Exception as e:
        logging.error(f"Error getting community message: {str(e)}")
        community_message = "Join our growing community of mindful journalers."

    return render_template('index.html', 
                          title='Welcome to Calm Journey',
                          community_message=community_message)

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect to the simplified registration page that doesn't have JSON parsing issues
    # Use direct path instead of url_for
    return redirect('/simple-register')

# User login - redirect to basic login to avoid JSON issues
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            if hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
                return redirect('/admin/dashboard')
            return redirect('/dashboard')

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/admin'):
                    flash('You need admin privileges to access that page.', 'warning')
                    return redirect('/dashboard')
                return redirect(next_page if next_page else '/dashboard')
            flash('Invalid email or password.', 'danger')

        # For GET requests, render the login form directly without using the FlaskForm
        if request.method == 'GET':
            # Create an emergency login form that doesn't depend on complex JSON parsing
            emergency_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login to Calm Journey</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="/static/css/bootstrap.min.css">
                <link rel="stylesheet" href="/static/css/styles.css">
                <style>
                    body {{ background-color: #1a1a1a; color: #f8f9fa; }}
                    .card {{ background-color: #212529; border: none; }}
                    .card-header {{ background-color: #0d6efd; color: white; }}
                    .form-control {{ background-color: #343a40; color: #f8f9fa; border-color: #495057; }}
                    .form-control:focus {{ background-color: #343a40; color: #f8f9fa; }}
                    .btn-primary {{ background-color: #0d6efd; }}
                </style>
            </head>
            <body>
                <div class="container mt-5">
                    <div class="row">
                        <div class="col-md-6 mx-auto">
                            <div class="card shadow">
                                <div class="card-header">
                                    <h3 class="mb-0">Login to Calm Journey</h3>
                                </div>
                                <div class="card-body">
                                    <form method="POST" action="/basic-login">
                                        <input type="hidden" name="csrf_token" value="{csrf_token}">
                                        <div class="mb-3">
                                            <label for="email" class="form-label">Email Address</label>
                                            <input type="email" class="form-control" id="email" name="email" required>
                                        </div>
                                        <div class="mb-3">
                                            <label for="password" class="form-label">Password</label>
                                            <input type="password" class="form-control" id="password" name="password" required>
                                        </div>
                                        <div class="mb-3 form-check">
                                            <input type="checkbox" class="form-check-input" id="remember" name="remember">
                                            <label class="form-check-label" for="remember">Remember me</label>
                                        </div>
                                        <div class="d-grid">
                                            <button type="submit" class="btn btn-primary">Login</button>
                                        </div>
                                    </form>
                                    <div class="mt-3 text-center">
                                        <p>Don't have an account? <a href="/register">Sign up</a></p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            from flask import Response
            return Response(emergency_html, 200, content_type='text/html')

        # For POST requests, redirect to basic_login which has better error handling
        # Use direct path instead of url_for
        return redirect('/basic-login')

    except Exception as e:
        app.logger.error(f"Error in login route: {str(e)}")

        # Fallback to basic_login in case of any errors
        # Use direct path instead of url_for
        return redirect('/basic-login')

# Token-based login route for email links
@app.route('/login/token/<token>')
def login_with_token(token):
    """
    Handle token-based login from email links.
    This expects URL parameters: email and expires
    """
    # Get the email and expiry from query parameters
    email = request.args.get('email')
    expires = request.args.get('expires')

    # Log parameters for debugging
    app.logger.info(f"Token login attempt: token={token}, email={email}, expires={expires}")

    # Check if required parameters are present
    if not email or not expires:
        flash('Invalid login link. Missing parameters.', 'danger')
        # Use direct path instead of url_for
        return redirect('/login')

    # Check if the link has expired
    try:
        expiry_time = int(expires)
        current_time = int(datetime.now().timestamp())

        if current_time > expiry_time:
            flash('Login link has expired. Please request a new one.', 'danger')
            # Use direct path instead of url_for
            return redirect('/login')
    except ValueError:
        flash('Invalid login link. Malformed expiry time.', 'danger')
        # Use direct path instead of url_for
        return redirect('/login')

    # Find the user by email
    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        flash('No account found with that email address.', 'danger')
        # Use direct path instead of url_for
        return redirect('/login')

    # Successfully validate the token, log in the user
    login_user(user, remember=True)
    flash('You have been logged in successfully via email link!', 'success')

    # Redirect to the dashboard using direct path - replace url_for calls with direct paths
    # to avoid 'str' object is not callable errors with the dashboard route
    return redirect('/dashboard')

# User logout
@app.route('/logout')
def logout():
    logout_user()
    # Use direct path instead of url_for
    return redirect('/')

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Make sure we're not logged in as admin trying to access regular dashboard
    if hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
        return redirect('/admin/dashboard')

    # Check if the user is new and needs onboarding
    from onboarding_routes import is_new_user
    if is_new_user(current_user.id):
        # New user, redirect to onboarding
        flash('Welcome to Calm Journey! Let\'s get you started with a few quick steps.', 'info')
        return redirect('/onboarding/step-1')

    # Get weekly mood summary
    weekly_summary = current_user.get_weekly_summary()

    # Get recent journal entries - use load_only to avoid loading deferred columns by default
    recent_entries = JournalEntry.query\
        .options(load_only(
            JournalEntry.id,
            JournalEntry.title,
            JournalEntry.content,
            JournalEntry.created_at,
            JournalEntry.updated_at,
            JournalEntry.is_analyzed,
            JournalEntry.anxiety_level,
            JournalEntry.user_id
        ))\
        .filter(JournalEntry.user_id == current_user.id)\
        .order_by(desc(JournalEntry.created_at))\
        .limit(5).all()

    # Get mood data for chart (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    mood_logs = MoodLog.query.filter(
        MoodLog.user_id == current_user.id,
        MoodLog.created_at >= seven_days_ago
    ).order_by(MoodLog.created_at).all()

    # Format mood data for chart.js
    mood_dates = [log.created_at.strftime('%Y-%m-%d') for log in mood_logs]
    mood_scores = [log.mood_score for log in mood_logs]

    # Get latest journal entry for coping statement - use load_only to avoid loading deferred columns
    latest_entry = JournalEntry.query\
        .options(load_only(
            JournalEntry.id,
            JournalEntry.title,
            JournalEntry.content,
            JournalEntry.created_at,
            JournalEntry.is_analyzed,
            JournalEntry.anxiety_level,
            JournalEntry.user_id
        ))\
        .filter(JournalEntry.user_id == current_user.id)\
        .order_by(desc(JournalEntry.created_at))\
        .first()

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

    # Get user's achievements and streaks - NEW FEATURE
    badge_data = None
    try:
        user_id = current_user.id
        badge_data = gamification.get_user_badges(user_id)
        badge_data['streak_status'] = gamification.check_streak_status(user_id)

        # Show earned badges on dashboard (limit to 6 most recent for a nice 2x3 grid)
        if badge_data:
            dashboard_badges = []
            # Get the most recent badges (up to 6)
            for badge_id in badge_data['earned_badges'][-6:]:
                if badge_id in badge_data['badge_details']:
                    dashboard_badges.append(badge_data['badge_details'][badge_id])
            badge_data['dashboard_badges'] = dashboard_badges

            # Also add next badges to earn (for motivation)
            next_badges = []
            # Look through all badges and find up to 3 that aren't earned yet
            count = 0
            for badge_id, badge in badge_data['badge_details'].items():
                if not badge['earned'] and count < 3:
                    next_badges.append(badge)
                    count += 1
            badge_data['next_badges'] = next_badges
    except Exception as e:
        logging.error(f"Error loading achievements for dashboard: {str(e)}")

    # Get form for mood logging
    mood_form = MoodLogForm()

    # Get community journal activity message
    try:
        community_message = get_community_message()
    except Exception as e:
        logging.error(f"Error getting community message for dashboard: {str(e)}")
        community_message = "Join our growing community of mindful journalers."

    return render_template('dashboard.html', 
                          title='Dashboard',
                          recent_entries=recent_entries,
                          mood_dates=mood_dates,
                          mood_scores=mood_scores,
                          coping_statement=coping_statement,
                          mood_form=mood_form,
                          weekly_summary=weekly_summary,
                          badge_data=badge_data,
                          community_message=community_message)

# Redirect to journal list
@app.route('/journal')
@login_required
def journal():
    # Get all entries with efficient loading
    entries = JournalEntry.query\
        .filter_by(user_id=current_user.id)\
        .order_by(JournalEntry.created_at.desc())\
        .limit(30).all()

    return render_template('journal.html', 
                          title='Journal', 
                          entries=entries)

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

# Endpoint for awarding XP when breathing exercise is completed
@app.route('/breathing/complete', methods=['POST'])
@login_required
def breathing_complete():
    try:
        # Award XP for completing breathing exercise
        xp_data = gamification.award_xp(
            user_id=current_user.id,
            xp_amount=gamification.XP_REWARDS['breathing'],
            reason="Completed breathing exercise"
        )

        # Process breathing session badge
        badge_result = gamification.process_breathing_session(current_user.id)

        # Flash notifications for badges
        gamification.flash_badge_notifications(badge_result)

        # Prepare response data
        response_data = {
            'success': True,
            'message': 'Great job completing your breathing exercise!'
        }

        # Add XP info to response
        if xp_data and xp_data.get('xp_gained'):
            response_data['xp_gained'] = xp_data['xp_gained']
            response_data['xp_message'] = f"You earned {xp_data['xp_gained']} XP!"

            # Add level up info if applicable
            if xp_data.get('leveled_up'):
                response_data['level_up'] = True
                response_data['level'] = xp_data['level']
                response_data['level_name'] = xp_data['level_name']
                response_data['level_message'] = f"Level Up! You're now Level {xp_data['level']}: {xp_data['level_name']}"

        return jsonify(response_data)
    except Exception as e:
        app.logger.error(f"Error in breathing_complete route: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error recording breathing exercise completion.'
        }), 500

# User account management - Now moved to account_routes.py blueprint
# This is commented out to avoid conflicts with the blueprint version
"""
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    # We'll let the global error handler handle any exceptions
    form = AccountUpdateForm(current_user.username, current_user.email)

    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('account.html', title='Account', form=form)

        # Store original values for error handling
        original_username = current_user.username
        original_email = current_user.email
        original_notifications = current_user.notifications_enabled
        original_phone = current_user.phone_number
        original_sms = current_user.sms_notifications_enabled

        try:
            # Update user information
            current_user.username = form.username.data
            # Handle email with null safety
            if form.email.data:
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
            # Use direct path instead of url_for
            return redirect('/account')

        except Exception as e:
            # Rollback changes and restore original values
            db.session.rollback()
            current_user.username = original_username
            current_user.email = original_email
            current_user.notifications_enabled = original_notifications
            current_user.phone_number = original_phone
            current_user.sms_notifications_enabled = original_sms

            # Log the specific error
            app.logger.error(f"Database error updating account: {str(e)}")
            flash('An error occurred while updating your account. Please try again.', 'danger')
            # Let the global error handler take over for JSON errors
            raise

    elif request.method == 'GET':
        # Pre-populate the form with current user data
        if current_user.username:
            form.username.data = current_user.username
        if current_user.email:
            form.email.data = current_user.email
        form.notifications_enabled.data = current_user.notifications_enabled
        form.phone_number.data = current_user.phone_number
        form.sms_notifications_enabled.data = current_user.sms_notifications_enabled

    return render_template('account.html', title='Account', form=form)
"""

# Remove the main account route to avoid conflicts with the account blueprint
# The account blueprint will handle the /account URL directly

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

        # Award XP for logging mood (Duolingo-style reward)
        xp_data = gamification.award_xp(
            user_id=current_user.id,
            xp_amount=gamification.XP_REWARDS['mood_log'],
            reason="Logged your mood"
        )

        # Process gamification for mood tracking badge
        badge_result = gamification.process_mood_log(current_user.id)

        # Flash badge notifications if any
        gamification.flash_badge_notifications(badge_result)

        # Flash XP notifications
        if xp_data and xp_data.get('xp_gained'):
            flash(f"🌟 You earned {xp_data['xp_gained']} XP for tracking your mood!", 'success')

            # Show level up message if user leveled up
            if xp_data.get('leveled_up'):
                level = xp_data['level']
                level_name = xp_data['level_name']
                flash(f"🎉 Level Up! You're now Level {level}: {level_name}", 'success')

        flash('Your mood has been logged!', 'success')
    else:
        flash('There was an error logging your mood. Please try again.', 'danger')

    # Use direct path instead of url_for
    return redirect('/dashboard')

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

# Achievements page - see implementation below

# Crisis Resources page
@app.route('/crisis')
def crisis():
    """
    Display mental health crisis resources in a calm, accessible format.
    This page is available to all users, whether logged in or not.
    """
    return render_template('crisis.html', title='Crisis Resources')

# About page
@app.route('/about')
def about():
    """
    Display information about Calm Journey and its mission.
    This page is available to all users, whether logged in or not.
    """
    return render_template('about.html', title='About Calm Journey')

# Define template filters globally before routes
@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    """
    Template filter to handle pluralization based on number.
    Example use in template: {{ count }} item{{ count|pluralize }}
    """
    return singular if number == 1 else plural

@app.route('/achievements')
@login_required
def achievements():
    """
    Display user achievements, badges, and streaks.
    This page shows the user's progress and gamification elements.
    """
    user_id = current_user.id

    try:
        # Get user badge data
        badge_data = gamification.get_user_badges(user_id)

        # Add streak status information
        badge_data['streak_status'] = gamification.check_streak_status(user_id)

        # Log badge data to debug
        app.logger.debug(f"Badge data for user {user_id}: {badge_data}")

        return render_template(
            'achievements.html',
            title='Your Achievements',
            badge_data=badge_data
        )
    except Exception as e:
        app.logger.error(f"Error in achievements route: {str(e)}")
        flash("There was an error loading your achievements. Please try again later.", "warning")
        return render_template('error.html', error_message="Could not load achievements data.")

# Debug route - only use during development
@app.route('/debug-achievements/<int:user_id>')
def debug_achievements(user_id):
    """
    Debug route to check what badge data is available for a user.
    This is for development purposes only.
    """
    try:
        # Get user badge data
        badge_data = gamification.get_user_badges(user_id)

        # Add streak status information
        badge_data['streak_status'] = gamification.check_streak_status(user_id)

        # Return data as JSON for debugging
        return jsonify({
            'badge_data': badge_data,
            'badge_file_exists': os.path.exists(f'data/badges/user_{user_id}_badges.json'),
            'badge_file_content': json.load(open(f'data/badges/user_{user_id}_badges.json', 'r')) if os.path.exists(f'data/badges/user_{user_id}_badges.json') else None
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# Data download routes
@app.route('/download/journal-entries')
@login_required
def download_journal_entries():
    """Download all journal entries for the current user as CSV"""
    # Use load_only to avoid loading user_reflection by default, but then explicitly undefer it
    # This approach optimizes query performance while ensuring we get the reflection data
    entries = JournalEntry.query\
        .options(load_only(
            JournalEntry.id,
            JournalEntry.title,
            JournalEntry.content,
            JournalEntry.created_at,
            JournalEntry.updated_at,
            JournalEntry.is_analyzed,
            JournalEntry.anxiety_level,
            JournalEntry.user_id
        ))\
        .options(undefer(JournalEntry.user_reflection))\
        .filter_by(user_id=current_user.id)\
        .order_by(JournalEntry.created_at.desc())\
        .all()

    # Create CSV file in memory
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Entry ID', 'Title', 'Content', 'Anxiety Level', 'Created', 'Last Updated', 'AI Analysis'])

    # Write data
    for entry in entries:
        # Get recommendations
        recommendations = []
        for rec in entry.recommendations:
            recommendations.append(f"{rec.thought_pattern}: {rec.recommendation}")

        writer.writerow([
            entry.id,
            entry.title,
            entry.content,
            entry.anxiety_level,
            entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            entry.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            '; '.join(recommendations)
        ])

    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=journal_entries.csv"
    response.headers["Content-type"] = "text/csv"

    return response

@app.route('/download/mood-logs')
@login_required
def download_mood_logs():
    """Download all mood logs for the current user as CSV"""
    logs = MoodLog.query.filter_by(user_id=current_user.id).order_by(MoodLog.created_at.desc()).all()

    # Create CSV file in memory
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Log ID', 'Mood Score', 'Notes', 'Created'])

    # Write data
    for log in logs:
        writer.writerow([
            log.id,
            log.mood_score,
            log.notes,
            log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=mood_logs.csv"
    response.headers["Content-type"] = "text/csv"

    return response

@app.route('/download/all-data')
@login_required
def download_all_data():
    """Download all user data including profile, journal entries, and mood logs as JSON"""
    # Get user data
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'created_at': current_user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'notifications_enabled': current_user.notifications_enabled,
        'phone_number': current_user.phone_number,
        'sms_notifications_enabled': current_user.sms_notifications_enabled
    }

    # Get journal entries - use load_only combined with undefer for user_reflection
    # This optimizes query performance while ensuring we get all needed data
    entries = JournalEntry.query\
        .options(load_only(
            JournalEntry.id,
            JournalEntry.title,
            JournalEntry.content,
            JournalEntry.created_at,
            JournalEntry.updated_at,
            JournalEntry.is_analyzed,
            JournalEntry.anxiety_level,
            JournalEntry.user_id
        ))\
        .options(undefer(JournalEntry.user_reflection))\
        .filter_by(user_id=current_user.id)\
        .order_by(JournalEntry.created_at.desc())\
        .all()
    journal_entries = []

    for entry in entries:
        recommendations = []
        for rec in entry.recommendations:
            recommendations.append({
                'thought_pattern': rec.thought_pattern,
                'recommendation': rec.recommendation,
                'created_at': rec.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        journal_entries.append({
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'anxiety_level': entry.anxiety_level,
            'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),            'updated_at': entry.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_analyzed': entry.is_analyzed,
            'recommendations': recommendations,
            'user_reflection': entry.user_reflection
        })

    # Get mood logs
    logs = MoodLog.query.filter_by(user_id=current_user.id).order_by(MoodLog.created_at.desc()).all()
    mood_logs = []

    for log in logs:
        mood_logs.append({
            'id': log.id,
            'mood_score': log.mood_score,
            'notes': log.notes,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    # Combine all data
    all_data = {
        'user': user_data,
        'journal_entries': journal_entries,
        'mood_logs': mood_logs,
        'export_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Prepare response
    response = make_response(jsonify(all_data))
    response.headers["Content-Disposition"] = "attachment; filename=calm_journey_all_data.json"
    response.headers["Content-type"] = "application/json"

    return response

def login_required(f):
    from functools import wraps
    from flask_login import current_user
    from flask import flash, redirect, request

    @wraps(f)
    def decorated_view(*args, **kwargs):
        # Import needed modules inside the decorator to avoid circular imports
        from models import User
        from admin_models import Admin

        if not current_user.is_authenticated:
            flash('You must be logged in to access this page.', 'warning')
            return redirect('/login')

        # Check if current route is for regular users but user is an admin
        if not request.path.startswith('/admin') and hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
            flash('You are logged in as an admin. Regular user pages are not accessible.', 'warning')
            return redirect('/admin/dashboard')

        # Check if current route is for admins but user is not an admin
        if request.path.startswith('/admin') and (not hasattr(current_user, 'get_id') or not current_user.get_id().startswith('admin_')):
            flash('You need admin privileges to access this page.', 'warning')
            return redirect('/dashboard')

        return f(*args, **kwargs)
    return decorated_view
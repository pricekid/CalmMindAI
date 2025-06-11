"""
Debug script to identify dashboard navigation issues
"""
from flask import Blueprint, render_template, current_app, session
from flask_login import current_user, login_required
from app import app, db
from models import User, JournalEntry, MoodLog
from datetime import datetime, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import load_only
import logging

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug-dashboard')
@login_required
def debug_dashboard():
    """
    Debug version of dashboard to identify what's causing the navigation error
    """
    try:
        current_app.logger.info(f"Debug dashboard accessed by user {current_user.id}")
        
        # Check user authentication status
        auth_status = {
            'is_authenticated': current_user.is_authenticated,
            'user_id': current_user.id if current_user.is_authenticated else None,
            'username': current_user.username if current_user.is_authenticated else None
        }
        current_app.logger.info(f"Auth status: {auth_status}")
        
        # Check if user is admin
        is_admin = hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_')
        current_app.logger.info(f"Is admin: {is_admin}")
        
        if is_admin:
            return f"Admin user detected: {current_user.get_id()}, should redirect to admin dashboard"
        
        # Check onboarding status
        try:
            from onboarding_routes import is_new_user
            is_new = is_new_user(current_user.id)
            current_app.logger.info(f"Is new user: {is_new}")
            
            if is_new:
                return f"New user detected: {current_user.id}, should redirect to onboarding"
        except Exception as e:
            current_app.logger.error(f"Error checking new user status: {e}")
        
        # Test database queries
        try:
            # Test weekly summary
            weekly_summary = current_user.get_weekly_summary()
            current_app.logger.info(f"Weekly summary: {weekly_summary}")
        except Exception as e:
            current_app.logger.error(f"Error getting weekly summary: {e}")
            weekly_summary = None
        
        try:
            # Test recent entries query
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
            current_app.logger.info(f"Found {len(recent_entries)} recent entries")
        except Exception as e:
            current_app.logger.error(f"Error getting recent entries: {e}")
            recent_entries = []
        
        try:
            # Test mood logs query
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            mood_logs = MoodLog.query.filter(
                MoodLog.user_id == current_user.id,
                MoodLog.created_at >= seven_days_ago
            ).order_by(MoodLog.created_at).all()
            current_app.logger.info(f"Found {len(mood_logs)} mood logs")
        except Exception as e:
            current_app.logger.error(f"Error getting mood logs: {e}")
            mood_logs = []
        
        # Test welcome message flag
        try:
            show_welcome = not current_user.welcome_message_shown
            current_app.logger.info(f"Show welcome: {show_welcome}")
        except Exception as e:
            current_app.logger.error(f"Error checking welcome flag: {e}")
            show_welcome = False
        
        return f"""
        <h1>Dashboard Debug Results</h1>
        <h2>Authentication</h2>
        <p>User ID: {current_user.id}</p>
        <p>Username: {current_user.username}</p>
        <p>Is authenticated: {current_user.is_authenticated}</p>
        
        <h2>Data Queries</h2>
        <p>Recent entries: {len(recent_entries)}</p>
        <p>Mood logs: {len(mood_logs)}</p>
        <p>Weekly summary: {weekly_summary is not None}</p>
        <p>Show welcome: {show_welcome}</p>
        
        <h2>Navigation</h2>
        <p><a href="/dashboard">Try Dashboard Again</a></p>
        <p><a href="/">Home Page</a></p>
        <p><a href="/journal">Journal</a></p>
        """
        
    except Exception as e:
        current_app.logger.error(f"Debug dashboard error: {e}")
        return f"Debug error: {str(e)}"

# Register the blueprint
app.register_blueprint(debug_bp)
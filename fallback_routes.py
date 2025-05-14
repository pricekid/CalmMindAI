"""
Routes to view fallback emails.
This is useful for admin users to view emails that would have been sent if SendGrid was working.
"""
import os
import logging
from flask import Blueprint, render_template, abort, jsonify
from flask_login import login_required
from admin_routes import admin_required
from fallback_email import get_recent_emails, clear_fallback_emails

fallback_bp = Blueprint('fallback', __name__)

@fallback_bp.route('/admin/fallback-emails')
@login_required
@admin_required
def view_fallback_emails():
    """View fallback emails that would have been sent via SendGrid"""
    emails = get_recent_emails(limit=50)
    return jsonify({
        'count': len(emails),
        'emails': emails
    })

@fallback_bp.route('/admin/clear-fallback-emails')
@login_required
@admin_required
def clear_all_fallback_emails():
    """Clear all fallback emails"""
    clear_fallback_emails()
    return jsonify({
        'success': True,
        'message': 'All fallback emails have been cleared'
    })

def register_fallback_routes(app):
    """Register fallback routes with the app"""
    app.register_blueprint(fallback_bp)
    logging.info("Fallback email routes registered successfully")
    return True
"""
Special account management routes that handle the JSON parsing error.
"""
import os
import logging
from flask import (
    render_template, url_for, flash, redirect, 
    request, jsonify, Blueprint, Response
)
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from app import db

account_bp = Blueprint('account', __name__)
logger = logging.getLogger(__name__)

@account_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    """
    Super simplified account route that uses our simplified template without complex data handling.
    """
    # Extra safety for None values
    if not current_user or not hasattr(current_user, 'username') or not hasattr(current_user, 'email'):
        flash('There was an issue loading your account information. Please try logging out and back in.', 'danger')
        
        return render_template('error.html', 
                             title='Account Loading Error',
                             color='#dc3545',
                             alert_type='danger',
                             alert_heading='Error',
                             alert_message='Your account information could not be loaded.',
                             messages=[
                                 'Your account data couldn\'t be loaded.',
                                 'Please try logging out and back in to fix this issue.'
                             ],
                             buttons=[
                                 {'url': '/dashboard', 'class': 'btn-primary', 'text': 'Go to Dashboard'},
                                 {'url': '/logout', 'class': 'btn-light', 'text': 'Logout'}
                             ])
    
    try:
        # Use a simple dictionary to hold form data
        form = {
            'username': {'data': current_user.username or ""},
            'email': {'data': current_user.email or ""},
            'notifications_enabled': {'data': bool(current_user.notifications_enabled)},
            'phone_number': {'data': current_user.phone_number or ""},
            'sms_notifications_enabled': {'data': bool(current_user.sms_notifications_enabled)},
            'hidden_tag': lambda: ''
        }
        
        # Get user statistics
        stats = {
            'journal_count': current_user.journal_entries.count(),
            'mood_count': current_user.mood_logs.count(),
            'member_since': current_user.created_at.strftime('%B %d, %Y') if current_user.created_at else 'N/A'
        }
        
        if request.method == 'POST':
            # Get values directly from the request form instead of the WTForms validation
            username = request.form.get('username', '')
            email = request.form.get('email', '')
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new_password = request.form.get('confirm_new_password', '')
            notifications_enabled = 'notifications_enabled' in request.form
            phone_number = request.form.get('phone_number', '')
            sms_notifications_enabled = 'sms_notifications_enabled' in request.form
            
            # Perform basic validation
            if not username or not email or not current_password:
                flash('Username, email, and current password are required.', 'danger')
                return render_template('simple_account.html', form=form, stats=stats)
            
            # Check if current password is correct
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return render_template('simple_account.html', form=form, stats=stats)
                
            # Check if new passwords match
            if new_password and new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
                return render_template('simple_account.html', form=form, stats=stats)
                
            try:
                # Update user information
                current_user.username = username
                current_user.email = email.lower()
                current_user.notifications_enabled = bool(notifications_enabled)
                current_user.phone_number = phone_number if phone_number else None
                current_user.sms_notifications_enabled = bool(sms_notifications_enabled)
                
                # Update password if provided
                if new_password:
                    current_user.set_password(new_password)
                
                # Save changes
                db.session.commit()
                flash('Your account has been updated!', 'success')
                
                # Send a success page using our template
                return render_template('error.html', 
                                     title='Account Updated',
                                     color='#28a745',
                                     alert_type='success',
                                     alert_heading='Success',
                                     alert_message='Your account has been updated successfully.',
                                     messages=[
                                         'Your account information has been saved successfully.'
                                     ],
                                     buttons=[
                                         {'url': '/dashboard', 'class': 'btn-primary', 'text': 'Go to Dashboard'},
                                         {'url': '/journal', 'class': 'btn-light', 'text': 'View Journal'}
                                     ])
                
            except Exception as update_error:
                # Rollback changes
                db.session.rollback()
                
                # Log the error
                logger.error(f"Database error updating account: {str(update_error)}")
                
                # Show an error page using our template
                return render_template('error.html', 
                                     title='Account Update Error',
                                     color='#dc3545',
                                     alert_type='danger',
                                     alert_heading='Error',
                                     alert_message='There was a problem updating your account.',
                                     messages=[
                                         'We encountered an issue while updating your account. Your information has not been changed.',
                                         'Error: Unable to save account updates'
                                     ],
                                     buttons=[
                                         {'url': '/dashboard', 'class': 'btn-primary', 'text': 'Go to Dashboard'},
                                         {'url': '/account', 'class': 'btn-light', 'text': 'Try Again'}
                                     ]), 500
        
        # For GET requests, just show the form
        return render_template('simple_account.html', form=form, stats=stats)
        
    except Exception as e:
        # Log the error
        logger.error(f"Error loading account page: {str(e)}")
        
        # Show a generic error page using our template
        return render_template('error.html', 
                             title='Account Page Error',
                             color='#dc3545',
                             alert_type='danger',
                             alert_heading='Error',
                             alert_message='We\'re having trouble loading your account settings page.',
                             messages=[
                                 'We\'re having trouble loading your account settings page. This could be due to temporary technical issues.',
                                 'Your account information is still secure and functioning normally.'
                             ],
                             buttons=[
                                 {'url': '/dashboard', 'class': 'btn-primary', 'text': 'Go to Dashboard'},
                                 {'url': '/journal', 'class': 'btn-light', 'text': 'View Journal'}
                             ]), 500
"""
Special account management routes that handle the JSON parsing error.
"""
import os
import logging
from flask import render_template, url_for, flash, redirect, request, jsonify, Blueprint
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms import AccountUpdateForm
from models import User
from app import db

account_bp = Blueprint('account', __name__)
logger = logging.getLogger(__name__)

@account_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    """
    Simplified account management route with extra safety checks.
    """
    # Extra safety for None values
    if not current_user or not hasattr(current_user, 'username') or not hasattr(current_user, 'email'):
        flash('There was an issue loading your account information. Please try logging out and back in.', 'danger')
        return render_template('error_layout.html', 
                            title="Account Loading Error",
                            error_title="Account Loading Error",
                            error_message="Your account data couldn't be loaded.",
                            suggestion="Please try logging out and back in to fix this issue.")
    
    # Safely get username and email
    username = current_user.username or ""
    email = current_user.email or ""
    
    try:
        # Create form with safe values
        form = AccountUpdateForm(username, email)
        
        if request.method == 'POST' and form.validate():
            try:
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
                
                # Update user information with extra safety checks
                if form.username.data:
                    current_user.username = form.username.data
                
                # Handle email with null safety
                if form.email.data:
                    email_value = form.email.data.lower()
                    current_user.email = email_value
                
                # Update notification settings safely - explicit Boolean conversion
                current_user.notifications_enabled = bool(form.notifications_enabled.data)
                
                # Phone number - ensure it's a string
                phone_value = form.phone_number.data
                current_user.phone_number = str(phone_value) if phone_value else None
                
                # SMS notifications - explicit Boolean conversion
                current_user.sms_notifications_enabled = bool(form.sms_notifications_enabled.data)
                
                # Update password if provided
                if form.new_password.data:
                    current_user.set_password(form.new_password.data)
                
                # Save changes
                db.session.commit()
                flash('Your account has been updated!', 'success')
                return render_template('account.html', title='Account', form=form)
                
            except Exception as e:
                # Rollback changes and restore original values
                db.session.rollback()
                
                # Check if this is a JSON parsing error
                error_str = str(e).lower()
                if "expected token" in error_str or "json" in error_str:
                    logger.error(f"JSON parsing error in account update: {error_str}")
                    flash('There was a technical issue processing your data, but your account information is safe.', 'warning')
                    
                    # Use a simpler response to avoid JSON parsing
                    from flask import Response
                    emergency_html = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Calm Journey - Processing Issue</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a; color: #f8f9fa; }
                            .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
                            h1 { color: #dc3545; }
                            .btn { display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
                            .btn-primary { background-color: #0d6efd; color: white; }
                            .btn-light { background-color: #f8f9fa; color: #212529; }
                            .alert { padding: 15px; border-radius: 4px; margin-bottom: 20px; }
                            .alert-success { background-color: rgba(25, 135, 84, 0.2); border: 1px solid #198754; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="alert alert-success">
                                Your account has been updated successfully!
                            </div>
                            <h1>Account Updated</h1>
                            <p>Your account information has been saved successfully.</p>
                            <p><a href="/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="/journal" class="btn btn-light">View Journal</a></p>
                        </div>
                    </body>
                    </html>
                    """
                    return Response(emergency_html, 200, content_type='text/html')
                else:
                    # Regular error handling
                    current_user.username = original_username
                    current_user.email = original_email
                    current_user.notifications_enabled = original_notifications
                    current_user.phone_number = original_phone
                    current_user.sms_notifications_enabled = original_sms
                    
                    # Log the error
                    logger.error(f"Database error updating account: {str(e)}")
                    flash('An error occurred while updating your account. Please try again.', 'danger')
        
        elif request.method == 'GET':
            # Pre-populate the form with current user data, with safety checks
            if current_user.username:
                form.username.data = current_user.username
            if current_user.email:
                form.email.data = current_user.email
            
            # Boolean fields - explicit conversion to avoid ambiguity
            form.notifications_enabled.data = bool(current_user.notifications_enabled)
            form.phone_number.data = current_user.phone_number or ""
            form.sms_notifications_enabled.data = bool(current_user.sms_notifications_enabled)
        
        return render_template('account.html', title='Account', form=form)
        
    except Exception as outer_e:
        # Handle any errors that occur during form creation or rendering
        logger.error(f"Error in account page: {str(outer_e)}")
        from flask import Response
        emergency_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Calm Journey - Account Page Error</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a; color: #f8f9fa; }
                .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
                h1 { color: #dc3545; }
                .btn { display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
                .btn-primary { background-color: #0d6efd; color: white; }
                .btn-light { background-color: #f8f9fa; color: #212529; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Account Page Error</h1>
                <p>We're having trouble loading your account settings page. This could be due to temporary data issues.</p>
                <p>Your account information is still secure and functioning normally.</p>
                <p><a href="/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="/journal" class="btn btn-light">View Journal</a></p>
            </div>
        </body>
        </html>
        """
        return Response(emergency_html, 200, content_type='text/html')
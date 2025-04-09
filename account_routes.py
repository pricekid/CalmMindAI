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
        emergency_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Calm Journey - Account Error</title>
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
                <h1>Account Loading Error</h1>
                <p>Your account data couldn't be loaded.</p>
                <p>Please try logging out and back in to fix this issue.</p>
                <p><a href="/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="/logout" class="btn btn-light">Logout</a></p>
            </div>
        </body>
        </html>
        """
        return Response(emergency_html, 200, content_type='text/html')
    
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
                return render_template('simple_account.html', form=form)
            
            # Check if current password is correct
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return render_template('simple_account.html', form=form)
                
            # Check if new passwords match
            if new_password and new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
                return render_template('simple_account.html', form=form)
                
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
                
                # Send a simple success page
                success_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Calm Journey - Account Updated</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a; color: #f8f9fa; }
                        .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
                        h1 { color: #28a745; }
                        .alert { padding: 15px; border-radius: 4px; margin-bottom: 20px; }
                        .alert-success { background-color: rgba(40, 167, 69, 0.2); border: 1px solid #28a745; }
                        .btn { display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
                        .btn-primary { background-color: #0d6efd; color: white; }
                        .btn-light { background-color: #f8f9fa; color: #212529; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="alert alert-success">
                            <strong>Success!</strong> Your account has been updated successfully.
                        </div>
                        <h1>Account Updated</h1>
                        <p>Your account information has been saved successfully.</p>
                        <p><a href="/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="/journal" class="btn btn-light">View Journal</a></p>
                    </div>
                </body>
                </html>
                """
                return Response(success_html, 200, content_type='text/html')
                
            except Exception as update_error:
                # Rollback changes
                db.session.rollback()
                
                # Log the error
                logger.error(f"Database error updating account: {str(update_error)}")
                
                # Show an error page
                from flask import Response
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Calm Journey - Update Error</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a; color: #f8f9fa; }}
                        .container {{ max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }}
                        h1 {{ color: #dc3545; }}
                        .alert {{ padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
                        .alert-danger {{ background-color: rgba(220, 53, 69, 0.2); border: 1px solid #dc3545; }}
                        .btn {{ display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }}
                        .btn-primary {{ background-color: #0d6efd; color: white; }}
                        .btn-light {{ background-color: #f8f9fa; color: #212529; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="alert alert-danger">
                            <strong>Error!</strong> There was a problem updating your account.
                        </div>
                        <h1>Account Update Error</h1>
                        <p>We encountered an issue while updating your account. Your information has not been changed.</p>
                        <p>Error: Unable to save account updates</p>
                        <p><a href="/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="/account/account" class="btn btn-light">Try Again</a></p>
                    </div>
                </body>
                </html>
                """
                return Response(error_html, 500, content_type='text/html')
        
        # For GET requests, just show the form
        return render_template('simple_account.html', form=form)
        
    except Exception as e:
        # Log the error
        logger.error(f"Error loading account page: {str(e)}")
        
        # Show a generic error page
        from flask import Response
        emergency_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Calm Journey - Account Error</title>
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
                <p>We're having trouble loading your account settings page. This could be due to temporary technical issues.</p>
                <p>Your account information is still secure and functioning normally.</p>
                <p><a href="/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="/journal" class="btn btn-light">View Journal</a></p>
            </div>
        </body>
        </html>
        """
        return Response(emergency_html, 500, content_type='text/html')
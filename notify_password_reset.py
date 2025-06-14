#!/usr/bin/env python3
"""
Notify users about password reset requirements.
Send email notifications to users who need to reset their passwords.
"""

from app import create_app
from models import User, db
import os

def create_password_reset_notification():
    """Create a notification template for users who need to reset passwords"""
    
    notification_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Password Reset Required - Dear Teddy</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
            .content { padding: 20px; background: #f9f9f9; border-radius: 8px; margin: 20px 0; }
            .button { display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }
            .temp-password { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 15px 0; }
            .code { font-family: monospace; background: #e9ecef; padding: 8px; border-radius: 4px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 Password Reset Required</h1>
            <p>Your Dear Teddy Account Security Update</p>
        </div>
        
        <div class="content">
            <h2>Hello {username},</h2>
            
            <p>We've improved the security of our authentication system and need you to reset your password to continue using Dear Teddy.</p>
            
            <div class="temp-password">
                <h3>📝 Temporary Login Information</h3>
                <p>Email: <span class="code">{email}</span></p>
                <p>Temporary Password: <span class="code">{temp_password}</span></p>
            </div>
            
            <h3>🚀 Next Steps:</h3>
            <ol>
                <li>Visit <a href="https://www.dearteddy.app/stable-login">www.dearteddy.app/stable-login</a></li>
                <li>Log in using your email and the temporary password above</li>
                <li>Go to your account settings to set a new permanent password</li>
                <li>Your temporary password will be disabled once you set a new one</li>
            </ol>
            
            <a href="https://www.dearteddy.app/stable-login" class="button">🔑 Log In Now</a>
            
            <h3>💡 Why This Happened</h3>
            <p>We identified that some user accounts were created through older registration systems that didn't properly secure passwords. This update ensures all accounts have proper security protection.</p>
            
            <h3>🔒 Your Data is Safe</h3>
            <p>All your journal entries, mood logs, and personal data remain completely secure and unchanged. Only the login process has been updated.</p>
            
            <hr>
            
            <p><small>This is an automated security notification from Dear Teddy. If you have any questions, please contact support.</small></p>
        </div>
    </body>
    </html>
    """
    
    return notification_html

def generate_user_notifications():
    """Generate individual notification files for users who need password resets"""
    app = create_app()
    with app.app_context():
        # Find users who had their passwords reset
        users_with_temp_passwords = [
            'Don', 'monique22004', 'Nicole Scott', 'Terry john', 'Naturalarts',
            'Peaceful ', 'Ms. Stressless', 'Dawn', 'Ginger', 'AndreRW',
            'Claudia', 'Peace', 'Toetoe86', 'Alea', 'Kk246', 'Sheldhl', 'Chilled'
        ]
        
        template = create_password_reset_notification()
        
        for username in users_with_temp_passwords:
            user = User.query.filter_by(username=username).first()
            if user:
                temp_password = f"temp_{username}_2025"
                
                notification = template.format(
                    username=username,
                    email=user.email,
                    temp_password=temp_password
                )
                
                # Save notification to file
                filename = f"password_reset_notification_{username.replace(' ', '_')}.html"
                with open(filename, 'w') as f:
                    f.write(notification)
                
                print(f"Created notification for {username}: {filename}")
        
        print(f"\nGenerated {len(users_with_temp_passwords)} password reset notifications")
        print("Users can now log in with their temporary passwords and should reset them immediately")

if __name__ == "__main__":
    generate_user_notifications()
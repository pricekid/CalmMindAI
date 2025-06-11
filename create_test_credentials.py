"""
Create test user credentials for testing the application
"""
import os
import sys
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def create_test_user():
    """Create a test user with known credentials"""
    with app.app_context():
        # Test user credentials
        test_email = "test@example.com"
        test_username = "testuser"
        test_password = "testpass123"
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            print(f"Test user already exists with email: {test_email}")
            print(f"Username: {existing_user.username}")
            print(f"Password: testpass123")
            return existing_user
        
        # Create new test user
        test_user = User(
            username=test_username,
            email=test_email,
            password_hash=generate_password_hash(test_password),
            welcome_message_shown=False  # So they see onboarding
        )
        
        try:
            db.session.add(test_user)
            db.session.commit()
            
            print("✅ Test user created successfully!")
            print(f"Email: {test_email}")
            print(f"Username: {test_username}")
            print(f"Password: {test_password}")
            print(f"User ID: {test_user.id}")
            
            return test_user
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating test user: {e}")
            return None

def create_returning_user():
    """Create a returning user (completed onboarding)"""
    with app.app_context():
        # Returning user credentials
        returning_email = "returning@example.com"
        returning_username = "returninguser"
        returning_password = "return123"
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=returning_email).first()
        if existing_user:
            print(f"Returning user already exists with email: {returning_email}")
            print(f"Username: {existing_user.username}")
            print(f"Password: return123")
            return existing_user
        
        # Create returning user
        returning_user = User(
            username=returning_username,
            email=returning_email,
            password_hash=generate_password_hash(returning_password),
            welcome_message_shown=True  # Skip onboarding
        )
        
        try:
            db.session.add(returning_user)
            db.session.commit()
            
            print("✅ Returning user created successfully!")
            print(f"Email: {returning_email}")
            print(f"Username: {returning_username}")
            print(f"Password: {returning_password}")
            print(f"User ID: {returning_user.id}")
            
            return returning_user
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating returning user: {e}")
            return None

if __name__ == "__main__":
    print("Creating test user credentials...")
    print("=" * 50)
    
    # Create new user (will see onboarding)
    print("\n🆕 NEW USER (will see onboarding):")
    create_test_user()
    
    # Create returning user (skips onboarding)
    print("\n🔄 RETURNING USER (skips onboarding):")
    create_returning_user()
    
    print("\n" + "=" * 50)
    print("Test credentials ready! Use these to test login and onboarding.")
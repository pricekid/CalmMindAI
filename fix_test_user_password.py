"""
Fix the test user password hash to ensure login works properly.
"""
import os
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def fix_test_user_password():
    """Fix the test user password hash"""
    with app.app_context():
        # Find the test user
        test_user = User.query.filter_by(email='test@example.com').first()
        if test_user:
            # Generate a fresh password hash
            new_password_hash = generate_password_hash('testpass123')
            test_user.password_hash = new_password_hash
            
            try:
                db.session.commit()
                print("✅ Test user password fixed successfully!")
                print(f"Email: test@example.com")
                print(f"Password: testpass123")
                return True
            except Exception as e:
                print(f"❌ Error updating password: {e}")
                db.session.rollback()
                return False
        else:
            print("❌ Test user not found")
            return False

def fix_returning_user_password():
    """Fix the returning user password hash"""
    with app.app_context():
        # Find the returning user
        returning_user = User.query.filter_by(email='returning@example.com').first()
        if returning_user:
            # Generate a fresh password hash
            new_password_hash = generate_password_hash('return123')
            returning_user.password_hash = new_password_hash
            
            try:
                db.session.commit()
                print("✅ Returning user password fixed successfully!")
                print(f"Email: returning@example.com")
                print(f"Password: return123")
                return True
            except Exception as e:
                print(f"❌ Error updating password: {e}")
                db.session.rollback()
                return False
        else:
            print("❌ Returning user not found")
            return False

if __name__ == "__main__":
    print("Fixing test user passwords...")
    print("=" * 50)
    
    # Fix both test users
    fix_test_user_password()
    print()
    fix_returning_user_password()
    
    print("\n" + "=" * 50)
    print("Password fixes complete!")
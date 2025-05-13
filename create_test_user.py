"""
Script to create a test user account.
"""
from app import app, db
from models import User

def create_test_user():
    """Create a test user account if it doesn't exist."""
    with app.app_context():
        print('Creating test user...')
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('Password123!')
            db.session.add(test_user)
            db.session.commit()
            print(f'Test user created with ID: {test_user.id}')
            print(f'Username: {test_user.username}')
            print(f'Email: {test_user.email}')
            print('Password: Password123!')
        else:
            print(f'Test user already exists with ID: {test_user.id}')
            # Reset password to ensure it works
            test_user.set_password('Password123!')
            db.session.commit()
            print('Password reset to: Password123!')

if __name__ == '__main__':
    create_test_user()
#!/usr/bin/env python3
"""
Script to create a test user directly in the database to verify the User model works.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
import logging

logging.basicConfig(level=logging.DEBUG)

def create_test_user():
    """Create a test user to verify the model works"""
    
    with app.app_context():
        try:
            # Test creating a user with the fixed model
            test_user = User()
            test_user.username = "model_test_user"
            test_user.email = "model_test@example.com"
            test_user.set_password("testpass123")
            
            print(f"✓ User object created: {test_user.username} ({test_user.email})")
            
            # Test database operations
            db.session.add(test_user)
            db.session.flush()  # Get the ID without committing
            
            user_id = test_user.id
            print(f"✓ User added to session with ID: {user_id}")
            
            # Test querying
            found_user = User.query.filter_by(email="model_test@example.com").first()
            if found_user:
                print(f"✓ User found in database: {found_user.username}")
            else:
                print("! User not found in query (expected for flush without commit)")
            
            # Rollback to not actually save
            db.session.rollback()
            print("✓ Database rollback successful")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating test user: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

def test_user_constructor_variations():
    """Test different ways of creating User objects"""
    
    with app.app_context():
        try:
            # Method 1: Empty constructor then set attributes
            user1 = User()
            user1.username = "test1"
            user1.email = "test1@example.com"
            print("✓ Method 1: Empty constructor + attributes")
            
            # Method 2: Constructor with kwargs (the problematic one)
            user2 = User(username="test2", email="test2@example.com")
            print("✓ Method 2: Constructor with kwargs")
            
            # Method 3: Constructor with individual assignments
            user3 = User()
            user3.username = "test3"
            user3.email = "test3@example.com"
            user3.set_password("testpass")
            print("✓ Method 3: Empty constructor + password setting")
            
            return True
            
        except Exception as e:
            print(f"✗ Error testing constructors: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("=== User Model Test ===")
    
    test1 = create_test_user()
    test2 = test_user_constructor_variations()
    
    print(f"\n=== Results ===")
    print(f"User Creation: {'PASS' if test1 else 'FAIL'}")
    print(f"Constructor Variations: {'PASS' if test2 else 'FAIL'}")
    
    if test1 and test2:
        print("✓ User model is working correctly")
    else:
        print("✗ User model has issues")
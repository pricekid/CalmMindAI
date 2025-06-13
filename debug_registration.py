#!/usr/bin/env python3
"""
Debug script to isolate the registration issue by testing locally.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from forms import RegistrationForm
from flask import Flask

def test_user_creation():
    """Test creating a user directly"""
    print("Testing User model creation...")
    
    try:
        # Test 1: Create user with keyword arguments
        user = User(username="testuser", email="test@example.com")
        print("✓ User creation with kwargs successful")
        
        # Test 2: Set password
        user.set_password("testpass123")
        print("✓ Password setting successful")
        
        # Test 3: Database operations
        with app.app_context():
            db.session.add(user)
            db.session.rollback()  # Don't actually save
            print("✓ Database operations successful")
            
        return True
        
    except Exception as e:
        print(f"✗ User creation failed: {str(e)}")
        return False

def test_form_validation():
    """Test form validation"""
    print("\nTesting form validation...")
    
    try:
        with app.app_context():
            # Create form with test data
            form = RegistrationForm()
            form.username.data = "testuser"
            form.email.data = "test@example.com"
            form.password.data = "testpass123"
            form.confirm_password.data = "testpass123"
            
            print("✓ Form creation successful")
            
            # Test validation
            if form.validate():
                print("✓ Form validation successful")
            else:
                print(f"✗ Form validation failed: {form.errors}")
                
        return True
        
    except Exception as e:
        print(f"✗ Form validation failed: {str(e)}")
        return False

def test_registration_route():
    """Test the registration route directly"""
    print("\nTesting registration route...")
    
    try:
        with app.test_client() as client:
            # Get CSRF token
            response = client.get('/register-simple')
            if response.status_code != 200:
                print(f"✗ GET request failed: {response.status_code}")
                return False
                
            print("✓ GET registration page successful")
            
            # Extract CSRF token from response
            import re
            csrf_match = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', response.get_data(as_text=True))
            if not csrf_match:
                print("✗ Could not find CSRF token")
                return False
                
            csrf_token = csrf_match.group(1)
            print("✓ CSRF token extracted")
            
            # Test POST request
            form_data = {
                'csrf_token': csrf_token,
                'username': 'testuser123',
                'email': 'test123@example.com',
                'password': 'testpass123',
                'confirm_password': 'testpass123',
                'submit': 'Sign Up'
            }
            
            response = client.post('/register-simple', data=form_data)
            print(f"POST response status: {response.status_code}")
            
            if response.status_code == 200:
                # Check for errors in response
                response_text = response.get_data(as_text=True)
                if "error" in response_text.lower() or "alert-danger" in response_text:
                    print("✗ Registration failed with validation errors")
                    return False
                else:
                    print("✓ Registration successful (stayed on page)")
                    return True
            elif response.status_code == 302:
                print("✓ Registration successful (redirected)")
                return True
            else:
                print(f"✗ Registration failed with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Registration route test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Registration Debug Tests ===")
    
    test1 = test_user_creation()
    test2 = test_form_validation()
    test3 = test_registration_route()
    
    print(f"\n=== Results ===")
    print(f"User Creation: {'PASS' if test1 else 'FAIL'}")
    print(f"Form Validation: {'PASS' if test2 else 'FAIL'}")
    print(f"Registration Route: {'PASS' if test3 else 'FAIL'}")
    
    if all([test1, test2, test3]):
        print("All tests passed - registration should work")
    else:
        print("Some tests failed - registration needs fixes")
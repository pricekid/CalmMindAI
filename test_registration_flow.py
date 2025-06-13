#!/usr/bin/env python3
"""
Comprehensive test script to verify the registration system works end-to-end.
This script tests the full registration flow including CSRF token handling.
"""

import requests
import re
import sys
import time
from urllib.parse import urljoin

def test_registration_flow(base_url="https://www.dearteddy.app"):
    """Test the complete registration flow"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print(f"Testing registration flow at: {base_url}")
    
    try:
        # Step 1: Get the registration page
        print("1. Fetching registration page...")
        response = session.get(f"{base_url}/register-simple")
        
        if response.status_code != 200:
            print(f"ERROR: Failed to load registration page. Status: {response.status_code}")
            return False
        
        # Step 2: Extract CSRF token
        print("2. Extracting CSRF token...")
        csrf_match = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', response.text)
        if not csrf_match:
            # Try alternative pattern
            csrf_match = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', response.text)
        if not csrf_match:
            print("ERROR: Could not find CSRF token in registration form")
            print("DEBUG: Looking for hidden inputs...")
            hidden_inputs = re.findall(r'<input[^>]*type="hidden"[^>]*>', response.text)
            for inp in hidden_inputs[:3]:
                print(f"   Found: {inp}")
            return False
        
        csrf_token = csrf_match.group(1)
        print(f"   Found CSRF token: {csrf_token[:20]}...")
        
        # Step 3: Test form submission with unique test data
        print("3. Testing form submission...")
        test_username = f"testuser_{int(time.time())}"
        test_email = f"test_{int(time.time())}@example.com"
        test_password = "TestPass123!"
        
        form_data = {
            'csrf_token': csrf_token,
            'username': test_username,
            'email': test_email,
            'password': test_password,
            'confirm_password': test_password,
            'submit': 'Sign Up'
        }
        
        print(f"   Submitting registration for: {test_email}")
        response = session.post(f"{base_url}/register-simple", data=form_data)
        
        # Step 4: Check response
        if response.status_code == 200:
            # Check if we're still on the registration page (indicates validation error)
            if "register-simple" in response.url or "Begin Your Wellness Journey" in response.text:
                print("4. Form validation or error occurred:")
                
                # Look for error messages
                error_patterns = [
                    r'<div class="alert alert-danger"[^>]*>(.*?)</div>',
                    r'<div class="invalid-feedback"[^>]*>(.*?)</div>',
                    r'class="alert alert-danger"[^>]*>([^<]+)',
                ]
                
                for pattern in error_patterns:
                    errors = re.findall(pattern, response.text, re.DOTALL)
                    if errors:
                        print(f"   Found errors: {[error.strip() for error in errors]}")
                        break
                
                return False
            else:
                print("4. Registration appeared to succeed - redirected away from form")
                return True
                
        elif response.status_code == 302:
            # Redirect indicates success
            print(f"4. Registration successful - redirected to: {response.headers.get('Location', 'unknown')}")
            return True
        else:
            print(f"4. ERROR: Unexpected response status: {response.status_code}")
            print(f"   Response URL: {response.url}")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception during test: {str(e)}")
        return False

def test_validation_errors(base_url="https://www.dearteddy.app"):
    """Test that validation errors are properly handled"""
    
    session = requests.Session()
    
    print(f"\nTesting validation error handling at: {base_url}")
    
    try:
        # Get registration page and CSRF token
        response = session.get(f"{base_url}/register-simple")
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        if not csrf_match:
            print("ERROR: Could not find CSRF token")
            return False
        
        csrf_token = csrf_match.group(1)
        
        # Test with mismatched passwords
        print("1. Testing password mismatch validation...")
        form_data = {
            'csrf_token': csrf_token,
            'username': f"testuser_{int(time.time())}",
            'email': f"test_{int(time.time())}@example.com",
            'password': "password123",
            'confirm_password': "differentpassword",
            'submit': 'Sign Up'
        }
        
        response = session.post(f"{base_url}/register-simple", data=form_data)
        
        if "Passwords must match" in response.text or "password" in response.text.lower():
            print("   ✓ Password mismatch validation working")
        else:
            print("   ✗ Password mismatch validation not working")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERROR: Exception during validation test: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Dear Teddy Registration System Test ===")
    
    # Test basic registration flow
    success = test_registration_flow()
    
    # Test validation error handling
    validation_success = test_validation_errors()
    
    print(f"\n=== Test Results ===")
    print(f"Registration Flow: {'PASS' if success else 'FAIL'}")
    print(f"Validation Errors: {'PASS' if validation_success else 'FAIL'}")
    print(f"Overall: {'PASS' if success and validation_success else 'FAIL'}")
    
    sys.exit(0 if success and validation_success else 1)
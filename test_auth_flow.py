#!/usr/bin/env python3
"""
Test the complete authentication flow:
1. Register a user via minimal registration
2. Verify the user can log in via stable login
"""
import requests
import uuid
import time

def test_registration_and_login():
    """Test the complete registration and login flow"""
    base_url = "http://localhost:5000"
    
    # Generate unique test credentials
    test_id = str(uuid.uuid4())[:8]
    username = f"testuser_{test_id}"
    email = f"test_{test_id}@example.com"
    password = "testpass123"
    
    print(f"Testing with username: {username}, email: {email}")
    
    # Step 1: Register user via minimal registration
    print("Step 1: Registering user...")
    register_data = {
        'username': username,
        'email': email,
        'password': password
    }
    
    register_response = requests.post(
        f"{base_url}/minimal-register",
        data=register_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    print(f"Registration response status: {register_response.status_code}")
    print(f"Registration response: {register_response.text}")
    
    if register_response.status_code != 200:
        print("❌ Registration failed")
        return False
    
    try:
        register_json = register_response.json()
        if not register_json.get('success'):
            print("❌ Registration not successful")
            return False
        user_id = register_json.get('user_id')
        print(f"✅ User registered successfully with ID: {user_id}")
    except Exception as e:
        print(f"❌ Failed to parse registration response: {e}")
        return False
    
    # Step 2: Get login page to establish session
    print("\nStep 2: Getting login page...")
    session = requests.Session()
    login_page_response = session.get(f"{base_url}/stable-login")
    print(f"Login page status: {login_page_response.status_code}")
    
    # Step 3: Attempt to log in
    print("\nStep 3: Attempting login...")
    login_data = {
        'email': email,
        'password': password,
        'remember': 'on'
    }
    
    login_response = session.post(
        f"{base_url}/stable-login",
        data=login_data,
        allow_redirects=False  # Don't follow redirects to see what happens
    )
    
    print(f"Login response status: {login_response.status_code}")
    print(f"Login response headers: {dict(login_response.headers)}")
    
    # Check if login was successful (should redirect to dashboard)
    if login_response.status_code == 302:
        redirect_location = login_response.headers.get('Location', '')
        print(f"Login redirect location: {redirect_location}")
        if '/dashboard' in redirect_location:
            print("✅ Login successful - redirecting to dashboard")
            return True
        else:
            print("❌ Login redirected to unexpected location")
            return False
    elif login_response.status_code == 200:
        # Check if there's an error in the response
        if 'error' in login_response.text.lower():
            print("❌ Login failed with error message")
            print(f"Response snippet: {login_response.text[:500]}")
            return False
        else:
            print("✅ Login successful - returned login page")
            return True
    else:
        print(f"❌ Unexpected login response status: {login_response.status_code}")
        return False

if __name__ == "__main__":
    print("Testing authentication flow...")
    success = test_registration_and_login()
    if success:
        print("\n🎉 Authentication flow test PASSED")
    else:
        print("\n💥 Authentication flow test FAILED")
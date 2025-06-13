
#!/usr/bin/env python3
"""
Test registration and login flow on live Dear Teddy site
"""
import requests
import uuid
import time
from datetime import datetime

def test_live_registration_and_login():
    """Test complete registration and login flow on live site"""
    base_url = "https://www.dearteddy.app"
    
    # Generate unique test credentials
    timestamp = int(time.time())
    test_username = f"testuser_{timestamp}"
    test_email = f"test_{timestamp}@example.com"
    test_password = "TestPass123!"
    
    print(f"🌐 Testing Dear Teddy Live Site Registration & Login")
    print(f"Site: {base_url}")
    print(f"Test User: {test_username}")
    print(f"Test Email: {test_email}")
    print("=" * 60)
    
    session = requests.Session()
    
    # Test 1: Check if site is accessible
    print("1. Testing site accessibility...")
    try:
        response = session.get(base_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ Site is accessible")
        else:
            print(f"   ❌ Site returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Site is not accessible: {e}")
        return False
    
    # Test 2: Test registration
    print("2. Testing user registration...")
    
    # Try different registration endpoints
    registration_endpoints = [
        "/register",
        "/register-simple", 
        "/minimal-register",
        "/working-register"
    ]
    
    registration_success = False
    for endpoint in registration_endpoints:
        try:
            print(f"   Trying endpoint: {endpoint}")
            
            # First get the registration page to establish session
            reg_page = session.get(f"{base_url}{endpoint}", timeout=10)
            
            if reg_page.status_code == 200:
                # Prepare registration data
                reg_data = {
                    'username': test_username,
                    'email': test_email,
                    'password': test_password,
                    'confirm_password': test_password
                }
                
                # Try to register
                reg_response = session.post(f"{base_url}{endpoint}", data=reg_data, timeout=10)
                
                print(f"   Registration response: {reg_response.status_code}")
                
                if reg_response.status_code == 200:
                    # Check if registration was successful
                    response_text = reg_response.text.lower()
                    if "success" in response_text or "dashboard" in response_text or "welcome" in response_text:
                        print(f"   ✅ Registration successful via {endpoint}")
                        registration_success = True
                        break
                    elif "already" in response_text or "exists" in response_text:
                        print(f"   ⚠️  User might already exist, trying login...")
                        break
                    else:
                        print(f"   ❌ Registration failed at {endpoint}")
                elif reg_response.status_code == 302:
                    print(f"   ✅ Registration successful (redirected) via {endpoint}")
                    registration_success = True
                    break
                        
        except Exception as e:
            print(f"   ❌ Error testing {endpoint}: {e}")
            continue
    
    if not registration_success:
        print("   ⚠️  Registration endpoints didn't work, testing login with existing account...")
    
    # Test 3: Test login
    print("3. Testing user login...")
    
    login_endpoints = [
        "/login",
        "/stable-login",
        "/simple-login",
        "/direct-login"
    ]
    
    login_success = False
    for endpoint in login_endpoints:
        try:
            print(f"   Trying login endpoint: {endpoint}")
            
            # Get login page
            login_page = session.get(f"{base_url}{endpoint}", timeout=10)
            
            if login_page.status_code == 200:
                # Prepare login data
                login_data = {
                    'email': test_email,
                    'password': test_password
                }
                
                # Try to login
                login_response = session.post(f"{base_url}{endpoint}", data=login_data, timeout=10, allow_redirects=False)
                
                print(f"   Login response: {login_response.status_code}")
                
                if login_response.status_code == 302:
                    # Check redirect location
                    location = login_response.headers.get('Location', '')
                    if 'dashboard' in location.lower():
                        print(f"   ✅ Login successful via {endpoint} - redirected to dashboard")
                        login_success = True
                        break
                    else:
                        print(f"   ⚠️  Login redirected to: {location}")
                elif login_response.status_code == 200:
                    response_text = login_response.text.lower()
                    if "dashboard" in response_text or "welcome" in response_text:
                        print(f"   ✅ Login successful via {endpoint}")
                        login_success = True
                        break
                    elif "invalid" in response_text or "incorrect" in response_text:
                        print(f"   ❌ Login failed - invalid credentials at {endpoint}")
                    else:
                        print(f"   ❌ Login failed at {endpoint}")
                        
        except Exception as e:
            print(f"   ❌ Error testing login {endpoint}: {e}")
            continue
    
    # Test 4: Check dashboard access
    if login_success or registration_success:
        print("4. Testing dashboard access...")
        try:
            dashboard_response = session.get(f"{base_url}/dashboard", timeout=10)
            if dashboard_response.status_code == 200:
                print("   ✅ Dashboard accessible after authentication")
            else:
                print(f"   ❌ Dashboard not accessible: {dashboard_response.status_code}")
        except Exception as e:
            print(f"   ❌ Error accessing dashboard: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🔍 LIVE SITE TEST RESULTS")
    print("=" * 60)
    
    if registration_success:
        print("✅ Registration: WORKING")
    else:
        print("❌ Registration: FAILED")
    
    if login_success:
        print("✅ Login: WORKING")
    else:
        print("❌ Login: FAILED")
    
    if registration_success and login_success:
        print("\n🎉 Complete authentication flow is working!")
        return True
    elif registration_success or login_success:
        print("\n⚠️  Partial authentication flow working")
        return True
    else:
        print("\n💥 Authentication flow has issues")
        return False

if __name__ == "__main__":
    test_live_registration_and_login()

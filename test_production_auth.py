#!/usr/bin/env python3
"""
Test authentication flow on production Dear Teddy site
"""
import requests
import uuid
import time

def test_production_registration():
    """Test registration on production site"""
    base_url = "https://dear-teddy.onrender.com"
    
    # Generate unique test credentials
    test_id = str(uuid.uuid4())[:8]
    username = f"prodtest_{test_id}"
    email = f"prodtest_{test_id}@example.com"
    password = "testpass123"
    
    print(f"Testing production with: {username}, {email}")
    
    # Try registration via different endpoints
    endpoints_to_try = [
        "/minimal-register",
        "/register", 
        "/emergency-register",
        "/production-register"
    ]
    
    for endpoint in endpoints_to_try:
        print(f"\nTesting registration endpoint: {endpoint}")
        try:
            register_data = {
                'username': username,
                'email': email,
                'password': password
            }
            
            response = requests.post(
                f"{base_url}{endpoint}",
                data=register_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    json_resp = response.json()
                    if json_resp.get('success'):
                        print(f"✅ Registration successful at {endpoint}")
                        return email, password, endpoint
                except:
                    pass
                    
                if 'success' in response.text.lower():
                    print(f"✅ Registration appears successful at {endpoint}")
                    return email, password, endpoint
            
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")
    
    print("❌ No working registration endpoint found")
    return None, None, None

def test_production_login(email, password):
    """Test login on production site"""
    base_url = "https://dear-teddy.onrender.com"
    
    print(f"\nTesting login with: {email}")
    
    # Get login page first to establish session
    session = requests.Session()
    try:
        login_page = session.get(f"{base_url}/stable-login", timeout=10)
        print(f"Login page status: {login_page.status_code}")
    except Exception as e:
        print(f"Error getting login page: {e}")
        return False
    
    # Attempt login
    login_data = {
        'email': email,
        'password': password
    }
    
    try:
        login_response = session.post(
            f"{base_url}/stable-login",
            data=login_data,
            allow_redirects=False,
            timeout=10
        )
        
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 302:
            redirect_location = login_response.headers.get('Location', '')
            print(f"Redirect to: {redirect_location}")
            if '/dashboard' in redirect_location:
                print("✅ Login successful - redirecting to dashboard")
                return True
        elif login_response.status_code == 200:
            if 'error' not in login_response.text.lower():
                print("✅ Login successful")
                return True
            else:
                print("❌ Login failed with error")
                return False
        else:
            print(f"❌ Login failed with status {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error during login: {e}")
        return False

def main():
    print("Testing production authentication flow...")
    
    # Test registration
    email, password, endpoint = test_production_registration()
    
    if not email:
        print("\n💥 Could not register user on production")
        return
    
    print(f"\n✅ Successfully registered via {endpoint}")
    
    # Wait a moment for database consistency
    time.sleep(2)
    
    # Test login
    login_success = test_production_login(email, password)
    
    if login_success:
        print("\n🎉 Production authentication flow WORKING")
    else:
        print("\n💥 Production login FAILED")

if __name__ == "__main__":
    main()
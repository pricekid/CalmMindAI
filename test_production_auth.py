"""
Test authentication flow on production Dear Teddy site
"""
import requests
import json

def test_production_registration():
    """Test registration on production site"""
    try:
        # Test minimal registration endpoint
        response = requests.post(
            "https://dear-teddy.onrender.com/minimal-register",
            data={
                "username": "testuser2025",
                "email": "testuser2025@example.com", 
                "password": "testpass123"
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"Registration Response Status: {response.status_code}")
        print(f"Registration Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    print("✅ Registration successful!")
                    return data.get('user_id')
                else:
                    print(f"❌ Registration failed: {data.get('error')}")
            except json.JSONDecodeError:
                print("❌ Invalid JSON response from registration")
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    return None

def test_production_login(email, password):
    """Test login on production site"""
    try:
        # Test stable login endpoint  
        response = requests.post(
            "https://dear-teddy.onrender.com/stable-login",
            data={
                "email": email,
                "password": password
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            allow_redirects=False
        )
        
        print(f"Login Response Status: {response.status_code}")
        print(f"Login Response Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 302]:
            print("✅ Login endpoint accessible")
            if 'Set-Cookie' in response.headers:
                print("✅ Session cookie set")
            return True
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    return False

def main():
    print("🚀 Testing Dear Teddy Production Authentication")
    print("=" * 50)
    
    # Test registration
    print("\n1. Testing Registration...")
    user_id = test_production_registration()
    
    # Test login if registration worked
    if user_id:
        print("\n2. Testing Login...")
        login_success = test_production_login("testuser2025@example.com", "testpass123")
        
        if login_success:
            print("\n✅ Complete authentication flow working!")
        else:
            print("\n❌ Login flow has issues")
    else:
        print("\n❌ Registration failed, skipping login test")
    
    print("\n" + "=" * 50)
    print("Test complete.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test registration and login on the live production site
"""
import requests
import json
from urllib.parse import urljoin

def test_production_site():
    """Test the live production site for authentication issues"""
    base_url = "https://www.dearteddy.app"
    
    print(f"Testing production site: {base_url}")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    try:
        response = requests.get(base_url, timeout=10)
        print(f"✓ Site accessibility: {response.status_code}")
        if response.status_code != 200:
            print(f"  Response: {response.text[:200]}...")
    except Exception as e:
        print(f"✗ Site accessibility failed: {str(e)}")
        return
    
    # Test 2: Registration page
    try:
        reg_url = urljoin(base_url, "/register")
        response = requests.get(reg_url, timeout=10)
        print(f"✓ Registration page: {response.status_code}")
        if response.status_code != 200:
            print(f"  Error response: {response.text[:300]}...")
    except Exception as e:
        print(f"✗ Registration page failed: {str(e)}")
    
    # Test 3: Login page
    try:
        login_url = urljoin(base_url, "/stable-login")
        response = requests.get(login_url, timeout=10)
        print(f"✓ Login page: {response.status_code}")
        if response.status_code != 200:
            print(f"  Error response: {response.text[:300]}...")
    except Exception as e:
        print(f"✗ Login page failed: {str(e)}")
    
    # Test 4: Try to get CSRF token and attempt registration
    session = requests.Session()
    try:
        # Get registration form
        reg_response = session.get(urljoin(base_url, "/register"), timeout=10)
        if reg_response.status_code == 200:
            # Try to extract CSRF token (basic approach)
            import re
            csrf_pattern = r'name="csrf_token"[^>]*value="([^"]*)"'
            csrf_match = re.search(csrf_pattern, reg_response.text)
            
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"✓ CSRF token extracted: {csrf_token[:20]}...")
                
                # Attempt test registration
                test_data = {
                    'csrf_token': csrf_token,
                    'email': 'test@example.com',
                    'password': 'TestPassword123!',
                    'confirm_password': 'TestPassword123!'
                }
                
                reg_post = session.post(urljoin(base_url, "/register"), 
                                      data=test_data, timeout=10)
                print(f"✓ Registration attempt: {reg_post.status_code}")
                
                if reg_post.status_code >= 400:
                    print(f"  Registration error response: {reg_post.text[:500]}...")
                    
            else:
                print("✗ Could not extract CSRF token from registration form")
        else:
            print(f"✗ Could not access registration form: {reg_response.status_code}")
            
    except Exception as e:
        print(f"✗ Registration test failed: {str(e)}")
    
    # Test 5: Check for common API endpoints
    api_endpoints = ["/health", "/api/health", "/dashboard", "/admin"]
    for endpoint in api_endpoints:
        try:
            response = requests.get(urljoin(base_url, endpoint), timeout=5)
            print(f"  {endpoint}: {response.status_code}")
        except:
            print(f"  {endpoint}: timeout/error")

if __name__ == "__main__":
    test_production_site()

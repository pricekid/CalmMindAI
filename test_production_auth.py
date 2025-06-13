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
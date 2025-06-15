#!/usr/bin/env python3
"""
Debug production login issue by testing different scenarios
"""
import requests
import json

def test_production_endpoints():
    """Test various production endpoints to diagnose the login issue"""
    base_url = "https://dear-teddy.onrender.com"
    
    print("Testing production endpoints...")
    
    # Test 1: Basic connectivity
    print("\n1. Testing basic connectivity...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   Root endpoint: {response.status_code}")
    except Exception as e:
        print(f"   Root endpoint error: {e}")
    
    # Test 2: Login page access
    print("\n2. Testing login page access...")
    try:
        response = requests.get(f"{base_url}/stable-login", timeout=10)
        print(f"   Login page: {response.status_code}")
        if response.status_code == 200:
            print("   Login page loads successfully")
    except Exception as e:
        print(f"   Login page error: {e}")
    
    # Test 3: Registration endpoint
    print("\n3. Testing registration endpoint...")
    try:
        response = requests.get(f"{base_url}/minimal-register", timeout=10)
        print(f"   Registration endpoint: {response.status_code}")
    except Exception as e:
        print(f"   Registration error: {e}")
    
    # Test 4: Emergency login routes
    print("\n4. Testing emergency login routes...")
    emergency_routes = [
        "/r-login",
        "/emergency-login", 
        "/test-login",
        "/render-login"
    ]
    
    for route in emergency_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            print(f"   {route}: {response.status_code}")
        except Exception as e:
            print(f"   {route} error: {e}")

def test_login_with_detailed_error():
    """Test login with detailed error capture"""
    base_url = "https://dear-teddy.onrender.com"
    
    print("\n5. Testing login with error details...")
    
    session = requests.Session()
    
    # Get login page first
    try:
        login_page = session.get(f"{base_url}/stable-login", timeout=10)
        print(f"   Login page status: {login_page.status_code}")
        
        # Try login with test credentials
        login_data = {
            'email': 'test@example.com',
            'password': 'test123'
        }
        
        print("   Attempting login...")
        login_response = session.post(
            f"{base_url}/stable-login",
            data=login_data,
            timeout=10,
            allow_redirects=False
        )
        
        print(f"   Login response status: {login_response.status_code}")
        print(f"   Response content length: {len(login_response.text)}")
        
        # Check for specific error indicators
        if login_response.status_code == 500:
            print("   500 Internal Server Error detected")
            
            # Look for common error patterns in response
            content = login_response.text.lower()
            if 'sqlalchemy' in content:
                print("   ⚠️  SQLAlchemy error detected in response")
            if 'csrf' in content:
                print("   ⚠️  CSRF error detected in response")
            if 'database' in content:
                print("   ⚠️  Database error detected in response")
            if 'not registered' in content:
                print("   ⚠️  Flask app registration error detected")
                
        elif login_response.status_code == 302:
            location = login_response.headers.get('Location', '')
            print(f"   Redirect to: {location}")
            if '/dashboard' in location:
                print("   ✅ Login appears successful")
            else:
                print("   ⚠️  Unexpected redirect location")
        
        elif login_response.status_code == 200:
            print("   Login page returned - checking for error messages")
            if 'error' in login_response.text.lower():
                print("   ⚠️  Error message present in response")
            
    except Exception as e:
        print(f"   Login test error: {e}")

def test_alternative_login_methods():
    """Test alternative login methods available on production"""
    base_url = "https://dear-teddy.onrender.com"
    
    print("\n6. Testing alternative login methods...")
    
    # Try emergency login
    try:
        session = requests.Session()
        emergency_data = {
            'email': 'test@example.com',
            'password': 'test123'
        }
        
        response = session.post(
            f"{base_url}/emergency-login",
            data=emergency_data,
            timeout=10,
            allow_redirects=False
        )
        print(f"   Emergency login: {response.status_code}")
        
    except Exception as e:
        print(f"   Emergency login error: {e}")
    
    # Try render-specific login
    try:
        session = requests.Session()
        render_data = {
            'email': 'test@example.com',
            'password': 'test123'
        }
        
        response = session.post(
            f"{base_url}/r-login",
            data=render_data,
            timeout=10,
            allow_redirects=False
        )
        print(f"   Render login: {response.status_code}")
        
    except Exception as e:
        print(f"   Render login error: {e}")

if __name__ == "__main__":
    print("🔍 Production Login Diagnostics")
    print("=" * 40)
    
    test_production_endpoints()
    test_login_with_detailed_error()
    test_alternative_login_methods()
    
    print("\n📋 Summary:")
    print("If all tests show 500 errors for login attempts,")
    print("the SQLAlchemy registration issue persists in production.")
    print("The fix may not have been deployed yet or needs additional changes.")
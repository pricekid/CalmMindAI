#!/usr/bin/env python3
"""
Comprehensive production authentication test for www.dearteddy.app
Tests both registration and login functionality with real API calls
"""

import requests
import json
import time
from datetime import datetime

def test_production_site():
    """Test registration and login on production site"""
    
    base_url = "https://www.dearteddy.app"
    session = requests.Session()
    
    print("=== Testing Production Site Authentication ===")
    print(f"Target: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Generate unique test credentials
    timestamp = int(time.time())
    test_data = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }
    
    print(f"\nTest Credentials:")
    print(f"Username: {test_data['username']}")
    print(f"Email: {test_data['email']}")
    print(f"Password: {test_data['password']}")
    
    # Test 1: Check if site is accessible
    print("\n1. Testing site accessibility...")
    try:
        response = session.get(base_url, timeout=10)
        print(f"   Main site status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Site is accessible")
        else:
            print(f"   ⚠ Site returned status {response.status_code}")
    except Exception as e:
        print(f"   ✗ Site not accessible: {e}")
        return False
    
    # Test 2: Registration
    print("\n2. Testing user registration...")
    try:
        reg_response = session.post(
            f"{base_url}/register",
            data=test_data,
            timeout=15,
            allow_redirects=False
        )
        print(f"   Registration status: {reg_response.status_code}")
        
        if reg_response.status_code == 302:
            print("   ✓ Registration successful (redirect)")
            registration_success = True
        elif reg_response.status_code == 200:
            if "success" in reg_response.text.lower() or "dashboard" in reg_response.text.lower():
                print("   ✓ Registration successful")
                registration_success = True
            else:
                print("   ⚠ Registration may have failed")
                print(f"   Response preview: {reg_response.text[:200]}")
                registration_success = False
        else:
            print(f"   ✗ Registration failed with status {reg_response.status_code}")
            print(f"   Response preview: {reg_response.text[:200]}")
            registration_success = False
            
    except Exception as e:
        print(f"   ✗ Registration error: {e}")
        registration_success = False
    
    # Test 3: Login (try both main and stable login endpoints)
    print("\n3. Testing user login...")
    login_endpoints = ["/login", "/stable-login"]
    login_success = False
    
    for endpoint in login_endpoints:
        print(f"\n   Testing {endpoint}...")
        try:
            login_data = {
                "email": test_data["email"],
                "password": test_data["password"]
            }
            
            login_response = session.post(
                f"{base_url}{endpoint}",
                data=login_data,
                timeout=15,
                allow_redirects=False
            )
            
            print(f"   Login status: {login_response.status_code}")
            
            if login_response.status_code == 302:
                print(f"   ✓ Login successful on {endpoint} (redirect)")
                login_success = True
                break
            elif login_response.status_code == 200:
                if "dashboard" in login_response.text.lower() or "welcome" in login_response.text.lower():
                    print(f"   ✓ Login successful on {endpoint}")
                    login_success = True
                    break
                else:
                    print(f"   ⚠ Login may have failed on {endpoint}")
            else:
                print(f"   ✗ Login failed on {endpoint} with status {login_response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Login error on {endpoint}: {e}")
    
    # Test 4: Try with existing known user
    print("\n4. Testing with existing user...")
    try:
        existing_login_data = {
            "email": "jamesbond@hotmail.com",
            "password": "temp_Jamesbond_2025"  # Known temporary password
        }
        
        existing_login_response = session.post(
            f"{base_url}/stable-login",
            data=existing_login_data,
            timeout=15,
            allow_redirects=False
        )
        
        print(f"   Existing user login status: {existing_login_response.status_code}")
        
        if existing_login_response.status_code == 302:
            print("   ✓ Existing user login successful")
        elif existing_login_response.status_code == 200:
            if "dashboard" in existing_login_response.text.lower():
                print("   ✓ Existing user login successful")
            else:
                print("   ⚠ Existing user login may have failed")
        else:
            print(f"   ✗ Existing user login failed")
            
    except Exception as e:
        print(f"   ✗ Existing user login error: {e}")
    
    # Test 5: Health check
    print("\n5. Testing health endpoint...")
    try:
        health_response = session.get(f"{base_url}/health", timeout=10)
        print(f"   Health status: {health_response.status_code}")
        
        if health_response.status_code == 200:
            try:
                health_data = health_response.json()
                print(f"   Health data: {health_data}")
            except:
                print("   Health endpoint accessible but not JSON")
        else:
            print(f"   Health endpoint returned {health_response.status_code}")
            
    except Exception as e:
        print(f"   Health endpoint error: {e}")
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Site accessible: {'✓' if response.status_code == 200 else '✗'}")
    print(f"Registration: {'✓' if registration_success else '✗'}")
    print(f"Login: {'✓' if login_success else '✗'}")
    
    return registration_success and login_success

if __name__ == "__main__":
    success = test_production_site()
    print(f"\nOverall test result: {'PASS' if success else 'FAIL'}")
    exit(0 if success else 1)
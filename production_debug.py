#!/usr/bin/env python3
"""
Production environment debugging script to identify why registration fails in production.
"""

import requests
import re
import json
from datetime import datetime

def test_production_environment():
    """Test various aspects of the production environment"""
    
    base_url = "https://www.dearteddy.app"
    session = requests.Session()
    
    print("=== Production Environment Analysis ===")
    print(f"Testing: {base_url}")
    
    # Test 1: Basic connectivity
    try:
        response = session.get(f"{base_url}/")
        print(f"✓ Homepage accessible: {response.status_code}")
    except Exception as e:
        print(f"✗ Homepage error: {str(e)}")
        return False
    
    # Test 2: Registration page structure
    try:
        response = session.get(f"{base_url}/register-simple")
        if response.status_code == 200:
            print("✓ Registration page loads")
            
            # Check for form elements
            if 'id="csrf_token"' in response.text:
                print("✓ CSRF token field present")
            else:
                print("✗ CSRF token field missing")
                
            if 'name="username"' in response.text:
                print("✓ Username field present")
            else:
                print("✗ Username field missing")
                
            if 'name="email"' in response.text:
                print("✓ Email field present")
            else:
                print("✗ Email field missing")
                
        else:
            print(f"✗ Registration page error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Registration page error: {str(e)}")
        return False
    
    # Test 3: CSRF token validity
    try:
        csrf_match = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"✓ CSRF token extracted: {csrf_token[:20]}...")
        else:
            print("✗ Could not extract CSRF token")
            return False
    except Exception as e:
        print(f"✗ CSRF token error: {str(e)}")
        return False
    
    # Test 4: Form submission with detailed error analysis
    try:
        timestamp = int(datetime.now().timestamp())
        test_data = {
            'csrf_token': csrf_token,
            'username': f'debuguser{timestamp}',
            'email': f'debug{timestamp}@example.com',
            'password': 'DebugPass123!',
            'confirm_password': 'DebugPass123!',
            'submit': 'Sign Up'
        }
        
        response = session.post(f"{base_url}/register-simple", data=test_data, allow_redirects=False)
        
        print(f"Form submission status: {response.status_code}")
        
        if response.status_code == 500:
            print("✗ 500 Internal Server Error detected")
            
            # Try to extract any error information from headers
            for header, value in response.headers.items():
                if 'error' in header.lower() or 'debug' in header.lower():
                    print(f"  Error header {header}: {value}")
            
            # Check if response contains any error details
            if response.text and len(response.text) > 0:
                if 'Traceback' in response.text or 'Error' in response.text:
                    print("  Response contains error information")
                else:
                    print("  Response is standard error page")
            
            return False
            
        elif response.status_code == 302:
            print("✓ Registration successful (redirect)")
            redirect_url = response.headers.get('Location', 'Unknown')
            print(f"  Redirected to: {redirect_url}")
            return True
            
        elif response.status_code == 200:
            if 'success' in response.text.lower() or 'created' in response.text.lower():
                print("✓ Registration successful (success message)")
                return True
            elif 'error' in response.text.lower() or 'invalid' in response.text.lower():
                print("! Registration validation error (expected for duplicates)")
                return True
            else:
                print("? Unclear registration result")
                return False
        else:
            print(f"? Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Form submission error: {str(e)}")
        return False

def test_alternative_endpoints():
    """Test alternative registration endpoints that might be working"""
    
    base_url = "https://www.dearteddy.app"
    endpoints = [
        "/register",
        "/signup", 
        "/auth/register",
        "/user/register"
    ]
    
    print("\n=== Alternative Endpoint Test ===")
    
    session = requests.Session()
    
    for endpoint in endpoints:
        try:
            response = session.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                print(f"✓ {endpoint} accessible")
            elif response.status_code == 404:
                print(f"- {endpoint} not found")
            else:
                print(f"? {endpoint} status: {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint} error: {str(e)}")

def check_production_vs_local():
    """Compare production and local behavior"""
    
    print("\n=== Production vs Local Comparison ===")
    
    # Test local endpoint
    local_url = "http://localhost:5000"
    
    try:
        local_response = requests.get(f"{local_url}/register-simple", timeout=5)
        print(f"Local registration page: {local_response.status_code}")
    except Exception:
        print("Local server not accessible (expected in production)")
    
    # Test production endpoint behavior
    prod_url = "https://www.dearteddy.app"
    
    try:
        prod_response = requests.get(f"{prod_url}/register-simple")
        print(f"Production registration page: {prod_response.status_code}")
        
        # Compare content lengths
        print(f"Production page size: {len(prod_response.text)} characters")
        
    except Exception as e:
        print(f"Production comparison error: {str(e)}")

if __name__ == "__main__":
    print(f"Starting production debugging at {datetime.now()}")
    
    env_test = test_production_environment()
    test_alternative_endpoints()
    check_production_vs_local()
    
    print(f"\n=== Summary ===")
    if env_test:
        print("✓ Production environment appears functional")
    else:
        print("✗ Production environment has issues requiring investigation")
        print("\nRecommendations:")
        print("1. Check production server logs for detailed error messages")
        print("2. Verify database connectivity in production")
        print("3. Confirm all dependencies are properly installed")
        print("4. Check environment variable configuration")
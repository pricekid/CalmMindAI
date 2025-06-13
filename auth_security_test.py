#!/usr/bin/env python3
"""
Comprehensive Authentication Security Test Suite
Tests all authentication features and security measures for Dear Teddy.
"""

import requests
import json
import time
from datetime import datetime

def test_authentication_security(base_url="http://localhost:5000"):
    """
    Comprehensive authentication security test suite.
    Tests registration, login, session management, and security features.
    """
    
    print(f"🔐 Authentication Security Test Suite")
    print(f"Testing against: {base_url}")
    print("=" * 50)
    
    timestamp = int(time.time())
    test_email = f"sectest{timestamp}@example.com"
    test_username = f"sectest{timestamp}"
    test_password = "SecurePass123!"
    
    results = {
        "registration": False,
        "login": False,
        "session_persistence": False,
        "logout": False,
        "duplicate_email_prevention": False,
        "empty_field_validation": False,
        "invalid_login_handling": False,
        "sql_injection_protection": False,
        "case_insensitive_email": False,
        "csrf_exemption": False,
        "secure_cookies": False
    }
    
    session = requests.Session()
    
    # Test 1: User Registration
    print("1. Testing user registration...")
    reg_data = {
        "username": test_username,
        "email": test_email,
        "password": test_password
    }
    
    reg_response = session.post(f"{base_url}/minimal-register", data=reg_data)
    if reg_response.status_code == 200 and "success" in reg_response.json():
        results["registration"] = True
        user_id = reg_response.json().get("user_id")
        print(f"   ✅ Registration successful - User ID: {user_id}")
    else:
        print(f"   ❌ Registration failed: {reg_response.text}")
        return results
    
    # Test 2: User Login
    print("2. Testing user login...")
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    login_response = session.post(f"{base_url}/stable-login", data=login_data, allow_redirects=False)
    if login_response.status_code == 302 and "/dashboard" in login_response.headers.get("Location", ""):
        results["login"] = True
        print("   ✅ Login successful - Redirected to dashboard")
    else:
        print(f"   ❌ Login failed: {login_response.status_code} - {login_response.text[:200]}")
    
    # Test 3: Session Persistence
    print("3. Testing session persistence...")
    dashboard_response = session.get(f"{base_url}/dashboard")
    if dashboard_response.status_code == 200:
        results["session_persistence"] = True
        print("   ✅ Session persists - Dashboard accessible")
    else:
        print(f"   ❌ Session failed: {dashboard_response.status_code}")
    
    # Test 4: Logout
    print("4. Testing logout functionality...")
    logout_response = session.get(f"{base_url}/logout", allow_redirects=False)
    if logout_response.status_code == 302:
        results["logout"] = True
        print("   ✅ Logout successful - Session terminated")
    else:
        print(f"   ❌ Logout failed: {logout_response.status_code}")
    
    # Test 5: Duplicate Email Prevention
    print("5. Testing duplicate email prevention...")
    dup_data = {
        "username": "duplicate_user",
        "email": test_email,
        "password": "AnotherPass123!"
    }
    
    dup_response = session.post(f"{base_url}/minimal-register", data=dup_data)
    if dup_response.status_code == 409 and "already registered" in dup_response.text:
        results["duplicate_email_prevention"] = True
        print("   ✅ Duplicate email properly rejected")
    else:
        print(f"   ❌ Duplicate email not handled: {dup_response.text}")
    
    # Test 6: Empty Field Validation
    print("6. Testing empty field validation...")
    empty_data = {
        "username": "",
        "email": "",
        "password": ""
    }
    
    empty_response = session.post(f"{base_url}/minimal-register", data=empty_data)
    if empty_response.status_code == 400 and "Empty fields" in empty_response.text:
        results["empty_field_validation"] = True
        print("   ✅ Empty fields properly rejected")
    else:
        print(f"   ❌ Empty field validation failed: {empty_response.text}")
    
    # Test 7: Invalid Login Handling
    print("7. Testing invalid login handling...")
    invalid_data = {
        "email": test_email,
        "password": "WrongPassword123!"
    }
    
    invalid_response = session.post(f"{base_url}/stable-login", data=invalid_data)
    if "Invalid email or password" in invalid_response.text:
        results["invalid_login_handling"] = True
        print("   ✅ Invalid login properly handled")
    else:
        print(f"   ❌ Invalid login not handled: {invalid_response.text[:200]}")
    
    # Test 8: SQL Injection Protection
    print("8. Testing SQL injection protection...")
    sql_data = {
        "email": "admin@example.com'; DROP TABLE user; --",
        "password": "anything"
    }
    
    sql_response = session.post(f"{base_url}/stable-login", data=sql_data)
    if "Invalid email or password" in sql_response.text and sql_response.status_code != 500:
        results["sql_injection_protection"] = True
        print("   ✅ SQL injection properly blocked")
    else:
        print(f"   ❌ SQL injection vulnerability: {sql_response.status_code}")
    
    # Test 9: Case-Insensitive Email
    print("9. Testing case-insensitive email login...")
    case_data = {
        "email": test_email.upper(),
        "password": test_password
    }
    
    case_response = session.post(f"{base_url}/stable-login", data=case_data, allow_redirects=False)
    if case_response.status_code == 302:
        results["case_insensitive_email"] = True
        print("   ✅ Case-insensitive email login works")
    else:
        print(f"   ❌ Case-insensitive email failed: {case_response.status_code}")
    
    # Test 10: CSRF Exemption
    print("10. Testing CSRF exemption...")
    csrf_response = session.post(f"{base_url}/stable-login", data=login_data)
    if csrf_response.status_code != 400:  # Should not fail due to missing CSRF token
        results["csrf_exemption"] = True
        print("   ✅ CSRF exemption working correctly")
    else:
        print(f"   ❌ CSRF exemption failed: {csrf_response.text}")
    
    # Test 11: Secure Cookie Configuration
    print("11. Testing secure cookie configuration...")
    cookie_response = session.get(f"{base_url}/stable-login")
    set_cookie = cookie_response.headers.get('Set-Cookie', '')
    if 'HttpOnly' in set_cookie and 'SameSite' in set_cookie:
        results["secure_cookies"] = True
        print("   ✅ Secure cookie configuration verified")
    else:
        print(f"   ❌ Insecure cookie configuration: {set_cookie}")
    
    # Summary
    print("\n" + "=" * 50)
    print("AUTHENTICATION SECURITY TEST RESULTS")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test, passed_status in results.items():
        status = "✅ PASS" if passed_status else "❌ FAIL"
        print(f"{test.replace('_', ' ').title():.<30} {status}")
    
    print(f"\nOverall Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL AUTHENTICATION SECURITY TESTS PASSED!")
    else:
        print(f"⚠️  {total-passed} security tests failed - review needed")
    
    return results

if __name__ == "__main__":
    test_authentication_security()
#!/usr/bin/env python3
"""
Create test user credentials for testing the application
"""
import requests
import os

def create_test_user():
    """Create a test user with known credentials"""
    base_url = "http://localhost:5000"
    
    # Test user credentials
    test_username = "testuser"
    test_email = "test@example.com"
    test_password = "test123"
    
    print(f"Creating test user:")
    print(f"Username: {test_username}")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    
    # Register the test user
    register_data = {
        'username': test_username,
        'email': test_email,
        'password': test_password
    }
    
    try:
        response = requests.post(
            f"{base_url}/minimal-register",
            data=register_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"\nRegistration response status: {response.status_code}")
        print(f"Registration response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Test user created successfully with ID: {result.get('user_id')}")
                return True
            else:
                print("❌ Registration failed")
                return False
        else:
            print("❌ Registration request failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

def create_returning_user():
    """Create a returning user (completed onboarding)"""
    base_url = "http://localhost:5000"
    
    # Returning user credentials
    test_username = "returninguser"
    test_email = "returning@example.com"
    test_password = "return123"
    
    print(f"\nCreating returning user:")
    print(f"Username: {test_username}")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    
    # Register the returning user
    register_data = {
        'username': test_username,
        'email': test_email,
        'password': test_password
    }
    
    try:
        response = requests.post(
            f"{base_url}/minimal-register",
            data=register_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"Registration response status: {response.status_code}")
        print(f"Registration response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Returning user created successfully with ID: {result.get('user_id')}")
                return True
            else:
                print("❌ Registration failed")
                return False
        else:
            print("❌ Registration request failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating returning user: {e}")
        return False

if __name__ == "__main__":
    print("Creating test user credentials...")
    
    success1 = create_test_user()
    success2 = create_returning_user()
    
    if success1 and success2:
        print("\n🎉 All test users created successfully!")
        print("\nTest Credentials:")
        print("=================")
        print("New User:")
        print("  Username: testuser")
        print("  Email: test@example.com")
        print("  Password: test123")
        print("")
        print("Returning User:")
        print("  Username: returninguser")
        print("  Email: returning@example.com")
        print("  Password: return123")
    else:
        print("\n💥 Some test users failed to create")
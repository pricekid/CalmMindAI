
#!/usr/bin/env python3
"""
Debug authentication issues locally
"""
import requests
import json

def test_local_auth():
    """Test authentication on local server"""
    base_url = "http://localhost:5000"
    
    print("🔍 Testing Local Authentication...")
    
    try:
        # Test registration page
        response = requests.get(f"{base_url}/register-simple", timeout=5)
        print(f"Registration page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Registration page loads successfully")
            
            # Test a simple registration
            test_data = {
                'username': 'debugtest',
                'email': 'debugtest@example.com', 
                'password': 'TestPass123!',
                'confirm_password': 'TestPass123!'
            }
            
            reg_response = requests.post(f"{base_url}/register-simple", data=test_data)
            print(f"Registration response: {reg_response.status_code}")
            
            if reg_response.status_code == 200:
                print("✅ Registration working locally")
            else:
                print(f"❌ Registration failed: {reg_response.text[:200]}")
        else:
            print(f"❌ Registration page failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Local server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_local_auth()

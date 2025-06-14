
#!/usr/bin/env python3
"""
Test connectivity and authentication on www.dearteddy.app
"""
import requests
import json
from datetime import datetime

def test_production_site():
    """Test the production Dear Teddy site"""
    base_url = "https://www.dearteddy.app"
    
    print(f"🔍 Testing production site: {base_url}")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    try:
        response = requests.get(base_url, timeout=10)
        print(f"✅ Site accessibility: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error response: {response.text[:300]}...")
            return False
            
    except Exception as e:
        print(f"❌ Site connectivity failed: {str(e)}")
        return False
    
    # Test 2: Registration page
    try:
        reg_response = requests.get(f"{base_url}/register-simple", timeout=10)
        print(f"✅ Registration page: {reg_response.status_code}")
        
        if reg_response.status_code != 200:
            print(f"❌ Registration page error: {reg_response.text[:200]}...")
        else:
            # Check for form fields
            if 'name="username"' in reg_response.text:
                print("✅ Registration form fields present")
            else:
                print("❌ Registration form fields missing")
                
    except Exception as e:
        print(f"❌ Registration page test failed: {str(e)}")
    
    # Test 3: Emergency production routes
    try:
        prod_status = requests.get(f"{base_url}/production-status", timeout=10)
        if prod_status.status_code == 200:
            status_data = prod_status.json()
            print(f"✅ Production status: {status_data}")
        else:
            print(f"⚠️  Production status route not available: {prod_status.status_code}")
    except Exception as e:
        print(f"⚠️  Production status check failed: {str(e)}")
    
    # Test 4: Database connectivity (indirect)
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health check: {health_data}")
        else:
            print(f"⚠️  Health check not available: {health_response.status_code}")
    except Exception as e:
        print(f"⚠️  Health check failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS:")
    print("1. Check if production environment variables are set")
    print("2. Verify database connection string")
    print("3. Ensure CSRF settings are compatible")
    print("4. Test emergency routes: /emergency-prod-register")

if __name__ == "__main__":
    test_production_site()

#!/usr/bin/env python3
"""
Script to fetch production logs from Render.com to diagnose login issues.
"""
import requests
import os
import json
from datetime import datetime

def get_render_logs():
    """
    Fetch logs from Render.com production deployment.
    Requires RENDER_API_KEY environment variable.
    """
    api_key = os.environ.get('RENDER_API_KEY')
    if not api_key:
        print("❌ RENDER_API_KEY environment variable not set")
        print("Please provide your Render API key to fetch production logs")
        return False
    
    # Render API endpoint for logs
    service_id = "srv-ctqgdej6l47c739tq3og"  # Dear Teddy service ID from logs
    base_url = "https://api.render.com/v1"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get service details first
        print("Fetching service information...")
        service_url = f"{base_url}/services/{service_id}"
        service_response = requests.get(service_url, headers=headers)
        
        if service_response.status_code == 200:
            service_data = service_response.json()
            print(f"Service: {service_data.get('name', 'Unknown')}")
            print(f"Status: {service_data.get('serviceDetails', {}).get('buildStatus', 'Unknown')}")
            print(f"URL: {service_data.get('serviceDetails', {}).get('url', 'Unknown')}")
        else:
            print(f"Failed to get service info: {service_response.status_code}")
            print(f"Response: {service_response.text}")
        
        # Get recent logs
        print("\nFetching recent production logs...")
        logs_url = f"{base_url}/services/{service_id}/logs"
        
        # Get logs from the last hour
        params = {
            'limit': 100,
            'cursor': '',
        }
        
        logs_response = requests.get(logs_url, headers=headers, params=params)
        
        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            logs = logs_data.get('logs', [])
            
            print(f"\n📋 Found {len(logs)} log entries")
            print("=" * 50)
            
            # Filter for login-related logs
            login_logs = []
            error_logs = []
            
            for log in logs:
                message = log.get('message', '')
                timestamp = log.get('timestamp', '')
                
                if any(keyword in message.lower() for keyword in ['login', 'auth', 'stable_login', 'error', 'exception']):
                    if 'error' in message.lower() or 'exception' in message.lower():
                        error_logs.append(log)
                    if 'login' in message.lower() or 'auth' in message.lower():
                        login_logs.append(log)
            
            # Show error logs first
            if error_logs:
                print(f"\n🚨 ERROR LOGS ({len(error_logs)} entries):")
                print("-" * 40)
                for log in error_logs[-10:]:  # Last 10 errors
                    timestamp = log.get('timestamp', '')
                    message = log.get('message', '')
                    print(f"[{timestamp}] {message}")
            
            # Show login-related logs
            if login_logs:
                print(f"\n🔐 LOGIN-RELATED LOGS ({len(login_logs)} entries):")
                print("-" * 40)
                for log in login_logs[-10:]:  # Last 10 login attempts
                    timestamp = log.get('timestamp', '')
                    message = log.get('message', '')
                    print(f"[{timestamp}] {message}")
            
            # Show all recent logs if no specific ones found
            if not error_logs and not login_logs:
                print("\n📝 RECENT LOGS:")
                print("-" * 40)
                for log in logs[-20:]:  # Last 20 logs
                    timestamp = log.get('timestamp', '')
                    message = log.get('message', '')
                    print(f"[{timestamp}] {message}")
            
            return True
            
        else:
            print(f"❌ Failed to fetch logs: {logs_response.status_code}")
            print(f"Response: {logs_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching logs: {str(e)}")
        return False

def test_production_login():
    """
    Test login against production to trigger log entries.
    """
    print("\n🧪 Testing production login to generate logs...")
    
    production_url = "https://dear-teddy.onrender.com"
    
    # Test credentials
    test_data = {
        'email': 'test@example.com',
        'password': 'test123'
    }
    
    try:
        # First get the login page to establish session
        session = requests.Session()
        login_page = session.get(f"{production_url}/stable-login")
        print(f"Login page status: {login_page.status_code}")
        
        # Attempt login
        login_response = session.post(
            f"{production_url}/stable-login",
            data=test_data,
            allow_redirects=False
        )
        
        print(f"Login attempt status: {login_response.status_code}")
        print(f"Response headers: {dict(login_response.headers)}")
        
        if login_response.status_code == 302:
            print(f"Redirect to: {login_response.headers.get('Location', 'Unknown')}")
        elif login_response.status_code == 200:
            if 'error' in login_response.text.lower():
                print("Login returned with error message")
            else:
                print("Login page returned (possible success or error)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing production login: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Render Production Log Fetcher")
    print("=" * 40)
    
    # Test production login first to generate fresh logs
    test_production_login()
    
    # Wait a moment for logs to propagate
    import time
    print("\nWaiting for logs to propagate...")
    time.sleep(3)
    
    # Fetch logs
    success = get_render_logs()
    
    if not success:
        print("\n💡 To use this script:")
        print("1. Get your Render API key from https://dashboard.render.com/account/api-keys")
        print("2. Set it as environment variable: export RENDER_API_KEY=your_key_here")
        print("3. Run this script again")
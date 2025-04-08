import requests
import re
from bs4 import BeautifulSoup

def test_admin_login():
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First get the login page to get the CSRF token
    response = session.get('http://localhost:5000/admin/login')
    print(f"Initial GET status code: {response.status_code}")
    
    # Extract the CSRF token using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
    print(f"CSRF token obtained: {csrf_token}")
    
    # Now attempt the login
    login_data = {
        'csrf_token': csrf_token,
        'username': 'admin',
        'password': 'admin123',
        'submit': 'Log In'
    }
    
    response = session.post('http://localhost:5000/admin/login', data=login_data, allow_redirects=True)
    print(f"Login POST status code: {response.status_code}")
    print(f"Final URL after redirects: {response.url}")
    
    # Check if login was successful by looking for admin dashboard elements
    if 'dashboard' in response.url:
        print("Login successful! Redirected to dashboard.")
    else:
        # Print any error messages
        soup = BeautifulSoup(response.text, 'html.parser')
        flash_messages = soup.select('.alert')
        if flash_messages:
            print("Error messages found:")
            for message in flash_messages:
                print(f"  - {message.text.strip()}")
        else:
            print("No error messages found, but login failed.")
            
    # Print the title to see where we are
    soup = BeautifulSoup(response.text, 'html.parser')
    if soup.title:
        print(f"Page title: {soup.title.string}")
    
    # Print some debugging info
    if 'Admin Login' in response.text:
        print("Still on the login page.")
    else:
        print("No longer on the login page.")
        
    return response.text

if __name__ == "__main__":
    test_admin_login()
"""
Test script to debug the login route functionality.
This test creates a test client to simulate HTTP requests to the login route.
"""
import os
import logging
from app import app, db
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_login_route(email, password):
    """
    Test the login route with the given credentials.
    
    Args:
        email: The user's email
        password: The user's password
        
    Returns:
        dict: Information about the login attempt
    """
    with app.test_client() as client:
        with app.app_context():
            # First check if the user exists
            from models import User
            user = User.query.filter_by(email=email).first()
            
            if not user:
                logger.error(f"User with email {email} not found in database")
                return {
                    "success": False,
                    "error": f"User with email {email} not found"
                }
            
            # Try to login
            logger.info(f"Attempting login with email: {email}")
            
            # Disable CSRF for this test
            app.config['WTF_CSRF_ENABLED'] = False
            
            try:
                # Send POST request to login route
                response = client.post('/login', data={
                    'email': email,
                    'password': password
                }, follow_redirects=False)
                
                logger.info(f"Login response: {response.status_code} - {response.location if hasattr(response, 'location') else 'No redirect'}")
                
                if response.status_code == 302:  # Redirect indicates success
                    redirect_url = response.location
                    logger.info(f"Login successful, redirecting to: {redirect_url}")
                    return {
                        "success": True,
                        "redirect_url": redirect_url
                    }
                else:
                    # Get the response data
                    response_data = response.get_data(as_text=True)
                    
                    # Check if it contains error messages
                    if "Login unsuccessful" in response_data:
                        logger.error("Login failed: Invalid credentials")
                        return {
                            "success": False,
                            "error": "Invalid credentials"
                        }
                    elif "error" in response_data.lower():
                        logger.error(f"Login failed with error page")
                        return {
                            "success": False,
                            "error": "Server error during login"
                        }
                    else:
                        logger.error(f"Login failed: Unknown reason")
                        return {
                            "success": False,
                            "error": "Unknown error"
                        }
            except Exception as e:
                logger.error(f"Exception during login test: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                # Re-enable CSRF
                app.config['WTF_CSRF_ENABLED'] = True

def main():
    """Main function to test login route."""
    # Get credentials from command line
    if len(sys.argv) < 3:
        print("Usage: python test_login_route.py <email> <password>")
        return

    email = sys.argv[1]
    password = sys.argv[2]
    
    # Test login route
    result = test_login_route(email, password)
    
    if result["success"]:
        print(f"Login test successful! Redirect URL: {result['redirect_url']}")
    else:
        print(f"Login test failed. Error: {result['error']}")

if __name__ == "__main__":
    main()
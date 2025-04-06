from werkzeug.security import check_password_hash, generate_password_hash
from admin_models import Admin

def test_admin_password():
    # Hardcoded admin account from Admin.get() method
    admin_hash = "pbkdf2:sha256:600000$zpbgMAIdCQZsHQnx$5ae4bc03dc4dde1cc18e8acf1c127aafa2bfa8c6f12beec3a683baa1a0d3a7a0"
    
    # Test with expected password
    password = "admin123"
    result = check_password_hash(admin_hash, password)
    print(f"Password check for 'admin123': {result}")
    
    # Generate a new hash for the expected password to see if it matches
    new_hash = generate_password_hash("admin123")
    print(f"New hash generated for 'admin123': {new_hash}")
    
    # Try to get the admin and check password directly
    admin = Admin.get(1)
    if admin:
        direct_check = admin.check_password("admin123")
        print(f"Direct password check for 'admin123': {direct_check}")
    else:
        print("Could not get admin user")

if __name__ == "__main__":
    test_admin_password()
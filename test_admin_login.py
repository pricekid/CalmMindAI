from werkzeug.security import check_password_hash, generate_password_hash
from admin_models import Admin

def test_admin_password():
    # Get the current hash used in the Admin model
    admin = Admin.get(1)
    
    if admin:
        # Test with expected password
        password = "admin123"
        
        # Direct check using Admin model's method
        direct_check = admin.check_password("admin123")
        print(f"Direct password check for 'admin123': {direct_check}")
        
        # Show the current hash being used
        print(f"Current hash in Admin model: {admin.password_hash}")
        
        # Generate a new hash for the expected password to see if it matches the format
        new_hash = generate_password_hash("admin123")
        print(f"New hash generated for 'admin123': {new_hash}")
        
        # Verify the new hash works with check_password_hash
        new_hash_check = check_password_hash(new_hash, "admin123")
        print(f"Verification of new hash: {new_hash_check}")
    else:
        print("Could not get admin user")

if __name__ == "__main__":
    test_admin_password()
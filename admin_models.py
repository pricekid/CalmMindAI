from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

class Admin(UserMixin):
    """
    Admin user model for Flask-Login.
    This is a simple implementation with a hardcoded admin account.
    """
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return a unique identifier for this admin user."""
        return f"admin_{self.id}"
    
    @staticmethod
    def get(user_id):
        """
        Required for Flask-Login. Returns the admin user if it matches the hardcoded ID.
        """
        if int(user_id) == 1:
            # Hardcoded admin account with pre-generated password hash for "admin123"
            admin_hash = "scrypt:32768:8:1$NSSgHSQAF7fVPQB3$a4d8f90b24c5827c5d19f5e0d40659e928a0068722bdf2d44c33c3c0f5450e8b98e82f777e4aa89f9d9045e727f7238cdc2f6543f2b1ef578d9e1c122203eed3a"
            return Admin(1, "admin", admin_hash)
        return None
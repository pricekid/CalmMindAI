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
        # For the admin account, just do a direct string comparison for now
        # This simplifies the login process for development
        if self.id == 1 and password == "admin123":
            return True
        # For any other admins, use the secure hash check
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return a unique identifier for this admin user."""
        return f"admin_{self.id}"
    
    @staticmethod
    def get(user_id):
        """
        Required for Flask-Login. Returns the admin user if it matches the hardcoded ID.
        """
        try:
            if str(user_id) == "1":
                # Create a placeholder hash - we'll check the raw password in check_password
                admin_hash = "placeholder_hash"
                return Admin(1, "admin", admin_hash)
        except (ValueError, TypeError):
            pass
        return None
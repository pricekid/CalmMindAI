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
        try:
            if str(user_id) == "1":
                # Use a static hash for consistency
                # The default password is "admin123"
                admin_hash = "scrypt:32768:8:1$awdIQ5jQp2D70Bxn$31d89a975f83d90e310ad591cb521e225454ca6fe06189d99c67e62cec380525fe6cc77b35b81159d3aa4c7e9f4d557afd8a4edb7d26eff9bdd6f6430a1fb790"
                return Admin(1, "admin", admin_hash)
        except (ValueError, TypeError):
            pass
        return None
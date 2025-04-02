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
            # Using a static hash so it doesn't change with every get() call
            admin_hash = "pbkdf2:sha256:600000$zpbgMAIdCQZsHQnx$5ae4bc03dc4dde1cc18e8acf1c127aafa2bfa8c6f12beec3a683baa1a0d3a7a0"
            return Admin(1, "admin", admin_hash)
        return None
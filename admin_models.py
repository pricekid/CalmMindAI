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
            # Generated fresh to ensure it works with our current werkzeug version
            admin_hash = "scrypt:32768:8:1$c049OmLL8Sc4X8Fk$1fb0d8d8dc2996eddddfc8218ee3e2463d9deca2bfda83ed2d1e3c5097dbca886926348f533415141cb7e4118ff7a7377f49e35a6c88b8c5fa4cc7a32f82bcf4"
            return Admin(1, "admin", admin_hash)
        return None
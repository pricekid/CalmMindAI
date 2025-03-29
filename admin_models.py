from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import logging

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
    
    @staticmethod
    def get(user_id):
        """
        Required for Flask-Login. Returns the admin user if it matches the hardcoded ID.
        """
        if user_id == 1:
            # Hardcoded admin account
            admin_hash = generate_password_hash("admin123")  # Default password
            return Admin(1, "admin", admin_hash)
        return None
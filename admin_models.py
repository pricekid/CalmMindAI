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
        logging.debug(f"Admin.get called with user_id: {user_id}")
        if int(user_id) == 1:
            # Hardcoded admin account - use a static hash instead of generating it each time
            # This ensures the same hash is used for comparison
            admin_hash = 'pbkdf2:sha256:600000$FjFuDq25zPdKjFQd$50e83bad91b3c58c9f83ecfafe04a7e15e3cac41d03d1b79ce714fbd4c8d2d3c'  # admin123
            logging.debug("Returning admin user")
            return Admin(1, "admin", admin_hash)
        logging.debug("No admin user found")
        return None
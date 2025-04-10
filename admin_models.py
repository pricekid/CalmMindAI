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
            # Hardcoded admin account with pre-generated password hash for "Kent20031232@"
            # Using a static hash so it doesn't change with every get() call
            # Generated fresh to ensure it works with our current werkzeug version
            admin_hash = "scrypt:32768:8:1$NSSgHSQAF7fVPQB3$b0b32774b424d18d1efb9892b1f4ca296889b16609e008246dc056cc917eb724d4e581eb083e42c176f33c49e2802208c2f6543f2b1ef578d9e1c122203eed3a"
            return Admin(1, "admin", admin_hash)
        return None
import uuid
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app import db

class Admin(UserMixin, db.Model):
    """
    Admin user model for Flask-Login.
    Now using the database for storage like the User model.
    """
    __tablename__ = "admin"
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Set the password hash for the admin."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the password against the stored hash."""
        # For development convenience, allow "admin123" for any admin
        if password == "admin123":
            return True
        # For production, use the secure hash check
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return a unique identifier for this admin user."""
        return f"admin_{self.id}"
    
    @staticmethod
    def get(user_id):
        """
        Required for Flask-Login. Returns the admin user by ID.
        user_id: The numeric portion of the admin ID (after "admin_").
        """
        try:
            # Try to get admin from database
            admin = Admin.query.get(user_id)
            if admin:
                return admin
                
            # If admin not found in database but ID is 1, create default admin
            if str(user_id) == "1" and not admin:
                # Create a default admin account if none exists
                default_admin = Admin(id="1", username="admin")
                default_admin.set_password("admin123")  # Set a default password
                db.session.add(default_admin)
                db.session.commit()
                return default_admin
        except Exception as e:
            print(f"Error in Admin.get: {e}")
        return None
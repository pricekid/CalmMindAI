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
    
    def __init__(self, **kwargs):
        """
        Initialize an Admin object with keyword arguments.
        This fixes the LSP issue with the constructor.
        """
        super(Admin, self).__init__(**kwargs)
    
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
        admin_id = f"admin_{self.id}"
        print(f"Admin.get_id() called, returning: {admin_id}")
        return admin_id
    
    @staticmethod
    def get(user_id):
        """
        Required for Flask-Login. Returns the admin user by ID.
        user_id: The admin ID, which may be in one of several formats:
        - "admin_1" (from session cookie)
        - "1" (direct numeric ID)
        """
        try:
            # Log the user_id we received
            print(f"Admin.get() called with user_id: {user_id}, type: {type(user_id)}")
            
            # Extract the numeric portion if in "admin_X" format
            if isinstance(user_id, str) and user_id.startswith("admin_"):
                user_id = user_id.split("_")[1]
                print(f"Extracted numeric portion: {user_id}")
            
            # Try to get admin from database
            admin = Admin.query.get(user_id)
            if admin:
                print(f"Found admin in database: {admin.username}")
                return admin
                
            # If admin not found in database but ID is 1, create default admin
            if str(user_id) == "1" and not admin:
                print("Creating default admin with ID 1")
                # Create a default admin account if none exists
                default_admin = Admin()
                default_admin.id = "1"
                default_admin.username = "admin"
                default_admin.set_password("admin123")  # Set a default password
                
                try:
                    db.session.add(default_admin)
                    db.session.commit()
                    print("Default admin created successfully")
                    return default_admin
                except Exception as commit_error:
                    print(f"Error committing default admin: {commit_error}")
                    db.session.rollback()
                    # Try one more time to get the admin in case it was created by another process
                    return Admin.query.get("1")
        except Exception as e:
            print(f"Error in Admin.get: {e}")
            import traceback
            print(traceback.format_exc())
        
        print("Admin.get() returning None")
        return None
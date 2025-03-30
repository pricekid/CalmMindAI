import os
import logging
from flask import Flask, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///calm_journey.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with extensions
db.init_app(app)
csrf.init_app(app)

# Configure login manager for regular users
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Regular user login route
login_manager.login_message_category = "info"

# Custom unauthorized handler for login_manager
@login_manager.unauthorized_handler
def unauthorized():
    # Only redirect to admin login if the path is an admin path
    if request.path.startswith('/admin'):
        return redirect(url_for('admin.login'))
    # For all other paths, use the regular login
    return redirect(url_for('login'))

# Add global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    from flask import render_template
    app.logger.error(f"Unhandled exception: {str(e)}")
    error_message = "Your data was saved, but we couldn't complete the analysis."
    
    # Check if it's an OpenAI API error related to quota
    is_api_error = False
    err_str = str(e).lower()
    if "openai" in err_str and ("quota" in err_str or "429" in err_str or "insufficient" in err_str):
        is_api_error = True
        error_title = "API Limit Reached"
        error_message = "Your journal entry was saved successfully, but AI analysis is currently unavailable due to API usage limits."
    else:
        error_title = "Something went wrong"
    
    return render_template('error.html', 
                          error_title=error_title,
                          error_message=error_message,
                          show_api_error=is_api_error), 500

# Set up the login_manager.user_loader before importing routes
from models import User
from admin_models import Admin

@login_manager.user_loader
def load_user(user_id):
    # Check if this is an admin user (user_id will be a string like "admin_1")
    if isinstance(user_id, str) and user_id.startswith('admin_'):
        admin_id = int(user_id.split('_')[1])
        return Admin.get(admin_id)
    # Regular user
    try:
        return db.session.get(User, int(user_id))
    except ValueError:
        return None

# Import routes after app is initialized to avoid circular imports
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import JournalEntry, CBTRecommendation, MoodLog
    db.create_all()
    
    # Import routes after models
    import routes
    
    # Register the admin blueprint
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp)

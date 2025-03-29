import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
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

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# Admin login manager setup for handling admin users
admin_login_manager = LoginManager()
admin_login_manager.init_app(app)
admin_login_manager.login_view = "admin.login"
admin_login_manager.login_message_category = "info"

# Add global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    from flask import render_template, request
    import traceback
    
    # Get complete exception traceback
    tb = traceback.format_exc()
    app.logger.error(f"Unhandled exception: {str(e)}\n{tb}")
    
    # Special handling for admin routes
    if request.path.startswith('/admin'):
        app.logger.error(f"Admin route error: {request.path}")
        if '/admin/login' in request.path:
            # Specific handling for login page
            try:
                return render_template('admin/error.html', error=f"Login error: {str(e)}"), 500
            except Exception as template_error:
                app.logger.error(f"Error rendering admin error template: {str(template_error)}")
                return f"Admin login error: {str(e)}", 500
        
        try:
            return render_template('admin/error.html', error=str(e)), 500
        except Exception as template_error:
            app.logger.error(f"Error rendering admin error template: {str(template_error)}")
            return f"Admin area error: {str(e)}", 500
    
    # Default error handling for non-admin routes
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
    
    try:
        return render_template('error.html', 
                            error_title=error_title,
                            error_message=error_message,
                            show_api_error=is_api_error), 500
    except Exception as template_error:
        app.logger.error(f"Error rendering error template: {str(template_error)}")
        return f"Application error: {str(e)}", 500

# Import routes after app is initialized to avoid circular imports
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, JournalEntry, CBTRecommendation, MoodLog
    db.create_all()
    
    # Import routes after models
    import routes
    
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Import admin model for admin login
    from admin_models import Admin
    
    @admin_login_manager.user_loader
    def load_admin(user_id):
        logging.debug(f"Loading admin with ID: {user_id}")
        try:
            admin = Admin.get(int(user_id))
            if admin:
                logging.debug(f"Found admin: {admin.username}")
            else:
                logging.debug("Admin not found")
            return admin
        except Exception as e:
            logging.error(f"Error loading admin: {str(e)}")
            return None
        
    # Register the admin blueprint
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp)

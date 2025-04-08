import os
import logging
from flask import Flask, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user, login_required as original_login_required
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()
mail = Mail()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///calm_journey.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 60,
    "isolation_level": "READ COMMITTED"  # More forgiving isolation level for general web apps
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure CSRF protection with a longer timeout
app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # Extend CSRF token expiration to 1 hour

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Base URL for links in emails and notifications
# In production, this should be set to the full URL of your application
# For example, 'https://your-app.replit.app'
# Use environment variable if available, otherwise URLs will be relative
app.config['BASE_URL'] = os.environ.get('BASE_URL', '')

# Initialize the app with extensions
db.init_app(app)
csrf.init_app(app)
mail.init_app(app)

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
    from flask import render_template, redirect, url_for
    from json.decoder import JSONDecodeError
    
    app.logger.error(f"Unhandled exception: {str(e)}")
    error_message = "Your data was saved, but we couldn't complete the analysis."
    
    # Check if it's a JSON parsing error (which is likely from OpenAI response)
    err_str = str(e).lower()
    
    # Special handler for the specific JSON parsing error we're seeing
    if isinstance(e, JSONDecodeError) or "expected token" in err_str or "json" in err_str:
        app.logger.error(f"JSON parsing error: {str(e)}")
        
        # Check if we're already processing an error to prevent redirect loops
        if request.path == '/dashboard' and 'handling_error' not in request.environ:
            # Set a flag in the request environment to prevent loops
            request.environ['handling_error'] = True
            
            # Just render the dashboard template with minimal data
            from models import JournalEntry, MoodLog
            from sqlalchemy import desc
            from datetime import datetime, timedelta
            
            # Get basic data for dashboard
            recent_entries = []
            mood_dates = []
            mood_scores = []
            weekly_summary = {}
            
            # Only try to get current_user data if authenticated
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                try:
                    # Get recent journal entries
                    recent_entries = JournalEntry.query.filter_by(user_id=current_user.id)\
                        .order_by(desc(JournalEntry.created_at)).limit(5).all()
                    
                    # Get mood data for chart (last 7 days)
                    seven_days_ago = datetime.utcnow() - timedelta(days=7)
                    mood_logs = MoodLog.query.filter(
                        MoodLog.user_id == current_user.id,
                        MoodLog.created_at >= seven_days_ago
                    ).order_by(MoodLog.created_at).all()
                    
                    # Format mood data for chart.js
                    mood_dates = [log.created_at.strftime('%Y-%m-%d') for log in mood_logs]
                    mood_scores = [log.mood_score for log in mood_logs]
                    
                    # Get weekly summary if available
                    weekly_summary = current_user.get_weekly_summary()
                except Exception as inner_e:
                    app.logger.error(f"Error fetching dashboard data: {str(inner_e)}")
            
            # Use a default coping statement
            coping_statement = "Mira suggests: Take a moment to breathe deeply. Remember that your thoughts don't define you, and this feeling will pass."
            
            # Get form for mood logging
            from forms import MoodLogForm
            mood_form = MoodLogForm()
            
            # Show a flash message about the error
            flash("Your dashboard is ready, but we couldn't generate a personalized message at this time.", "info")
            
            return render_template('dashboard.html', 
                                  title='Dashboard',
                                  recent_entries=recent_entries,
                                  mood_dates=mood_dates,
                                  mood_scores=mood_scores,
                                  coping_statement=coping_statement,
                                  mood_form=mood_form,
                                  weekly_summary=weekly_summary), 200
            
        # For other routes with JSON parsing errors, show a friendly message
        error_title = "Processing Issue"
        error_message = "We had a minor issue processing your data, but your information was saved successfully."
        return render_template('error.html', 
                             error_title=error_title,
                             error_message=error_message), 200
    
    # Check if it's a CSRF error
    if "csrf" in err_str:
        error_title = "Session Expired"
        error_message = "Your session has expired. Please refresh the page and try again."
        return render_template('error.html', 
                              error_title=error_title,
                              error_message=error_message,
                              show_csrf_error=True), 400
    
    # Check if it's an OpenAI API error related to quota
    is_api_error = False
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

# Create a custom login_required decorator that checks user type
def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        # First check if user is authenticated at all
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        
        # Check if current route is for regular users but user is an admin
        if not request.path.startswith('/admin') and hasattr(current_user, 'get_id') and current_user.get_id().startswith('admin_'):
            flash('You are logged in as an admin. Regular user pages are not accessible.', 'warning')
            return redirect(url_for('admin.dashboard'))
            
        # Check if current route is for admins but user is not an admin
        if request.path.startswith('/admin') and (not hasattr(current_user, 'get_id') or not current_user.get_id().startswith('admin_')):
            flash('You need admin privileges to access this page.', 'warning')
            return redirect(url_for('dashboard'))
            
        return f(*args, **kwargs)
    return decorated_view

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
        with db.session.begin():  # Start a new transaction
            return db.session.get(User, int(user_id))
    except ValueError:
        return None
    except Exception as e:
        # Log the error and return None to force re-login
        app.logger.error(f"Database error in load_user: {str(e)}")
        # Try to rollback any failed transaction
        try:
            db.session.rollback()
        except:
            pass
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
    
    # Register the notification blueprint
    from notification_routes import notification_bp
    app.register_blueprint(notification_bp)

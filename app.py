import os
import logging
from flask import Flask, url_for, redirect, request, flash, render_template, session
from flask_login import LoginManager, current_user, login_required as original_login_required
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_session import Session
from functools import wraps

# Import shared database extension
from extensions import db

# Import Render.com compatibility module
try:
    from render_compatibility import init_render_compatibility, is_render_environment
    has_render_compatibility = True
except ImportError:
    has_render_compatibility = False

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask extensions
csrf = CSRFProtect()
mail = Mail()
sess = Session()

def create_app():
    """Application factory to create Flask app with proper initialization"""
    app = Flask(__name__)
    
    # Configure secret key
    if os.environ.get("SESSION_SECRET"):
        app.secret_key = os.environ.get("SESSION_SECRET")
    else:
        import secrets
        app.logger.warning("No SESSION_SECRET found, generating a temporary one")
        app.secret_key = secrets.token_hex(32)
    
    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize database with app
    db.init_app(app)
    
    return app

# Create app instance
app = create_app()

# Add custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(s):
    """Convert newlines to HTML line breaks"""
    if s is None:
        return ""
    return s.replace('\n', '<br>')

# Add custom CSRF token context processor that works reliably
@app.context_processor
def inject_csrf_token():
    """Make CSRF token function available in all templates"""
    def csrf_token():
        try:
            from flask_wtf.csrf import generate_csrf
            return generate_csrf()
        except Exception:
            return ""
    return dict(csrf_token=csrf_token)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///calm_journey.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 60,
    "pool_size": 10,
    "max_overflow": 20,
    "isolation_level": "READ COMMITTED",  # More forgiving isolation level for general web apps
    "connect_args": {
        "connect_timeout": 10
    }
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure CSRF protection with consistent settings
app.config["WTF_CSRF_TIME_LIMIT"] = 7200  # 2 hour token expiration (extended)
app.config["WTF_CSRF_SSL_STRICT"] = False  # Allow CSRF token on HTTP
app.config["WTF_CSRF_ENABLED"] = True  # Keep CSRF globally enabled
app.config["WTF_CSRF_METHODS"] = ['POST', 'PUT', 'PATCH', 'DELETE']  # Only protect data-changing methods
app.config["WTF_CSRF_CHECK_DEFAULT"] = True  # Apply CSRF checking by default
app.config["WTF_CSRF_FIELD_NAME"] = "csrf_token"  # Consistent field name

# Disable Flask-WTF's automatic context processor to prevent conflicts
app.config["WTF_CSRF_CONTEXT_GLOBAL"] = False

# Configure session cookies with secure settings
from datetime import timedelta
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Compatible with most browsers
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Extended session lifetime
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions on filesystem for reliability
app.config['SESSION_USE_SIGNER'] = True  # Add a signature to session cookies
app.config['SESSION_PERMANENT'] = True  # Make sessions permanent by default

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

# Initialize CSRF with authentication endpoint exemptions
csrf.init_app(app)

# Exempt authentication endpoints from CSRF protection
AUTH_EXEMPT_PATHS = [
    '/minimal-register', '/auth-register', '/auth-login', '/auth-test-login',
    '/production-register', '/production-login', '/direct-register', '/direct-login',
    '/stable-login', '/emergency-register', '/test-login', '/register', '/login'
]

# Apply CSRF exemption using before_request handler
@app.before_request
def exempt_auth_endpoints():
    """Exempt authentication endpoints from CSRF validation"""
    if request.path in AUTH_EXEMPT_PATHS and request.method == 'POST':
        csrf._exempt_views.add(request.endpoint)

# Additional route-specific exemptions
for path in AUTH_EXEMPT_PATHS:
    try:
        csrf.exempt(path)
    except:
        pass

# Remove Flask-WTF's automatic csrf_token injection after initialization to prevent conflicts
if 'csrf_token' in app.jinja_env.globals:
    del app.jinja_env.globals['csrf_token']
mail.init_app(app)
sess.init_app(app)

# Apply Render.com compatibility settings if available
if has_render_compatibility:
    app = init_render_compatibility(app)
    app.logger.info(f"Render compatibility settings applied: {app.config['IS_RENDER']}")

# Apply CSRF debug middleware to log token validation details
from csrf_debug import CSRFDebugMiddleware
app.wsgi_app = CSRFDebugMiddleware(app.wsgi_app)

# Configure login manager for regular users
login_manager = LoginManager()
login_manager.init_app(app)
# Use direct path instead of route name
login_manager.login_view = "/stable-login"  # Direct path to avoid url_for issues
login_manager.login_message_category = "info"

# Custom unauthorized handler for login_manager
@login_manager.unauthorized_handler
def unauthorized():
    # Only redirect to admin login if the path is an admin path
    if request.path.startswith('/admin'):
        # Use direct path instead of url_for
        return redirect('/admin/login')
    # For all other paths, use the stable login path
    # Use direct path instead of url_for
    return redirect('/stable-login')

# Add global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    from flask import render_template, redirect, url_for, Response
    from json.decoder import JSONDecodeError
    from flask_wtf.csrf import CSRFError
    
    # Don't handle CSRF validation errors - let them be handled normally
    if isinstance(e, CSRFError) or "'str' object is not callable" in str(e):
        return None  # Let Flask handle the error normally
    
    app.logger.error(f"Unhandled exception: {str(e)}")
    error_message = "Your data was saved, but we couldn't complete the analysis."
    
    # Check if it's a JSON parsing error (which is likely from OpenAI response)
    err_str = str(e).lower()
    
    # For BuildError exceptions (URL building issues) - avoid template rendering which might cause infinite recursion
    if "builderror" in err_str or "could not build url" in err_str:
        app.logger.error(f"URL build error: {str(e)}")
        emergency_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dear Teddy - Error</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a; color: #f8f9fa; }
                .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
                h1 { color: #dc3545; }
                .btn { display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
                .btn-primary { background-color: #0d6efd; color: white; }
                .btn-light { background-color: #f8f9fa; color: #212529; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Navigation Error</h1>
                <p>We're having trouble with some of our internal links. We're working to fix this issue.</p>
                <p><a href="/" class="btn btn-primary">Go to Home Page</a> &nbsp; <a href="javascript:history.back()" class="btn btn-light">Go Back</a></p>
            </div>
        </body>
        </html>
        """
        return Response(emergency_html, 500, content_type='text/html')
    
    # Special handler for the specific JSON parsing error we're seeing
    if isinstance(e, JSONDecodeError) or "expected token" in err_str or "json" in err_str:
        app.logger.error(f"JSON parsing error: {str(e)}")
        
        # For login routes, redirect to the basic login page
        if '/login' in request.path or '/sign-in' in request.path or '/signin' in request.path:
            app.logger.info(f"Redirecting login JSON error to basic login page. Path: {request.path}")
            
            # Render the basic login template directly to avoid additional redirects
            try:
                # Generate a CSRF token for the login form to avoid CSRF errors
                from flask_wtf.csrf import generate_csrf
                csrf_token = generate_csrf()
                
                # Create an emergency login form that doesn't depend on the normal routes
                emergency_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Login - Dear Teddy</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
                    <link rel="stylesheet" href="/static/css/styles.css">
                    <style>
                        body {{ background-color: #1a1a1a; color: #f8f9fa; }}
                        .card {{ background-color: #212529; border: none; }}
                        .card-header {{ background-color: #0d6efd; color: white; }}
                        .form-control {{ background-color: #343a40; color: #f8f9fa; border-color: #495057; }}
                        .form-control:focus {{ background-color: #343a40; color: #f8f9fa; }}
                        .btn-primary {{ background-color: #0d6efd; }}
                    </style>
                </head>
                <body>
                    <div class="container mt-5">
                        <div class="row">
                            <div class="col-md-6 mx-auto">
                                <div class="card shadow">
                                    <div class="card-header">
                                        <h3 class="mb-0">Login to Dear Teddy</h3>
                                    </div>
                                    <div class="card-body">
                                        <form method="POST" action="/basic-login">
                                            <input type="hidden" name="csrf_token" value="{csrf_token}">
                                            <div class="mb-3">
                                                <label for="email" class="form-label">Email Address</label>
                                                <input type="email" class="form-control" id="email" name="email" required>
                                            </div>
                                            <div class="mb-3">
                                                <label for="password" class="form-label">Password</label>
                                                <input type="password" class="form-control" id="password" name="password" required>
                                            </div>
                                            <div class="mb-3 form-check">
                                                <input type="checkbox" class="form-check-input" id="remember" name="remember">
                                                <label class="form-check-label" for="remember">Remember me</label>
                                            </div>
                                            <div class="d-grid">
                                                <button type="submit" class="btn btn-primary">Login</button>
                                            </div>
                                        </form>
                                        <div class="mt-3 text-center">
                                            <p>Don't have an account? <a href="/register">Sign up</a></p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                return Response(emergency_html, 200, content_type='text/html')
            except Exception as login_error:
                app.logger.error(f"Failed to render emergency login: {str(login_error)}")
                return redirect('/basic-login')
        
        # For dashboard route, just redirect back to dashboard without the analysis
        elif request.path == '/dashboard':
            # Show a flash message about the error
            flash("Your dashboard is ready, but we couldn't generate a personalized message at this time.", "info")
            # Redirect instead of trying to render the template directly
            # Use direct path instead of url_for
            return redirect('/dashboard')
            
        # For journal-related JSON errors, which might be from the reflection feature
        elif '/journal' in request.path:
            app.logger.info(f"Journal-related JSON error: {request.path}")
            
            # If it's specifically from the save-reflection endpoint
            if '/journal/save-reflection' in request.path:
                # Return a JSON response with error details
                from flask import jsonify
                return jsonify({
                    "error": "Could not process your reflection due to a technical issue",
                    "success": False,
                    "message": "Your reflection was not saved. Please try again."
                }), 400
                
            # For other journal routes, just redirect to the journal list
            else:
                flash("We encountered an issue processing your request, but your journal entries are safe.", "info")
                return redirect('/journal')
        
        # For journal routes, provide a specific message related to journaling    
        elif '/journal' in request.path:
            emergency_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dear Teddy - Journal Processing</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a; color: #f8f9fa; }
                    .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
                    h1 { color: #0d6efd; }
                    .btn { display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
                    .btn-primary { background-color: #0d6efd; color: white; }
                    .btn-light { background-color: #f8f9fa; color: #212529; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Journal Entry Saved</h1>
                    <p>Your journal entry was saved successfully, but we're having trouble with the AI analysis right now.</p>
                    <p>You can view your journal entries or try again later.</p>
                    <p><a href="/journal" class="btn btn-primary">View Journal Entries</a> &nbsp; <a href="/dashboard" class="btn btn-light">Go to Dashboard</a></p>
                </div>
            </body>
            </html>
            """
            return Response(emergency_html, 200, content_type='text/html')
            
        # For other routes with JSON parsing errors, use a simple response to avoid template issues
        else:
            emergency_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dear Teddy - Processing Issue</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a; color: #f8f9fa; }
                    .container { max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }
                    h1 { color: #dc3545; }
                    .btn { display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
                    .btn-primary { background-color: #0d6efd; color: white; }
                    .btn-light { background-color: #f8f9fa; color: #212529; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Processing Issue</h1>
                    <p>We had a minor issue processing your data, but your information was saved successfully.</p>
                    <p>This is likely a temporary issue. You can try refreshing the page or go back to the dashboard.</p>
                    <p><a href="/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="javascript:history.back()" class="btn btn-light">Go Back</a></p>
                </div>
            </body>
            </html>
            """
            return Response(emergency_html, 200, content_type='text/html')
    
    # Check if it's a CSRF error
    if "csrf" in err_str:
        app.logger.warning(f"CSRF validation error: {str(e)}")
        error_title = "Session Expired"
        error_message = "Your session has expired. Please refresh the page and try again."
        
        # For login routes, redirect to the stable login
        if 'login' in request.path.lower() or request.path == '/':
            flash('Your session has expired. Please try logging in again.', 'warning')
            return redirect('/stable-login')
            
        try:
            return render_template('error.html', 
                                  error_title=error_title,
                                  error_message=error_message,
                                  show_csrf_error=True), 400
        except Exception as template_error:
            app.logger.error(f"Error rendering template: {str(template_error)}")
            return Response(f"Session expired. Please <a href='/stable-login'>login again</a>.", 400, content_type='text/html')
    
    # Check if it's an OpenAI API error related to quota
    is_api_error = False
    if "openai" in err_str and ("quota" in err_str or "429" in err_str or "insufficient" in err_str):
        is_api_error = True
        error_title = "API Limit Reached"
        error_message = "Your journal entry was saved successfully, but AI analysis is currently unavailable due to API usage limits."
    # Check for 'form' is undefined errors
    elif "'form' is undefined" in err_str or "'form'" in err_str:
        # Redirect to journal list page with a friendly message
        flash("Your journal entry was saved! You can view it in your journal list.", "success")
        if 'entry_id' in request.view_args:
            # Try to use the entry_id from the URL if available
            entry_id = request.view_args.get('entry_id')
            # Use direct path instead of url_for
            return redirect('/journal'), 302
    else:
        error_title = "Something went wrong"
    
    # Add any potentially missing template variables
    template_vars = {
        'error_title': error_title,
        'error_message': error_message,
        'show_api_error': is_api_error
    }
    
    try:
        return render_template('error.html', **template_vars), 500
    except Exception as template_error:
        app.logger.error(f"Error rendering template: {str(template_error)}")
        emergency_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dear Teddy - Error</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a; color: #f8f9fa; }}
                .container {{ max-width: 800px; margin: 40px auto; padding: 20px; background-color: #212529; border-radius: 8px; }}
                h1 {{ color: #dc3545; }}
                .btn {{ display: inline-block; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 20px; }}
                .btn-primary {{ background-color: #0d6efd; color: white; }}
                .btn-light {{ background-color: #f8f9fa; color: #212529; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{error_title}</h1>
                <p>{error_message}</p>
                <p>We encountered an issue while processing your request. The application is still running normally though.</p>
                <p><a href="/dashboard" class="btn btn-primary">Go to Dashboard</a> &nbsp; <a href="javascript:history.back()" class="btn btn-light">Go Back</a></p>
            </div>
        </body>
        </html>
        """
        return Response(emergency_html, 500, content_type='text/html')

# Create a custom login_required decorator that checks user type
def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        # First check if user is authenticated at all
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        
        # Check for admin impersonation mode
        is_admin_impersonating = session.get('is_admin_impersonating') == True
        
        # Check if current route is for regular users but user is an admin
        if (not request.path.startswith('/admin') and 
            hasattr(current_user, 'get_id') and 
            current_user.get_id().startswith('admin_') and
            not is_admin_impersonating):
            flash('You are logged in as an admin. Regular user pages are not accessible.', 'warning')
            # Use direct path instead of url_for
            return redirect('/admin/dashboard')
            
        # Check if current route is for admins but user is not an admin
        if request.path.startswith('/admin') and (not hasattr(current_user, 'get_id') or not current_user.get_id().startswith('admin_')):
            # If in impersonation mode and trying to access admin routes, let them return to admin
            if is_admin_impersonating and request.path.startswith('/admin/return-to-admin'):
                pass  # Allow access to return-to-admin route
            else:
                flash('You need admin privileges to access this page.', 'warning')
                # Use direct path instead of url_for
                return redirect('/dashboard')
            
        return f(*args, **kwargs)
    return decorated_view

# Set up the login_manager.user_loader before importing routes
from models import User
from admin_models import Admin

# Import emergency admin blueprints
try:
    from emergency_admin import emergency_admin_bp
    has_emergency_admin = True
except ImportError:
    app.logger.warning("Emergency admin module not available")
    has_emergency_admin = False
    
# Import standalone admin blueprint
try:
    from emergency_standalone import standalone_admin_bp
    has_standalone_admin = True
except ImportError:
    app.logger.warning("Standalone admin module not available")
    has_standalone_admin = False

@login_manager.user_loader
def load_user(user_id):
    app.logger.debug(f"load_user called with user_id: {user_id}, type: {type(user_id)}")
    
    # Check if this is an admin user (user_id will be a string like "admin_1")
    if isinstance(user_id, str) and user_id.startswith('admin_'):
        try:
            admin_id = user_id.split('_')[1]
            app.logger.debug(f"Extracted admin_id: {admin_id} from user_id: {user_id}")
            admin = Admin.get(admin_id)
            app.logger.debug(f"Admin.get({admin_id}) returned: {admin}")
            return admin
        except Exception as e:
            app.logger.error(f"Error loading admin user: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            return None
    
    # Regular user
    try:
        return User.query.get(user_id)
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
    
    # Register SendGrid email-based password reset functionality
    try:
        from password_reset import setup_password_reset
        setup_password_reset(app)
        app.logger.info("Password reset functionality enabled with SendGrid")
    except ImportError as e:
        app.logger.warning(f"Password reset module not available: {str(e)}")
        
    # We're using the original password reset module as it's already properly registered
        
    # Register admin login-as-user functionality
    try:
        from admin_login_as_user import setup_routes
        setup_routes(app)
        app.logger.info("Admin login-as-user functionality enabled")
    except ImportError:
        app.logger.warning("Admin login-as-user module not available")
    
    # Register the notification blueprint
    from notification_routes import notification_bp
    app.register_blueprint(notification_bp)
    
    # Register the journal blueprint
    from journal_routes import journal_bp
    app.register_blueprint(journal_bp, name='journal_blueprint')
    
    # Register the account blueprint for specialized account handling
    from account_routes import account_bp
    app.register_blueprint(account_bp)
    
    # Register marketing integration for dearteddy.app connection
    try:
        from marketing_integration import register_marketing_integration
        register_marketing_integration(app)
        app.logger.info("Marketing integration registered successfully")
    except ImportError as e:
        app.logger.warning(f"Marketing integration not available: {str(e)}")
    
    # Register the login blueprint for specialized login handling
    try:
        from login_routes import login_bp
        app.register_blueprint(login_bp)
        app.logger.info("Login routes registered successfully")
    except ImportError:
        app.logger.warning("Login routes module not available")
    
    # Comment out missing basic_login blueprint that's no longer needed
    # since we implemented the login directly in routes.py
    """
    # Register the basic login blueprint with minimal dependencies
    from basic_login import basic_login_bp
    app.register_blueprint(basic_login_bp)
    """
    
    # Try to register simple login as a fallback
    try:
        from simple_login import simple_login_bp
        app.register_blueprint(simple_login_bp)
        app.logger.info("Simple login fallback registered successfully")
    except ImportError:
        app.logger.warning("Simple login module not available")
    
    # Try to register test reflection page
    try:
        from test_journal_reflection import test_reflection_bp
        app.register_blueprint(test_reflection_bp)
        app.logger.info("Test reflection routes registered successfully")
    except ImportError:
        app.logger.warning("Test reflection module not available")
        
    # Enhanced Mira testing has been removed per user request
    # The relevant files (test_enhanced_mira.py and templates/test_enhanced_mira.html) are still available
    # but not registered with the application
    
    # Register the simple dashboard for emergency access
    try:
        from simple_dashboard import simple_dashboard_bp
        app.register_blueprint(simple_dashboard_bp)
        app.logger.info("Simple dashboard registered successfully")
    except ImportError:
        app.logger.warning("Simple dashboard module not available")
    
    # Register the completely standalone login system
    try:
        from special_login import special_login_bp
        app.register_blueprint(special_login_bp)
        app.logger.info("Special login routes registered successfully")
    except ImportError:
        app.logger.warning("Special login module not available")
    
    # Register the standalone reflection test page
    try:
        from standalone_reflection_test import reflection_test_bp
        app.register_blueprint(reflection_test_bp)
        app.logger.info("Standalone reflection test routes registered successfully")
    except ImportError:
        app.logger.warning("Standalone reflection test module not available")
    
    # Register the simple registration blueprint with minimal dependencies
    try:
        from simple_register import simple_register_bp
        app.register_blueprint(simple_register_bp)
        app.logger.info("Simple registration blueprint registered successfully")
    except ImportError:
        app.logger.warning("Simple registration module not available")
    
    # Register working registration system (CSRF-exempt)
    try:
        from working_register import working_register_bp
        csrf.exempt(working_register_bp)
        app.register_blueprint(working_register_bp)
        app.logger.info("Working registration system registered successfully")
    except ImportError:
        app.logger.warning("Working registration module not available")
    
    # Register final registration system (completely isolated)
    try:
        from final_register import final_register_bp
        csrf.exempt(final_register_bp)
        app.register_blueprint(final_register_bp)
        app.logger.info("Final registration system registered successfully")
    except ImportError:
        app.logger.warning("Final registration module not available")
    
    # Register the clean, fixed registration blueprint
    try:
        from simple_register_fixed import simple_register_bp
        csrf.exempt(simple_register_bp)
        app.register_blueprint(simple_register_bp)
        app.logger.info("Clean registration blueprint registered successfully")
    except ImportError:
        app.logger.warning("Clean registration module not available")
    
    # Register minimal registration blueprint (backup)
    try:
        from minimal_register import bp as minimal_register_bp
        csrf.exempt(minimal_register_bp)
        app.register_blueprint(minimal_register_bp)
        app.logger.info("Minimal registration blueprint registered successfully")
    except ImportError:
        app.logger.warning("Minimal registration module not available")
    
    # We're keeping emergency_login_main.py, emergency_direct_login.py, and emergency_app.py
    # but removing redundant emergency files
    try:
        from emergency_login_main import emergency_main_bp
        app.register_blueprint(emergency_main_bp)
        app.logger.info("Emergency main login blueprint registered successfully")
    except ImportError:
        app.logger.warning("Emergency main login module not available")
    
    # Register the simple text-to-speech blueprint (keep browser-based TTS)
    try:
        from simple_tts import tts_simple_bp
        app.register_blueprint(tts_simple_bp)
        app.logger.info("Simple TTS blueprint registered successfully")
    except ImportError:
        app.logger.warning("Simple TTS module not available")
    
    # Register the direct TTS blueprint (serves audio directly without CSRF issues)
    try:
        from direct_tts import direct_tts_bp
        app.register_blueprint(direct_tts_bp)
        app.logger.info("Direct TTS blueprint registered successfully")
    except ImportError:
        app.logger.warning("Direct TTS module not available")
    
    # Register the simplified direct TTS blueprint
    try:
        from simple_direct_tts import simple_direct_tts_bp
        app.register_blueprint(simple_direct_tts_bp)
        app.logger.info("Simple direct TTS blueprint registered successfully")
    except ImportError:
        app.logger.warning("Simple direct TTS module not available")
    
    # Register TTS routes for test page
    try:
        from tts_routes import tts_routes_bp
        app.register_blueprint(tts_routes_bp)
        app.logger.info("TTS routes blueprint registered successfully")
    except ImportError:
        app.logger.warning("TTS routes module not available")
    
    # Register premium TTS service
    try:
        from premium_tts_service import premium_tts_bp
        app.register_blueprint(premium_tts_bp)
        app.logger.info("Premium TTS service blueprint registered successfully")
    except ImportError:
        app.logger.warning("Premium TTS service module not available")
    
    # Register enhanced natural-sounding TTS service
    try:
        from enhanced_tts_service import enhanced_tts_bp
        app.register_blueprint(enhanced_tts_bp)
        app.logger.info("Enhanced TTS service blueprint registered successfully")
    except ImportError:
        app.logger.warning("Enhanced TTS service module not available")
    
    # Register OpenAI neural voices TTS service
    try:
        from openai_tts_service import openai_tts_bp
        app.register_blueprint(openai_tts_bp)
        app.logger.info("OpenAI TTS service blueprint registered successfully")
    except ImportError:
        app.logger.warning("OpenAI TTS service module not available")
    
    # Register the stable login blueprint with improved CSRF handling
    try:
        from stable_login import stable_login_bp
        app.register_blueprint(stable_login_bp)
        # Apply CSRF exemption properly
        csrf.exempt(stable_login_bp)
        app.logger.info("Stable login blueprint registered with CSRF exemption for authentication reliability")
    except ImportError:
        app.logger.warning("Stable login blueprint not available")
    
    # Register the stable login as the primary login option
    # This makes all other login paths redirect to stable-login
    try:
        from redirect_to_stable import register_login_redirects
        register_login_redirects(app)
        app.logger.info("All login paths now redirect to stable login")
    except ImportError as e:
        app.logger.warning(f"Login redirect module not available: {str(e)}")
    
    # Keep emergency login options (but they'll redirect to stable login)
    try:
        # FINAL HARDCODED LOGIN: Completely hardcoded test user login
        try:
            from emergency_hardcoded_login import register_hardcoded_login
            register_hardcoded_login(app)
            app.logger.info("Hardcoded test user login registered - use /test-login")
        except ImportError as e:
            app.logger.warning(f"Hardcoded test login not available: {str(e)}")
        
        # ULTRA-EMERGENCY LOGIN: This completely bypasses CSRF and template rendering
        try:
            from emergency_direct_render import register_emergency_render_routes
            register_emergency_render_routes(app)
            app.logger.info("Ultra-emergency Render login system registered and CSRF disabled")
        except ImportError as e:
            app.logger.warning(f"Ultra-emergency login not available: {str(e)}")
            
        # Try our optimized Render login system
        try:
            from render_init import register_render_routes
            # Initialize the Render routes with CSRF exemption
            register_render_routes(app)
            app.logger.info("Render-specific optimized login routes registered successfully")
            
            # Also register the direct login solution for emergency access
            try:
                from direct_login_fix import register_direct_login
                register_direct_login(app)
                app.logger.info("Emergency direct login system registered successfully")
            except ImportError as e:
                app.logger.warning(f"Direct login solution not available: {str(e)}")
                
        except ImportError as e:
            app.logger.warning(f"New Render login routes not available, falling back to legacy: {str(e)}")
            
            # Fall back to legacy render login if needed
            import render_login_fix
            app.register_blueprint(render_login_fix.render_login_bp)
            
            # For Render.com, exempt CSRF to avoid cross-environment issues
            csrf.exempt(render_login_fix.render_login_bp)
            app.logger.info("Legacy Render login blueprint registered with CSRF exemption")
    except ImportError as e:
        app.logger.warning(f"All Render login solutions unavailable: {str(e)}")
    
    # Register the onboarding blueprint
    try:
        from onboarding_routes import onboarding_bp
        app.register_blueprint(onboarding_bp, url_prefix='/onboarding')
        app.logger.info("Onboarding blueprint registered successfully")
    except ImportError:
        app.logger.warning("Onboarding module not available")
        
    # Register the emergency admin blueprint
    if has_emergency_admin:
        app.register_blueprint(emergency_admin_bp)
        csrf.exempt(emergency_admin_bp)
        app.logger.info("Emergency admin blueprint registered with CSRF exemption")
        
    # Register the standalone admin blueprint
    if has_standalone_admin:
        app.register_blueprint(standalone_admin_bp)
        csrf.exempt(standalone_admin_bp)
        app.logger.info("Standalone admin blueprint registered with CSRF exemption")
    
    # Explicitly exempt specific routes from CSRF protection only if they exist
    # This prevents errors when certain blueprints aren't loaded
    try:
        if 'direct_tts_bp' in locals():
            csrf.exempt(direct_tts_bp)
            app.logger.info("CSRF exemption applied to direct_tts_bp")
    except:
        pass
        
    try:
        if 'simple_direct_tts_bp' in locals():
            csrf.exempt(simple_direct_tts_bp)
            app.logger.info("CSRF exemption applied to simple_direct_tts_bp")
    except:
        pass
        
    try:
        if 'premium_tts_bp' in locals():
            csrf.exempt(premium_tts_bp)
            app.logger.info("CSRF exemption applied to premium_tts_bp")
    except:
        pass
        
    try:
        if 'enhanced_tts_bp' in locals():
            csrf.exempt(enhanced_tts_bp)
            app.logger.info("CSRF exemption applied to enhanced_tts_bp")
    except:
        pass
        
    try:
        if 'openai_tts_bp' in locals():
            csrf.exempt(openai_tts_bp)
            app.logger.info("CSRF exemption applied to openai_tts_bp")
    except:
        pass
        
    # Register the email template preview blueprint
    try:
        from preview_email import preview_email_bp
        app.register_blueprint(preview_email_bp)
        app.logger.info("Email preview blueprint registered successfully")
    except ImportError:
        app.logger.warning("Email preview module not available")
    
    # Register emergency dashboard blueprint
    try:
        from emergency_dashboard import emergency_dashboard_bp
        app.register_blueprint(emergency_dashboard_bp)
        app.logger.info("Emergency dashboard blueprint registered successfully")
    except ImportError:
        app.logger.warning("Emergency dashboard module not available")
    
    # Register password reset blueprint
    try:
        from pwd_reset import pwd_reset_bp
        app.register_blueprint(pwd_reset_bp)
        app.logger.info("Password reset blueprint registered successfully")
    except ImportError:
        app.logger.warning("Password reset module not available")
    
    # Register static pages blueprint
    try:
        from static_pages import static_pages_bp
        app.register_blueprint(static_pages_bp)
        app.logger.info("Static pages blueprint registered successfully")
    except ImportError:
        app.logger.warning("Static pages module not available")
    
    # Add favicon route
    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon from static directory"""
        from flask import send_from_directory
        return send_from_directory('static', 'favicon.ico', mimetype='image/x-icon')
    
    # Note: Removed problematic CSRF exemptions that caused 'str' object is not callable errors
    # API endpoints will use proper CSRF tokens in requests instead
    
    # Register push notification routes
    try:
        from push_notification_routes import init_app as init_push_notifications
        init_push_notifications(app)
        app.logger.info("Push notification routes registered successfully")
    except ImportError:
        app.logger.warning("Push notification routes not available")
    
    # Register journal reminder routes
    try:
        from journal_reminder_routes import journal_reminder_bp
        app.register_blueprint(journal_reminder_bp)
        app.logger.info("Journal reminder routes registered successfully")
    except ImportError:
        app.logger.warning("Journal reminder routes not available")
    
    # Register emergency login blueprint with CSRF exemption
    try:
        from emergency_direct_login import emergency_bp
        app.register_blueprint(emergency_bp)
        # Explicitly exempt the emergency blueprint from CSRF protection
        # This is needed to ensure we can log in even if CSRF validation fails
        csrf.exempt(emergency_bp)
        app.logger.info("Emergency login blueprint registered with CSRF exemption")
    except ImportError:
        app.logger.warning("Emergency login blueprint not available")
    
    # Register emergency registration system
    try:
        from emergency_registration_fix import register_emergency_routes
        register_emergency_routes(app)
        app.logger.info("Emergency registration system registered successfully")
    except ImportError:
        app.logger.warning("Emergency registration module not available")
    
    # Register standalone registration system (bypasses SQLAlchemy issues)
    try:
        from standalone_registration import register_standalone_routes
        register_standalone_routes(app)
        app.logger.info("Standalone registration system registered successfully")
    except ImportError:
        app.logger.warning("Standalone registration module not available")
    
    # Register production registration fix (direct database access)
    try:
        from production_registration_fix import register_production_fix
        register_production_fix(app)
        app.logger.info("Production registration fix registered successfully")
    except ImportError:
        app.logger.warning("Production registration fix module not available")
    
    # Register production authentication fix with CSRF exemption
    try:
        from production_auth_fix import production_auth_bp
        csrf.exempt(production_auth_bp)
        app.register_blueprint(production_auth_bp)
        app.logger.info("Production authentication fix registered successfully")
    except ImportError:
        app.logger.warning("Production auth fix module not available")
    
    # Register direct authentication system (bypasses CSRF completely)
    try:
        from direct_auth import register_direct_auth
        register_direct_auth(app)
        app.logger.info("Direct authentication system registered successfully")
    except ImportError:
        app.logger.warning("Direct auth module not available")
    
    # Register complete authentication fix (final solution)
    try:
        from complete_auth_fix import register_complete_auth
        register_complete_auth(app)
        app.logger.info("Complete authentication system registered successfully")
    except ImportError:
        app.logger.warning("Complete auth fix module not available")

# ============================================================================
# DEMOGRAPHICS COLLECTION FUNCTIONALITY
# ============================================================================

@app.route('/demographics', methods=['GET', 'POST'])
@original_login_required
def demographics():
    """Collect user demographics after registration"""
    from flask_wtf import FlaskForm
    from wtforms import SelectField, StringField, SelectMultipleField, SubmitField
    from wtforms.validators import DataRequired
    from wtforms.widgets import CheckboxInput, ListWidget
    
    class MultiCheckboxField(SelectMultipleField):
        widget = ListWidget(prefix_label=False)
        option_widget = CheckboxInput()
    
    class DemographicsForm(FlaskForm):
        age_range = SelectField('Age Range', choices=[
            ('', 'Select age range'),
            ('18-25', '18-25'),
            ('26-35', '26-35'),
            ('36-45', '36-45'),
            ('46-55', '46-55'),
            ('56-65', '56-65'),
            ('65+', '65+')
        ], validators=[DataRequired()])
        
        gender = SelectField('Gender', choices=[
            ('', 'Select gender'),
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Non-binary', 'Non-binary'),
            ('Prefer not to say', 'Prefer not to say')
        ], validators=[DataRequired()])
        
        location = StringField('Location (City/State)', validators=[DataRequired()])
        
        mental_health_concerns = MultiCheckboxField('Primary Mental Health Concerns', choices=[
            ('Anxiety', 'Anxiety'),
            ('Depression', 'Depression'),
            ('Stress', 'Stress'),
            ('Sleep issues', 'Sleep issues'),
            ('Relationship issues', 'Relationship issues'),
            ('Work stress', 'Work stress'),
            ('Other', 'Other')
        ])
        
        submit = SubmitField('Complete Profile')
    
    # Skip if already completed
    if current_user.demographics_collected:
        flash('Demographics already collected.', 'info')
        return redirect('/dashboard')
    
    form = DemographicsForm()
    
    if form.validate_on_submit():
        # Save demographics
        current_user.age_range = form.age_range.data
        current_user.gender = form.gender.data
        current_user.location = form.location.data
        current_user.mental_health_concerns = ','.join(form.mental_health_concerns.data) if form.mental_health_concerns.data else ''
        current_user.demographics_collected = True
        
        try:
            db.session.commit()
            flash('Thank you for completing your profile! This helps us personalize your experience.', 'success')
            return redirect('/dashboard')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving demographics: {str(e)}")
            flash('There was an error saving your information. Please try again.', 'error')
    
    return render_template('demographics.html', form=form)

# Add demographics check to be used by existing routes
def check_demographics_required():
    """Check if current user needs to complete demographics"""
    if current_user.is_authenticated and not current_user.demographics_collected:
        return True
    return False

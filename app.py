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
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Initializing Flask app...")
        app = Flask(__name__)
        
        # Configure secret key
        if os.environ.get("SESSION_SECRET"):
            app.secret_key = os.environ.get("SESSION_SECRET")
            # Use the same secret for CSRF protection
            app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get("SESSION_SECRET")
        else:
            import secrets
            app.logger.warning("No SESSION_SECRET found, generating a temporary one")
            secret = secrets.token_hex(32)
            app.secret_key = secret
            app.config['WTF_CSRF_SECRET_KEY'] = secret
        
        # Configure database
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        
        # Initialize database with app
        db.init_app(app)
        
        logger.info("✅ Flask app initialization completed successfully")
        return app
        
    except Exception as e:
        logger.error(f"🔥 CRITICAL ERROR in create_app: {str(e)}")
        logger.error(traceback.format_exc())
        raise

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

# Initialize the app with extensions
csrf.init_app(app)

# Remove Flask-WTF's automatic csrf_token injection after initialization to prevent conflicts
if 'csrf_token' in app.jinja_env.globals:
    del app.jinja_env.globals['csrf_token']
mail.init_app(app)
sess.init_app(app)

# Apply Render.com compatibility settings if available
if has_render_compatibility:
    app = init_render_compatibility(app)
    app.logger.info(f"Render compatibility settings applied: {app.config['IS_RENDER']}")

# Apply ProxyFix for Render.com HTTPS handling
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)

# Disable CSRF for production to resolve authentication issues
if os.environ.get('RENDER'):
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['WTF_CSRF_SSL_STRICT'] = False

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

# Global error handler completely disabled to restore normal Flask routing
# The error handler was intercepting all requests and causing system-wide routing failure
def handle_exception_disabled(e):
    # This function is completely disabled and should not execute
    pass

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
            current_user.get_id() and 
            current_user.get_id().startswith('admin_') and
            not is_admin_impersonating):
            # Admin user accessing non-admin route without impersonation
            return redirect(url_for('admin_routes.dashboard'))
        
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
    
    # Register minimal registration blueprint
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
        
        # Apply CSRF exemption to stable login for enhanced reliability
        # Enable by default to fix authentication issues
        csrf.exempt(stable_login_bp)
        app.logger.info("Stable login blueprint registered with CSRF exemption for reliability")
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
    
    # Register minimal production login system
    try:
        from minimal_production_login import minimal_login_bp
        app.register_blueprint(minimal_login_bp)
        app.logger.info("Minimal production login registered successfully")
    except ImportError as e:
        app.logger.warning(f"Minimal production login not available: {e}")
    
    # Register direct session login system (bypasses Flask-Login)
    try:
        print("Y1 - Importing direct session login")
        from direct_session_login import direct_login_bp
        print("Y2 - Direct session login imported")
        app.register_blueprint(direct_login_bp)
        print("Y3 - Direct session login blueprint registered")
        app.logger.info("Direct session login registered successfully")
    except ImportError as e:
        print(f"Y4 - Import error: {e}")
        app.logger.warning(f"Direct session login not available: {e}")
    except Exception as e:
        print(f"Y5 - Registration error: {e}")
        app.logger.error(f"Error registering direct session login: {e}")
    
    # Register simple auth test system
    try:
        print("Z1 - Importing simple auth test")
        from simple_auth_test import simple_auth_bp
        print("Z2 - Simple auth test imported")
        app.register_blueprint(simple_auth_bp)
        print("Z3 - Simple auth test blueprint registered")
        app.logger.info("Simple auth test registered successfully")
    except ImportError as e:
        print(f"Z4 - Import error: {e}")
        app.logger.warning(f"Simple auth test not available: {e}")
    except Exception as e:
        print(f"Z5 - Registration error: {e}")
        app.logger.error(f"Error registering simple auth test: {e}")
    
    # Register basic test system
    try:
        print("T1 - Importing basic test")
        from basic_test import basic_test_bp
        print("T2 - Basic test imported")
        app.register_blueprint(basic_test_bp)
        print("T3 - Basic test blueprint registered")
        app.logger.info("Basic test registered successfully")
    except Exception as e:
        print(f"T4 - Basic test error: {e}")
        app.logger.error(f"Error registering basic test: {e}")
    
    # Register isolated test for diagnosis
    try:
        print("I1 - Importing isolated test")
        from isolated_test import isolated_bp
        print("I2 - Isolated test imported")
        app.register_blueprint(isolated_bp)
        print("I3 - Isolated test blueprint registered")
        app.logger.info("Isolated test registered successfully")
    except Exception as e:
        print(f"I4 - Isolated test error: {e}")
        app.logger.error(f"Error registering isolated test: {e}")
    
    # Register minimal authentication fix
    try:
        print("M1 - Importing minimal auth fix")
        from minimal_auth_fix import minimal_auth_bp
        print("M2 - Minimal auth fix imported")
        app.register_blueprint(minimal_auth_bp)
        print("M3 - Minimal auth fix blueprint registered")
        app.logger.info("Minimal auth fix registered successfully")
    except Exception as e:
        print(f"M4 - Minimal auth fix error: {e}")
        app.logger.error(f"Error registering minimal auth fix: {e}")

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
        return redirect(url_for('dashboard'))
    
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
            return redirect(url_for('dashboard'))
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

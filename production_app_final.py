"""
Final production application for Dear Teddy - comprehensive and stable
"""
import os
import logging
from flask import Flask, redirect, render_template, request, flash, url_for, render_template_string
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_production_app():
    """Create production-ready Dear Teddy application"""
    app = Flask(__name__)
    
    # Essential configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "production-fallback-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(user_id)
    
    # Create database tables
    with app.app_context():
        try:
            import models
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    # Import and register full routes if available
    try:
        import routes
        import admin_routes
        import journal_routes
        import account_routes
        logger.info("Full Dear Teddy routes loaded successfully")
        return app
    except Exception as e:
        logger.warning(f"Full routes not available, using basic routes: {e}")
    
    # Basic routes for production stability
    @app.route('/')
    def index():
        """Root route with proper Dear Teddy dashboard"""
        if current_user.is_authenticated:
            try:
                return render_template('dashboard.html', user=current_user)
            except:
                # Fallback dashboard if template missing
                return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Dear Teddy Dashboard</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        .navbar { background-color: #1D4D4F !important; }
                        .btn-primary { background-color: #A05C2C; border-color: #A05C2C; }
                        .btn-primary:hover { background-color: #8B4F26; border-color: #8B4F26; }
                    </style>
                </head>
                <body class="bg-light">
                    <nav class="navbar navbar-dark">
                        <div class="container">
                            <span class="navbar-brand">🧸 Dear Teddy</span>
                            <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                        </div>
                    </nav>
                    <div class="container mt-4">
                        <div class="row">
                            <div class="col-12">
                                <h2>Welcome back, {{ user.email }}!</h2>
                                <p class="lead">Your mental wellness companion is here for you.</p>
                            </div>
                        </div>
                        <div class="row mt-4">
                            <div class="col-md-6 mb-3">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <h5 class="card-title">📝 Journal Entry</h5>
                                        <p class="card-text">Express your thoughts and feelings in a safe space.</p>
                                        <a href="/journal" class="btn btn-primary">Start Writing</a>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <h5 class="card-title">📊 Mood Tracking</h5>
                                        <p class="card-text">Track your emotional wellness journey.</p>
                                        <a href="/mood" class="btn btn-success">Log Mood</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """, user=current_user)
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login route with form handling"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if email and password:
                from models import User
                user = User.query.filter_by(email=email).first()
                if user and user.password_hash and check_password_hash(user.password_hash, password):
                    login_user(user, remember=True)
                    return redirect(url_for('index'))
            
            flash('Invalid email or password.', 'error')
        
        try:
            return render_template('login.html')
        except:
            # Fallback login page
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login - Dear Teddy</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    .card-header { background-color: #1D4D4F !important; color: white; }
                    .btn-login { background-color: #A05C2C; border-color: #A05C2C; color: white; }
                    .btn-login:hover { background-color: #8B4F26; border-color: #8B4F26; color: white; }
                </style>
            </head>
            <body class="bg-light">
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-4">
                            <div class="card shadow">
                                <div class="card-header text-center">
                                    <h4>🧸 Dear Teddy</h4>
                                    <p class="mb-0">Your Mental Wellness Companion</p>
                                </div>
                                <div class="card-body">
                                    {% with messages = get_flashed_messages() %}
                                        {% if messages %}
                                            {% for message in messages %}
                                                <div class="alert alert-danger">{{ message }}</div>
                                            {% endfor %}
                                        {% endif %}
                                    {% endwith %}
                                    <form method="POST">
                                        <div class="mb-3">
                                            <label class="form-label">Email Address</label>
                                            <input type="email" name="email" class="form-control" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Password</label>
                                            <input type="password" name="password" class="form-control" required>
                                        </div>
                                        <button type="submit" class="btn btn-login w-100">Sign In</button>
                                    </form>
                                    <div class="text-center mt-3">
                                        <a href="/register" class="text-decoration-none">Create New Account</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Registration route"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if email and password:
                from models import User
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already registered. Please log in.', 'error')
                else:
                    user = User(email=email, password_hash=generate_password_hash(password))
                    db.session.add(user)
                    db.session.commit()
                    login_user(user, remember=True)
                    return redirect(url_for('index'))
        
        try:
            return render_template('register.html')
        except:
            # Fallback registration page
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Register - Dear Teddy</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    .card-header { background-color: #1D4D4F !important; color: white; }
                    .btn-register { background-color: #A05C2C; border-color: #A05C2C; color: white; }
                    .btn-register:hover { background-color: #8B4F26; border-color: #8B4F26; color: white; }
                </style>
            </head>
            <body class="bg-light">
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-4">
                            <div class="card shadow">
                                <div class="card-header text-center">
                                    <h4>🧸 Join Dear Teddy</h4>
                                    <p class="mb-0">Start Your Wellness Journey</p>
                                </div>
                                <div class="card-body">
                                    {% with messages = get_flashed_messages() %}
                                        {% if messages %}
                                            {% for message in messages %}
                                                <div class="alert alert-danger">{{ message }}</div>
                                            {% endfor %}
                                        {% endif %}
                                    {% endwith %}
                                    <form method="POST">
                                        <div class="mb-3">
                                            <label class="form-label">Email Address</label>
                                            <input type="email" name="email" class="form-control" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Password</label>
                                            <input type="password" name="password" class="form-control" required>
                                        </div>
                                        <button type="submit" class="btn btn-register w-100">Create Account</button>
                                    </form>
                                    <div class="text-center mt-3">
                                        <a href="/login" class="text-decoration-none">Already have an account?</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """)
    
    @app.route('/logout')
    def logout():
        """Logout route"""
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/journal')
    @login_required
    def journal():
        """Basic journal route"""
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Journal - Dear Teddy</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <nav class="navbar navbar-dark" style="background-color: #1D4D4F;">
                <div class="container">
                    <a href="/" class="navbar-brand">🧸 Dear Teddy</a>
                    <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                </div>
            </nav>
            <div class="container mt-4">
                <h2>Journal Entry</h2>
                <p>Express your thoughts and feelings in this safe space.</p>
                <p class="text-muted">Full journaling features will be available soon.</p>
                <a href="/" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </body>
        </html>
        """)
    
    @app.route('/mood')
    @login_required
    def mood():
        """Basic mood tracking route"""
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mood - Dear Teddy</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <nav class="navbar navbar-dark" style="background-color: #1D4D4F;">
                <div class="container">
                    <a href="/" class="navbar-brand">🧸 Dear Teddy</a>
                    <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                </div>
            </nav>
            <div class="container mt-4">
                <h2>Mood Tracking</h2>
                <p>Track your emotional wellness journey.</p>
                <p class="text-muted">Full mood tracking features will be available soon.</p>
                <a href="/" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </body>
        </html>
        """)
    
    return app

# Create the app instance
app = create_production_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Dear Teddy production server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
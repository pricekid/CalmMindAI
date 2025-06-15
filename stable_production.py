"""
Stable production application for Dear Teddy
"""
import os
import logging
from flask import Flask, redirect, request, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET", "stable-production-key")
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
        logger.error(f"Database error: {e}")

# Try to import full routes, fallback to basic ones
try:
    import routes
    import admin_routes
    import journal_routes
    import account_routes
    logger.info("Full Dear Teddy routes loaded")
except Exception as e:
    logger.warning(f"Using basic routes: {e}")
    
    @app.route('/')
    def index():
        """Landing page that shows marketing page for new visitors, dashboard for logged in users"""
        if current_user.is_authenticated:
            # Redirect authenticated users to dashboard
            return redirect('/dashboard')
        
        # Show marketing landing page for new visitors
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dear Teddy - Your Mental Wellness Companion</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                .hero-section { background: linear-gradient(135deg, #1D4D4F 0%, #A05C2C 100%); color: white; padding: 100px 0; }
                .btn-custom { background-color: #A05C2C; border-color: #A05C2C; color: white; }
                .btn-custom:hover { background-color: #8B4F26; border-color: #8B4F26; color: white; }
                .feature-icon { font-size: 3rem; color: #A05C2C; }
            </style>
        </head>
        <body>
            <!-- Navigation -->
            <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
                <div class="container">
                    <a class="navbar-brand fw-bold" href="/" style="color: #A05C2C;">
                        🧸 Dear Teddy
                    </a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="/login">Sign In</a>
                        <a class="btn btn-custom ms-2" href="/register">Get Started</a>
                    </div>
                </div>
            </nav>

            <!-- Hero Section -->
            <section class="hero-section text-center">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-lg-8">
                            <h1 class="display-4 fw-bold mb-4">Your Mental Wellness Companion</h1>
                            <p class="lead mb-5">A safe space to express your thoughts, track your mood, and receive personalized insights powered by AI.</p>
                            <a href="/register" class="btn btn-light btn-lg me-3">Start Your Journey</a>
                            <a href="/login" class="btn btn-outline-light btn-lg">Sign In</a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Features Section -->
            <section class="py-5">
                <div class="container">
                    <div class="row text-center mb-5">
                        <div class="col-12">
                            <h2 class="display-5 fw-bold" style="color: #1D4D4F;">How Dear Teddy Helps</h2>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-4 mb-4">
                            <div class="text-center">
                                <div class="feature-icon">📝</div>
                                <h4 class="mt-3">AI-Powered Journaling</h4>
                                <p>Express your thoughts and receive personalized insights and coping strategies.</p>
                            </div>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="text-center">
                                <div class="feature-icon">📊</div>
                                <h4 class="mt-3">Mood Tracking</h4>
                                <p>Monitor your emotional wellness journey with visual insights and patterns.</p>
                            </div>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="text-center">
                                <div class="feature-icon">🧠</div>
                                <h4 class="mt-3">CBT Techniques</h4>
                                <p>Learn evidence-based cognitive behavioral therapy techniques for better mental health.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- CTA Section -->
            <section class="py-5 bg-light">
                <div class="container text-center">
                    <div class="row justify-content-center">
                        <div class="col-lg-6">
                            <h3 class="mb-4" style="color: #1D4D4F;">Ready to Start Your Wellness Journey?</h3>
                            <a href="/register" class="btn btn-custom btn-lg">Get Started Free</a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Footer -->
            <footer class="py-4" style="background-color: #1D4D4F; color: white;">
                <div class="container text-center">
                    <p class="mb-0">&copy; 2025 Dear Teddy. Your mental wellness companion.</p>
                </div>
            </footer>
        </body>
        </html>
        '''

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """User dashboard after login"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Dear Teddy</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                .navbar {{ background-color: #1D4D4F !important; }}
                .card {{ border: none; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .btn-primary {{ background-color: #A05C2C; border-color: #A05C2C; }}
                .btn-primary:hover {{ background-color: #8B4F26; border-color: #8B4F26; }}
            </style>
        </head>
        <body class="bg-light">
            <nav class="navbar navbar-dark">
                <div class="container">
                    <span class="navbar-brand">🧸 Dear Teddy</span>
                    <div>
                        <span class="text-light me-3">Welcome, {current_user.email}</span>
                        <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                    </div>
                </div>
            </nav>
            <div class="container mt-4">
                <div class="row">
                    <div class="col-12 mb-4">
                        <h2>Your Mental Wellness Dashboard</h2>
                        <p class="text-muted">Take care of your mental health with our supportive tools.</p>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">📝 Journal Entry</h5>
                                <p class="card-text">Express your thoughts and feelings in a safe, private space.</p>
                                <a href="/new-journal" class="btn btn-primary">Start Writing</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">📊 Mood Tracking</h5>
                                <p class="card-text">Track your emotional wellness and see patterns over time.</p>
                                <a href="/mood-log" class="btn btn-success">Log Mood</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">📚 Your Journal History</h5>
                                <p class="card-text">Review your previous entries and insights.</p>
                                <a href="/journal-history" class="btn btn-secondary">View History</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">⚙️ Account Settings</h5>
                                <p class="card-text">Manage your profile and preferences.</p>
                                <a href="/account" class="btn btn-outline-primary">Settings</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if email and password:
                from models import User
                user = User.query.filter_by(email=email).first()
                if user and user.password_hash and check_password_hash(user.password_hash, password):
                    login_user(user, remember=True)
                    return redirect('/dashboard')
            
            flash('Invalid email or password.', 'error')
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sign In - Dear Teddy</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }
                .login-card { border-radius: 20px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.1); background: white; }
                .teddy-icon { width: 60px; height: 60px; background: #A05C2C; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; margin: 0 auto 20px; }
                .btn-login { background: linear-gradient(135deg, #A05C2C 0%, #B86A3A 100%); border: none; color: white; padding: 12px; border-radius: 10px; font-weight: 600; }
                .btn-login:hover { background: linear-gradient(135deg, #8B4F26 0%, #A05C2C 100%); color: white; }
                .form-control { border-radius: 10px; border: 2px solid #e9ecef; padding: 12px 15px; }
                .form-control:focus { border-color: #A05C2C; box-shadow: 0 0 0 0.2rem rgba(160, 92, 44, 0.25); }
                .form-label { color: #A05C2C; font-weight: 600; margin-bottom: 8px; }
                .remember-check { accent-color: #A05C2C; }
                .secure-badge { background: #e8f5e8; color: #2d5a2d; padding: 8px 15px; border-radius: 20px; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="row justify-content-center align-items-center min-vh-100">
                    <div class="col-md-5 col-lg-4">
                        <div class="login-card p-4">
                            <div class="text-center mb-4">
                                <div class="teddy-icon">🐻</div>
                                <h3 style="color: #A05C2C; font-weight: 700;">Dear Teddy</h3>
                                <h4 style="color: #1D4D4F; font-weight: 600; margin-top: 20px;">Welcome Back</h4>
                            </div>
                            
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">Email</label>
                                    <input type="email" name="email" class="form-control" value="test@example.com" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Password</label>
                                    <input type="password" name="password" class="form-control" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input remember-check" id="remember" name="remember">
                                    <label class="form-check-label" for="remember" style="color: #6c757d;">Remember Me</label>
                                </div>
                                <button type="submit" class="btn btn-login w-100 mb-3">LOGIN</button>
                            </form>
                            
                            <div class="text-center mb-3">
                                <a href="/forgot-password" style="color: #6c757d; text-decoration: none;">Forgot your password?</a>
                            </div>
                            
                            <div class="text-center mb-3">
                                <span class="secure-badge">🔒 Secure Connection</span>
                            </div>
                            
                            <div class="text-center">
                                <p style="color: #6c757d; margin: 0;">New to Dear Teddy?</p>
                                <a href="/register" style="color: #A05C2C; text-decoration: none; font-weight: 600;">Create Account</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect('/dashboard')
            
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation
            if not email or not password:
                flash('Please fill in all fields.', 'error')
            elif password != confirm_password:
                flash('Passwords do not match.', 'error')
            elif len(password) < 6:
                flash('Password must be at least 6 characters.', 'error')
            else:
                from models import User
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already registered. Please sign in.', 'error')
                else:
                    try:
                        user = User(email=email, password_hash=generate_password_hash(password))
                        db.session.add(user)
                        db.session.commit()
                        login_user(user, remember=True)
                        return redirect('/dashboard')
                    except Exception as e:
                        logger.error(f"Registration error: {e}")
                        flash('Registration failed. Please try again.', 'error')
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Join Dear Teddy</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }
                .register-card { border-radius: 20px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.1); background: white; }
                .teddy-icon { width: 60px; height: 60px; background: #A05C2C; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; margin: 0 auto 20px; }
                .btn-register { background: linear-gradient(135deg, #A05C2C 0%, #B86A3A 100%); border: none; color: white; padding: 12px; border-radius: 10px; font-weight: 600; }
                .btn-register:hover { background: linear-gradient(135deg, #8B4F26 0%, #A05C2C 100%); color: white; }
                .form-control { border-radius: 10px; border: 2px solid #e9ecef; padding: 12px 15px; }
                .form-control:focus { border-color: #A05C2C; box-shadow: 0 0 0 0.2rem rgba(160, 92, 44, 0.25); }
                .form-label { color: #A05C2C; font-weight: 600; margin-bottom: 8px; }
                .privacy-text { font-size: 13px; color: #6c757d; line-height: 1.4; }
                .feature-item { display: flex; align-items: center; margin-bottom: 10px; color: #6c757d; font-size: 14px; }
                .feature-icon { color: #A05C2C; margin-right: 8px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="row justify-content-center align-items-center min-vh-100">
                    <div class="col-md-6 col-lg-5">
                        <div class="register-card p-4">
                            <div class="text-center mb-4">
                                <div class="teddy-icon">🐻</div>
                                <h3 style="color: #A05C2C; font-weight: 700;">Dear Teddy</h3>
                                <h4 style="color: #1D4D4F; font-weight: 600; margin-top: 20px;">Start Your Wellness Journey</h4>
                                <p style="color: #6c757d; margin-top: 10px;">Join thousands who trust Dear Teddy for mental wellness support</p>
                            </div>
                            
                            <div class="mb-4">
                                <div class="feature-item">
                                    <span class="feature-icon">📝</span>
                                    <span>AI-powered journaling with personalized insights</span>
                                </div>
                                <div class="feature-item">
                                    <span class="feature-icon">📊</span>
                                    <span>Mood tracking and wellness analytics</span>
                                </div>
                                <div class="feature-item">
                                    <span class="feature-icon">🔒</span>
                                    <span>Complete privacy and security</span>
                                </div>
                            </div>
                            
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">Email Address</label>
                                    <input type="email" name="email" class="form-control" placeholder="Enter your email" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Password</label>
                                    <input type="password" name="password" class="form-control" placeholder="Create a secure password" minlength="6" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Confirm Password</label>
                                    <input type="password" name="confirm_password" class="form-control" placeholder="Confirm your password" minlength="6" required>
                                </div>
                                <button type="submit" class="btn btn-register w-100 mb-3">Create My Account</button>
                            </form>
                            
                            <div class="text-center mb-3">
                                <p class="privacy-text">
                                    By creating an account, you agree to our privacy-first approach. 
                                    Your data is encrypted and never shared.
                                </p>
                            </div>
                            
                            <div class="text-center">
                                <p style="color: #6c757d; margin: 0;">Already have an account?</p>
                                <a href="/login" style="color: #A05C2C; text-decoration: none; font-weight: 600;">Sign In</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
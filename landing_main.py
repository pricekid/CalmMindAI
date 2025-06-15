"""
Landing page focused production app for Dear Teddy
"""
import os
import logging
from flask import Flask, redirect, request, flash
from flask_login import LoginManager, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET", "landing-production-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

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

@app.route('/')
def index():
    """Always show marketing landing page"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dear Teddy - Your Mental Wellness Companion</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .hero-section { 
                background: linear-gradient(135deg, #1D4D4F 0%, #A05C2C 100%); 
                color: white; 
                padding: 100px 0; 
                min-height: 80vh;
                display: flex;
                align-items: center;
            }
            .btn-custom { 
                background-color: #A05C2C; 
                border-color: #A05C2C; 
                color: white; 
                padding: 15px 30px;
                font-size: 18px;
                border-radius: 50px;
                font-weight: 600;
            }
            .btn-custom:hover { 
                background-color: #8B4F26; 
                border-color: #8B4F26; 
                color: white; 
            }
            .btn-outline-custom {
                border: 2px solid white;
                color: white;
                padding: 15px 30px;
                font-size: 18px;
                border-radius: 50px;
                font-weight: 600;
                background: transparent;
            }
            .btn-outline-custom:hover {
                background: white;
                color: #1D4D4F;
                border-color: white;
            }
            .feature-icon { 
                font-size: 4rem; 
                color: #A05C2C; 
                margin-bottom: 20px;
            }
            .navbar-brand {
                font-size: 24px;
                font-weight: 700;
            }
            .feature-card {
                border: none;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                padding: 30px;
                height: 100%;
                transition: transform 0.3s;
            }
            .feature-card:hover {
                transform: translateY(-5px);
            }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm fixed-top">
            <div class="container">
                <a class="navbar-brand" href="/" style="color: #A05C2C;">
                    🧸 Dear Teddy
                </a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link me-3" href="/login" style="color: #1D4D4F; font-weight: 500;">Sign In</a>
                    <a class="btn btn-custom" href="/register">Get Started Free</a>
                </div>
            </div>
        </nav>

        <!-- Hero Section -->
        <section class="hero-section">
            <div class="container">
                <div class="row justify-content-center text-center">
                    <div class="col-lg-8">
                        <div style="font-size: 80px; margin-bottom: 30px;">🧸</div>
                        <h1 class="display-3 fw-bold mb-4">Your Mental Wellness Companion</h1>
                        <p class="lead mb-5 fs-4">A safe, private space to express your thoughts, track your mood, and receive personalized AI-powered insights for better mental health.</p>
                        <div class="d-flex justify-content-center gap-4 flex-wrap">
                            <a href="/register" class="btn btn-light btn-lg px-5 py-3" style="border-radius: 50px; font-weight: 600; font-size: 18px;">Start Your Journey</a>
                            <a href="/login" class="btn btn-outline-custom btn-lg px-5 py-3">Sign In</a>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section class="py-5" style="padding: 100px 0;">
            <div class="container">
                <div class="row text-center mb-5">
                    <div class="col-12">
                        <h2 class="display-4 fw-bold mb-4" style="color: #1D4D4F;">How Dear Teddy Helps You</h2>
                        <p class="lead" style="color: #6c757d;">Evidence-based tools for your mental wellness journey</p>
                    </div>
                </div>
                <div class="row g-5">
                    <div class="col-md-4">
                        <div class="feature-card text-center">
                            <div class="feature-icon">📝</div>
                            <h4 class="fw-bold mb-3" style="color: #1D4D4F;">AI-Powered Journaling</h4>
                            <p style="color: #6c757d;">Express your thoughts freely and receive personalized insights, coping strategies, and emotional support powered by advanced AI.</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="feature-card text-center">
                            <div class="feature-icon">📊</div>
                            <h4 class="fw-bold mb-3" style="color: #1D4D4F;">Mood Tracking</h4>
                            <p style="color: #6c757d;">Monitor your emotional wellness with visual insights, track patterns over time, and understand your mental health journey.</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="feature-card text-center">
                            <div class="feature-icon">🧠</div>
                            <h4 class="fw-bold mb-3" style="color: #1D4D4F;">CBT Techniques</h4>
                            <p style="color: #6c757d;">Learn and practice evidence-based cognitive behavioral therapy techniques for better mental health and emotional regulation.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- CTA Section -->
        <section class="py-5" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 100px 0;">
            <div class="container text-center">
                <div class="row justify-content-center">
                    <div class="col-lg-8">
                        <h2 class="display-5 fw-bold mb-4" style="color: #1D4D4F;">Ready to Start Your Wellness Journey?</h2>
                        <p class="lead mb-5" style="color: #6c757d;">Join thousands who trust Dear Teddy for compassionate mental health support. Free to start, always private.</p>
                        <a href="/register" class="btn btn-custom btn-lg px-5 py-3">Create Free Account</a>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="py-5" style="background-color: #1D4D4F; color: white;">
            <div class="container">
                <div class="row">
                    <div class="col-lg-6">
                        <h5 class="fw-bold mb-3">🧸 Dear Teddy</h5>
                        <p>Your trusted companion for mental wellness and emotional support.</p>
                    </div>
                    <div class="col-lg-6 text-lg-end">
                        <div class="d-flex justify-content-lg-end gap-4">
                            <a href="/login" style="color: white; text-decoration: none;">Sign In</a>
                            <a href="/register" style="color: white; text-decoration: none;">Register</a>
                        </div>
                    </div>
                </div>
                <hr style="border-color: rgba(255,255,255,0.2); margin: 40px 0;">
                <div class="text-center">
                    <p class="mb-0">&copy; 2025 Dear Teddy. Your mental wellness companion.</p>
                </div>
            </div>
        </footer>
    </body>
    </html>
    '''

@app.route('/app')
def app_redirect():
    """Direct app access for logged in users"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if not current_user.is_authenticated:
        return redirect('/login')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Dear Teddy</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .navbar {{ background-color: #1D4D4F !important; }}
            .card {{ border: none; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 15px; }}
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
            <h2>Your Mental Wellness Dashboard</h2>
            <p class="text-muted mb-4">Take care of your mental health with our supportive tools.</p>
            <div class="row g-4">
                <div class="col-md-6">
                    <div class="card h-100 p-4">
                        <h5 class="card-title">📝 Journal Entry</h5>
                        <p class="card-text">Express your thoughts and feelings in a safe, private space.</p>
                        <a href="/journal" class="btn btn-primary">Start Writing</a>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card h-100 p-4">
                        <h5 class="card-title">📊 Mood Tracking</h5>
                        <p class="card-text">Track your emotional wellness and see patterns over time.</p>
                        <a href="/mood" class="btn btn-success">Log Mood</a>
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center align-items-center min-vh-100">
                <div class="col-md-5 col-lg-4">
                    <div class="login-card p-4">
                        <div class="text-center mb-4">
                            <div class="teddy-icon">🐻</div>
                            <h3 style="color: #A05C2C;">Dear Teddy</h3>
                            <h4 style="color: #1D4D4F;">Welcome Back</h4>
                        </div>
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label" style="color: #A05C2C;">Email</label>
                                <input type="email" name="email" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label" style="color: #A05C2C;">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-login w-100 mb-3">LOGIN</button>
                        </form>
                        <div class="text-center">
                            <p style="color: #6c757d;">New to Dear Teddy?</p>
                            <a href="/register" style="color: #A05C2C; font-weight: 600;">Create Account</a>
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
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if email and password:
            from models import User
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered.', 'error')
            else:
                user = User(email=email, password_hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                return redirect('/dashboard')
    
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center align-items-center min-vh-100">
                <div class="col-md-5 col-lg-4">
                    <div class="register-card p-4">
                        <div class="text-center mb-4">
                            <div class="teddy-icon">🐻</div>
                            <h3 style="color: #A05C2C;">Dear Teddy</h3>
                            <h4 style="color: #1D4D4F;">Start Your Journey</h4>
                        </div>
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label" style="color: #A05C2C;">Email</label>
                                <input type="email" name="email" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label" style="color: #A05C2C;">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-register w-100 mb-3">Create Account</button>
                        </form>
                        <div class="text-center">
                            <p style="color: #6c757d;">Already have an account?</p>
                            <a href="/login" style="color: #A05C2C; font-weight: 600;">Sign In</a>
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
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
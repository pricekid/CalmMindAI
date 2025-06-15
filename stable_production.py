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
        if current_user.is_authenticated:
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dear Teddy</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="bg-light">
                <nav class="navbar navbar-dark" style="background-color: #1D4D4F;">
                    <div class="container">
                        <span class="navbar-brand">Dear Teddy</span>
                        <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                    </div>
                </nav>
                <div class="container mt-4">
                    <h1>Welcome, {current_user.email}!</h1>
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h5>Journal</h5>
                                    <p>Express your thoughts and feelings.</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h5>Mood Tracking</h5>
                                    <p>Track your emotional wellness.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
        return redirect('/login')

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
                    return redirect('/')
            
            flash('Invalid email or password.', 'error')
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Dear Teddy</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header text-center" style="background-color: #1D4D4F; color: white;">
                                <h4>Dear Teddy Login</h4>
                            </div>
                            <div class="card-body">
                                <form method="POST">
                                    <div class="mb-3">
                                        <label class="form-label">Email</label>
                                        <input type="email" name="email" class="form-control" required>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Password</label>
                                        <input type="password" name="password" class="form-control" required>
                                    </div>
                                    <button type="submit" class="btn w-100" style="background-color: #A05C2C; color: white;">Login</button>
                                </form>
                                <div class="text-center mt-3">
                                    <a href="/register">Create Account</a>
                                </div>
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
                    return redirect('/')
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Register - Dear Teddy</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header text-center" style="background-color: #1D4D4F; color: white;">
                                <h4>Create Account</h4>
                            </div>
                            <div class="card-body">
                                <form method="POST">
                                    <div class="mb-3">
                                        <label class="form-label">Email</label>
                                        <input type="email" name="email" class="form-control" required>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Password</label>
                                        <input type="password" name="password" class="form-control" required>
                                    </div>
                                    <button type="submit" class="btn w-100" style="background-color: #A05C2C; color: white;">Create Account</button>
                                </form>
                                <div class="text-center mt-3">
                                    <a href="/login">Already have an account?</a>
                                </div>
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
"""
Minimal production app for Render deployment.
This ensures the site loads with basic functionality while fixing routing issues.
"""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Production configuration
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'fallback-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Fix HTTPS/HTTP for Render
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Simple User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    
    def __init__(self, **kwargs):
        super().__init__()
        self.id = kwargs.get('id')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Routes
@app.route('/')
def index():
    """Home route"""
    if current_user.is_authenticated:
        try:
            return render_template('simple_dashboard.html', user=current_user)
        except:
            # Fallback if template is missing
            return f'''
            <!DOCTYPE html>
            <html>
            <head><title>Dear Teddy Dashboard</title>
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
                <h1>Welcome to Dear Teddy</h1>
                <p>Your mental wellness companion is loading...</p>
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5>Journal</h5>
                                <p>Express your thoughts and feelings.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            </body>
            </html>
            '''
    try:
        return render_template('login.html')
    except:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if email and password:
                user = User.query.filter_by(email=email).first()
                if user and check_password_hash(user.password_hash, password):
                    login_user(user, remember=True)
                    return redirect(url_for('index'))
            
            flash('Invalid email or password.', 'error')
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Login system temporarily unavailable.', 'error')
    
    try:
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Login template error: {e}")
        # Return inline HTML if template fails
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
    """Registration route"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if email and password:
            existing_user = User.query.filter_by(email=email).first()
            if not existing_user:
                import uuid
                user = User(
                    id=str(uuid.uuid4()),
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                return redirect(url_for('index'))
            else:
                flash('Email already registered.', 'error')
        else:
            flash('Please enter both email and password.', 'error')
    
    return render_template('standalone_register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'app': 'dear-teddy'})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

# Create tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Database error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Routes
@app.route('/')
def index():
    """Home route"""
    if current_user.is_authenticated:
        return render_template('simple_dashboard.html', user=current_user)
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if email and password:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=True)
                return redirect(url_for('index'))
        
        flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

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
    
    return render_template('register.html')

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
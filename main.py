
from app import app, db
import logging
from flask import redirect

# Configure logging
logging.basicConfig(level=logging.INFO)

# Ensure database tables exist
with app.app_context():
    db.create_all()

# Import and register Replit Auth blueprint
from replit_routes import replit_bp
app.register_blueprint(replit_bp, url_prefix='/auth')

# Add a direct route to Replit Auth login
@app.route('/login-with-replit')
def login_with_replit():
    """Redirect to Replit Auth login"""
    return redirect('/auth/login')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

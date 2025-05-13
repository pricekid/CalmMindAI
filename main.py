from app import app, db
import logging
from flask import redirect

# Configure logging
logging.basicConfig(level=logging.INFO)

# Ensure database tables exist
with app.app_context():
    db.create_all()

# No Auth integration is required in main.py
# Authentication is handled in app.py and routes.py

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
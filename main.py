from app import app, db, csrf
import subprocess
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure database tables exist
with app.app_context():
    db.create_all()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import admin_routes but don't register the blueprint again since it's imported in app.py
import admin_routes

# We'll skip registering the emergency blueprint here
# because we're already registering it in app.py
# This prevents the "blueprint already registered" error

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
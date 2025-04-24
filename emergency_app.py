"""
Emergency application with minimal dependencies for recovery.
"""
import os
import logging
from flask import Flask
from emergency_login import emergency_bp
from test_journal_reflection import test_reflection_bp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a minimal app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "emergency_secret_key"

# Register only the emergency blueprints
app.register_blueprint(emergency_bp)
app.register_blueprint(test_reflection_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
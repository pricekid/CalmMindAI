"""
Register the test login blueprint with the main application.
This creates a special diagnostic route to help debug login issues.
"""

from flask import Flask
from test_login import test_login_bp
import logging

logger = logging.getLogger(__name__)

def register_test_login_blueprint(app):
    """Register the test login blueprint with the application."""
    app.register_blueprint(test_login_bp)
    logger.info("Test login diagnostic blueprint registered successfully")
    return app

# Direct import function for app.py
if __name__ == "__main__":
    # This is only used if this script is run directly
    from app import app
    register_test_login_blueprint(app)
    print("Test login blueprint registered successfully. Access at /test-login")
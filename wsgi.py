"""
WSGI entry point for the application.
This file is used by Gunicorn to start the application.
"""

import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wsgi")

# Set environment variables for production
if not os.environ.get('ENVIRONMENT'):
    os.environ['ENVIRONMENT'] = 'production'
    logger.info("Set ENVIRONMENT=production environment variable")

if not os.environ.get('RENDER'):
    os.environ['RENDER'] = 'true'
    logger.info("Set RENDER=true environment variable")

# Import the application
try:
    from main import app as application
    logger.info("Application imported successfully")
except Exception as e:
    logger.error(f"Error importing application: {e}")
    raise

# This variable is used by Gunicorn
app = application

if __name__ == "__main__":
    logger.info("Starting application directly from wsgi.py")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
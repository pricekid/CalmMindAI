"""
Production-only main file for Render deployment.
This ensures the minimal app is used for production without environment detection issues.
"""

import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

try:
    logger.info("Starting Dear Teddy production application")
    from production_full_app import app
    logger.info("Full Dear Teddy application imported successfully")
    
except Exception as e:
    logger.error(f"Critical error during app creation: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting production server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        logger.error(f"Production server startup error: {e}")
        raise
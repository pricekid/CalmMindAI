import os
import logging
import traceback
import sys

# Bulletproof logging setup
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

file_handler = logging.FileHandler('debug.log')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

try:
    logger.info("🚀 Starting Dear Teddy application...")
    
    # Use simplified app for Render deployment, full app for development
    if os.environ.get('RENDER'):
        logger.info("🔧 Using Render production configuration")
        from render_app import app
    else:
        logger.info("🔧 Using development configuration")
        from app import app
    
    logger.info("✅ Application created successfully")
    
except Exception as e:
    logger.error("🔥 CRITICAL ERROR during app creation:")
    logger.error(traceback.format_exc())
    raise

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"🌐 Starting server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.error("🔥 UNCAUGHT EXCEPTION in main:")
        logger.error(traceback.format_exc())
        raise
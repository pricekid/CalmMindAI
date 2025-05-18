"""
Render startup script to troubleshoot and fix common deployment issues.
This file is intended to be run before the main application starts on Render.
"""

import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("render_startup")

def check_environment():
    """Verify that all required environment variables are set"""
    logger.info("Checking environment variables...")
    
    # Critical variables that must be present
    required_vars = [
        "DATABASE_URL",
        "SESSION_SECRET",
        "OPENAI_API_KEY"
    ]
    
    # Variables that are helpful but not strictly required
    optional_vars = [
        "SENDGRID_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER"
    ]
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        logger.error(f"Missing critical environment variables: {', '.join(missing)}")
        logger.error("These must be set in the Render dashboard for the application to work.")
        return False
    
    # Check optional variables
    missing_optional = []
    for var in optional_vars:
        if not os.environ.get(var):
            missing_optional.append(var)
    
    if missing_optional:
        logger.warning(f"Missing optional variables: {', '.join(missing_optional)}")
        logger.warning("Some features may not work correctly without these variables.")
    
    logger.info("Environment check complete. All critical variables are set.")
    return True

def check_database():
    """Test database connectivity"""
    logger.info("Testing database connection...")
    try:
        # Don't import db until after we've checked environment variables
        from app import db
        
        # Simple connection test
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("Database connection successful.")
                return True
            else:
                logger.error("Database query failed to return expected result.")
                return False
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def apply_patches():
    """Apply any necessary patches for production environment"""
    logger.info("Applying production patches...")
    
    # Set RENDER environment variable if it's not already set
    if not os.environ.get('RENDER'):
        os.environ['RENDER'] = 'true'
        logger.info("Set RENDER=true environment variable")
    
    # Set production environment
    if not os.environ.get('ENVIRONMENT'):
        os.environ['ENVIRONMENT'] = 'production'
        logger.info("Set ENVIRONMENT=production environment variable")
    
    return True

def main():
    """Main startup function"""
    logger.info("=== Render Startup Script ===")
    
    # Run checks
    env_ok = check_environment()
    if not env_ok:
        logger.error("Environment check failed. Application may not start correctly.")
    
    patches_ok = apply_patches()
    if not patches_ok:
        logger.error("Failed to apply necessary patches.")
    
    # Only check database after environment variables are confirmed
    if env_ok:
        db_ok = check_database()
        if not db_ok:
            logger.error("Database check failed. Application may not be able to access data.")
    
    # Final status report
    logger.info("Startup script complete. Application will now attempt to start.")
    
    # Note: No need to manually start the app - gunicorn will do that after this script

if __name__ == "__main__":
    main()
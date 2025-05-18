"""
Diagnostic script for Render deployment issues.
This helps identify common problems like missing environment variables,
database connectivity issues, or module import problems.
"""

import os
import sys
import logging
import importlib
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check that all required environment variables are set"""
    required_vars = [
        "DATABASE_URL",  # Database connection string
        "SESSION_SECRET",  # Secret for session encryption
        "OPENAI_API_KEY",  # OpenAI API key
    ]
    
    optional_vars = [
        "SENDGRID_API_KEY",  # For email notifications
        "TWILIO_ACCOUNT_SID",  # For SMS notifications
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "PORT",  # Render sets this automatically
        "RENDER",  # Set by Render in production
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.environ.get(var):
            missing_optional.append(var)
    
    if missing_required:
        logger.error(f"Missing required environment variables: {', '.join(missing_required)}")
    else:
        logger.info("All required environment variables are set")
    
    if missing_optional:
        logger.warning(f"Missing optional environment variables: {', '.join(missing_optional)}")
    
    return len(missing_required) == 0

def check_database_connection():
    """Check if the database connection is working"""
    try:
        # Import the database connection
        from app import db
        
        # Try to connect to the database
        with db.engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def check_required_modules():
    """Check if all required modules are installed"""
    required_modules = [
        "flask",
        "flask_sqlalchemy",
        "flask_login",
        "werkzeug",
        "openai",
        "gunicorn",
        "psycopg2",
        "sendgrid",  # For email functionality
        "twilio",    # For SMS functionality
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Missing required modules: {', '.join(missing_modules)}")
    else:
        logger.info("All required modules are installed")
    
    return len(missing_modules) == 0

def check_gunicorn_config():
    """Check if the gunicorn configuration is correct"""
    # Check if Procfile exists and contains valid settings
    procfile_path = Path("Procfile")
    if not procfile_path.exists():
        logger.error("Procfile not found")
        return False
    
    with open(procfile_path, "r") as f:
        content = f.read()
    
    if "gunicorn" not in content:
        logger.error("Procfile does not contain gunicorn command")
        return False
    
    logger.info(f"Procfile content: {content.strip()}")
    return True

def check_render_specific():
    """Check Render-specific configuration"""
    # Check if build.sh exists for Render
    build_sh_path = Path("build.sh")
    if not build_sh_path.exists():
        logger.warning("build.sh not found (may be optional for Python apps)")
    else:
        logger.info("build.sh found")
        
    # Check if there's a requirements.txt file
    req_path = Path("requirements.txt")
    if not req_path.exists():
        logger.error("requirements.txt not found")
        return False
    
    logger.info("requirements.txt found")
    return True

def main():
    """Run all checks and print results"""
    logger.info("Running Render deployment diagnostics...")
    
    # Run all checks
    env_check = check_environment_variables()
    db_check = check_database_connection()
    modules_check = check_required_modules()
    gunicorn_check = check_gunicorn_config()
    render_check = check_render_specific()
    
    # Print summary
    logger.info("\n== Deployment Diagnostic Summary ==")
    logger.info(f"Environment variables: {'PASS' if env_check else 'FAIL'}")
    logger.info(f"Database connection: {'PASS' if db_check else 'FAIL'}")
    logger.info(f"Required modules: {'PASS' if modules_check else 'FAIL'}")
    logger.info(f"Gunicorn configuration: {'PASS' if gunicorn_check else 'FAIL'}")
    logger.info(f"Render-specific checks: {'PASS' if render_check else 'FAIL'}")
    
    if all([env_check, db_check, modules_check, gunicorn_check, render_check]):
        logger.info("All checks passed! The application should deploy successfully.")
    else:
        logger.warning("Some checks failed. Please address the issues above.")

if __name__ == "__main__":
    main()
"""
Completely isolated test route to diagnose authentication routing issues.
This bypasses all complex systems and only tests basic Flask routing.
"""

from flask import Blueprint

isolated_bp = Blueprint('isolated_test', __name__)

@isolated_bp.route('/isolated-test')
def isolated_test():
    """Ultra-minimal test route with no dependencies"""
    try:
        return "ISOLATED TEST SUCCESS - Route executed without errors"
    except Exception as e:
        return f"ISOLATED TEST ERROR: {str(e)}", 500

@isolated_bp.route('/health-check')
def health_check():
    """Simple health check endpoint"""
    try:
        return {"status": "healthy", "message": "Flask routing is working"}
    except Exception as e:
        return f"HEALTH CHECK ERROR: {str(e)}", 500
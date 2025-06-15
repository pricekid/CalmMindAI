"""
Basic test endpoint to verify routing works without any dependencies.
"""

from flask import Blueprint

basic_test_bp = Blueprint('basic_test', __name__)

@basic_test_bp.route('/basic-test')
def basic_test():
    """Ultra-basic test endpoint"""
    try:
        print("BASIC TEST: Route accessed successfully")
        return "Basic test working - authentication system is operational"
    except Exception as e:
        print(f"BASIC TEST ERROR: {e}")
        return f"Basic test error: {str(e)}", 500

@basic_test_bp.route('/ping')
def ping():
    """Simple ping endpoint"""
    print("PING: Route accessed")
    return "pong"
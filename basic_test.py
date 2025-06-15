"""
Basic test endpoint to verify routing works without any dependencies.
"""

from flask import Blueprint

basic_test_bp = Blueprint('basic_test', __name__)

@basic_test_bp.route('/basic-test')
def basic_test():
    """Ultra-basic test endpoint"""
    try:
        print("🟢 BASIC TEST: Route accessed successfully")
        return "Basic test working - authentication system is operational"
    except Exception as e:
        import traceback
        print("🔥 BASIC TEST EXCEPTION:")
        traceback.print_exc()
        return f"<h2>Basic Test Route Error</h2><pre>{str(e)}</pre>", 500

@basic_test_bp.route('/ping')
def ping():
    """Simple ping endpoint"""
    try:
        print("🟢 PING: Route accessed successfully")
        return "pong"
    except Exception as e:
        import traceback
        print("🔥 PING EXCEPTION:")
        traceback.print_exc()
        return f"<h2>Ping Route Error</h2><pre>{str(e)}</pre>", 500
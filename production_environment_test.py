"""
Test which app configuration is being used in production.
"""

import os
import logging
from flask import Blueprint, jsonify

test_bp = Blueprint('production_test', __name__)
logger = logging.getLogger(__name__)

@test_bp.route('/production-environment-check')
def production_environment_check():
    """Check which app configuration is being used"""
    try:
        env_info = {
            'RENDER': os.environ.get('RENDER', 'Not set'),
            'app_module': 'Unknown',
            'database_url_exists': bool(os.environ.get('DATABASE_URL')),
            'session_secret_exists': bool(os.environ.get('SESSION_SECRET')),
        }
        
        # Try to determine which app is being used
        try:
            if os.environ.get('RENDER'):
                env_info['app_module'] = 'render_app (expected)'
            else:
                env_info['app_module'] = 'app.py (development)'
        except:
            pass
        
        return jsonify({
            'status': 'success',
            'environment': env_info,
            'message': 'Environment check successful'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Environment check failed: {str(e)}'
        }), 500

@test_bp.route('/production-simple-login', methods=['GET', 'POST'])
def production_simple_login():
    """Ultra-simple login without any dependencies"""
    from flask import request, redirect, session
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        # Hardcoded test credentials for production verification
        if email == 'test@example.com' and password == 'test123':
            session['user_id'] = 'test-user-id'
            session['user_email'] = email
            return redirect('/dashboard')
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    # Return simple HTML form
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Production Simple Login</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
            input { width: 100%; padding: 10px; margin: 10px 0; }
            button { width: 100%; padding: 15px; background: #007bff; color: white; border: none; }
        </style>
    </head>
    <body>
        <h2>Production Simple Login</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p><small>Test: test@example.com / test123</small></p>
    </body>
    </html>
    '''
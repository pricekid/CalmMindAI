"""
Ultra-simple authentication test that bypasses all complex systems.
"""

from flask import Blueprint, request, session, jsonify

simple_auth_bp = Blueprint('simple_auth', __name__)

@simple_auth_bp.route('/simple-login-test', methods=['GET', 'POST'])
def simple_login_test():
    """Ultra-simple login test that only uses sessions"""
    try:
        print("🟢 A1 - Simple login test route accessed")
        print("A2 - Checking request method")
        if request.method == 'POST':
            print("A3 - POST request detected")
            try:
                print("A4 - Getting form data")
                email = request.form.get('email', '').lower().strip()
                password = request.form.get('password', '')
                print(f"A5 - Email: {email}, Password: {'*' * len(password)}")
                
                # Test with hardcoded credentials
                if email == 'test@example.com' and password == 'test123':
                    print("A6 - Credentials match, setting session")
                    session['authenticated'] = True
                    session['user_email'] = email
                    session['user_id'] = 'test-user-123'
                    session.permanent = True
                    print("A7 - Session set successfully")
                    
                    return jsonify({
                        'success': True,
                        'message': 'Login successful',
                        'redirect': '/dashboard'
                    })
                else:
                    print("A8 - Invalid credentials")
                    return jsonify({
                        'success': False,
                        'message': 'Invalid credentials'
                    }), 401
                    
            except Exception as e:
                print(f"A9 - POST exception: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Login error: {str(e)}'
                }), 500
        
        print("A10 - GET request - showing login form")
        # GET request - show simple login form
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Simple Login Test</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="email"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-success { background: #d1edff; color: #155724; border: 1px solid #c3e6cb; }
    </style>
</head>
<body>
    <h2>🧸 Simple Login Test</h2>
    <div id="message"></div>
    
    <form id="loginForm">
        <div class="form-group">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" value="test@example.com" required>
        </div>
        
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" value="test123" required>
        </div>
        
        <button type="submit">Login</button>
    </form>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const messageDiv = document.getElementById('message');
            
            try {
                const response = await fetch('/simple-login-test', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    messageDiv.innerHTML = '<div class="alert alert-success">' + data.message + '</div>';
                    if (data.redirect) {
                        setTimeout(() => window.location.href = data.redirect, 1000);
                    }
                } else {
                    messageDiv.innerHTML = '<div class="alert alert-danger">' + data.message + '</div>';
                }
            } catch (error) {
                messageDiv.innerHTML = '<div class="alert alert-danger">Network error: ' + error.message + '</div>';
            }
        });
    </script>
</body>
</html>
        '''
        
    except Exception as e:
        import traceback
        print("🔥 SIMPLE LOGIN TEST EXCEPTION:")
        traceback.print_exc()
        return f"<h2>Simple Login Test Route Error</h2><pre>{str(e)}</pre>", 500

@simple_auth_bp.route('/simple-logout-test')
def simple_logout_test():
    """Simple logout"""
    try:
        print("🟢 B1 - Simple logout test route accessed")
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        import traceback
        print("🔥 SIMPLE LOGOUT TEST EXCEPTION:")
        traceback.print_exc()
        return f"<h2>Simple Logout Test Route Error</h2><pre>{str(e)}</pre>", 500

@simple_auth_bp.route('/simple-status-test')
def simple_status_test():
    """Check authentication status"""
    try:
        print("🟢 C1 - Simple status test route accessed")
        return jsonify({
            'authenticated': session.get('authenticated', False),
            'user_email': session.get('user_email'),
            'user_id': session.get('user_id')
        })
    except Exception as e:
        import traceback
        print("🔥 SIMPLE STATUS TEST EXCEPTION:")
        traceback.print_exc()
        return f"<h2>Simple Status Test Route Error</h2><pre>{str(e)}</pre>", 500
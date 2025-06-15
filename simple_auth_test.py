"""
Ultra-simple authentication test that bypasses all complex systems.
"""

from flask import Blueprint, request, session, jsonify

simple_auth_bp = Blueprint('simple_auth', __name__)

@simple_auth_bp.route('/simple-login-test', methods=['GET', 'POST'])
def simple_login_test():
    """Ultra-simple login test that only uses sessions"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            # Test with hardcoded credentials
            if email == 'test@example.com' and password == 'test123':
                session['authenticated'] = True
                session['user_email'] = email
                session['user_id'] = 'test-user-123'
                session.permanent = True
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': '/dashboard'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Invalid credentials'
                }), 401
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Login error: {str(e)}'
            }), 500
    
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

@simple_auth_bp.route('/simple-logout-test')
def simple_logout_test():
    """Simple logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@simple_auth_bp.route('/simple-status-test')
def simple_status_test():
    """Check authentication status"""
    return jsonify({
        'authenticated': session.get('authenticated', False),
        'user_email': session.get('user_email'),
        'user_id': session.get('user_id')
    })
"""
Direct session-based login that bypasses Flask-Login entirely.
Uses only Flask sessions and direct database access.
"""

from flask import Blueprint, request, redirect, session, jsonify, render_template_string
from werkzeug.security import check_password_hash
import os

direct_login_bp = Blueprint('session_login', __name__)

@direct_login_bp.route('/direct-login', methods=['GET', 'POST'])
def direct_login():
    """Direct login using sessions only"""
    if request.method == 'POST':
        try:
            # Get form data
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                return jsonify({'error': 'Email and password required'}), 400
            
            # Import models inside the route to avoid initialization issues
            from models import User
            
            # Query user
            user = User.query.filter(User.email.ilike(email)).first()
            
            if user and user.password_hash:
                if check_password_hash(user.password_hash, password):
                    # Set session data (no Flask-Login needed)
                    session['user_id'] = user.id
                    session['user_email'] = user.email
                    session['user_first_name'] = user.first_name or 'User'
                    session['authenticated'] = True
                    session.permanent = True
                    
                    # Success response for AJAX
                    if request.headers.get('Content-Type') == 'application/json':
                        return jsonify({'success': True, 'redirect': '/dashboard'})
                    
                    return redirect('/dashboard')
                else:
                    return jsonify({'error': 'Invalid credentials'}), 401
            else:
                return jsonify({'error': 'User not found'}), 401
                
        except Exception as e:
            return jsonify({'error': f'Login failed: {str(e)}'}), 500
    
    # GET request - show login form
    login_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dear Teddy - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            padding: 3rem;
            width: 100%;
            max-width: 400px;
        }
        .logo {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
            text-align: center;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">🧸 Dear Teddy</div>
        <h3 class="text-center mb-4">Welcome Back</h3>
        
        <div id="error-message" class="alert alert-danger d-none"></div>
        
        <form id="loginForm">
            <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="fas fa-envelope"></i></span>
                    <input type="email" class="form-control" id="email" name="email" required>
                </div>
            </div>
            
            <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="fas fa-lock"></i></span>
                    <input type="password" class="form-control" id="password" name="password" required>
                </div>
            </div>
            
            <button type="submit" class="btn btn-primary w-100 mb-3">
                <i class="fas fa-sign-in-alt me-2"></i>Sign In
            </button>
        </form>
        
        <div class="alert alert-info">
            <strong>Test Account:</strong><br>
            Email: test@example.com<br>
            Password: test123
        </div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const errorDiv = document.getElementById('error-message');
            
            try {
                const response = await fetch('/direct-login', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        window.location.href = data.redirect;
                    } else if (response.redirected) {
                        window.location.href = response.url;
                    }
                } else {
                    const error = await response.json();
                    errorDiv.textContent = error.error || 'Login failed';
                    errorDiv.classList.remove('d-none');
                }
            } catch (error) {
                errorDiv.textContent = 'Network error: ' + error.message;
                errorDiv.classList.remove('d-none');
            }
        });
    </script>
</body>
</html>
    '''
    
    return login_html

@direct_login_bp.route('/direct-logout')
def direct_logout():
    """Direct logout"""
    session.clear()
    return redirect('/')

@direct_login_bp.route('/direct-status')
def direct_status():
    """Check authentication status"""
    return jsonify({
        'authenticated': session.get('authenticated', False),
        'user_id': session.get('user_id'),
        'user_email': session.get('user_email'),
        'user_name': session.get('user_first_name', 'User')
    })

# Simple middleware function to check authentication
def require_auth():
    """Check if user is authenticated via session"""
    return session.get('authenticated', False)

def get_current_user_data():
    """Get current user data from session"""
    if require_auth():
        return {
            'id': session.get('user_id'),
            'email': session.get('user_email'),
            'first_name': session.get('user_first_name', 'User'),
            'authenticated': True
        }
    return None
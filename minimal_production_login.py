"""
Minimal production login system that bypasses all complex dependencies.
This creates a working authentication system for production deployment.
"""

from flask import Blueprint, request, redirect, session, jsonify, render_template_string
from werkzeug.security import check_password_hash
import os
import psycopg2
from urllib.parse import urlparse

minimal_login_bp = Blueprint('minimal_login', __name__)

def get_direct_db_connection():
    """Get direct PostgreSQL connection"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL not found")
    
    parsed = urlparse(database_url)
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:]
    )

@minimal_login_bp.route('/minimal-login', methods=['GET', 'POST'])
def minimal_login():
    """Minimal login with direct database access"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                return jsonify({'error': 'Email and password required'}), 400
            
            # Direct database query
            conn = get_direct_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, email, password_hash, first_name FROM users WHERE LOWER(email) = %s",
                (email,)
            )
            user_data = cursor.fetchone()
            
            if user_data and user_data[2]:  # Check if password hash exists
                user_id, user_email, password_hash, first_name = user_data
                
                if check_password_hash(password_hash, password):
                    # Set session data
                    session['user_id'] = user_id
                    session['user_email'] = user_email
                    session['user_first_name'] = first_name or 'User'
                    session['authenticated'] = True
                    
                    cursor.close()
                    conn.close()
                    
                    return redirect('/dashboard')
                else:
                    cursor.close()
                    conn.close()
                    return jsonify({'error': 'Invalid credentials'}), 401
            else:
                cursor.close()
                conn.close()
                return jsonify({'error': 'User not found'}), 401
                
        except Exception as e:
            return jsonify({'error': f'Login failed: {str(e)}'}), 500
    
    # GET request - show login form
    login_form = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dear Teddy - Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 20px; min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }
            .login-container { 
                background: white; max-width: 400px; width: 100%; padding: 40px; border-radius: 12px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1); text-align: center;
            }
            .logo { font-size: 24px; font-weight: bold; color: #333; margin-bottom: 30px; }
            input { 
                width: 100%; padding: 15px; margin: 10px 0; border: 2px solid #f0f0f0; 
                border-radius: 8px; font-size: 16px; box-sizing: border-box;
            }
            input:focus { border-color: #667eea; outline: none; }
            button { 
                width: 100%; padding: 15px; background: #667eea; color: white; border: none; 
                border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 20px;
            }
            button:hover { background: #5a67d8; }
            .test-info { 
                background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px; 
                font-size: 14px; color: #666;
            }
            .error { color: #e53e3e; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">🧸 Dear Teddy</div>
            <h2 style="color: #333; margin-bottom: 30px;">Welcome Back</h2>
            
            <form method="POST" id="loginForm">
                <input type="email" name="email" placeholder="Email Address" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Sign In</button>
            </form>
            
            <div class="test-info">
                <strong>Test Account:</strong><br>
                Email: test@example.com<br>
                Password: test123
            </div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                
                fetch('/minimal-login', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;
                    } else if (!response.ok) {
                        return response.json().then(data => {
                            throw new Error(data.error || 'Login failed');
                        });
                    }
                })
                .catch(error => {
                    alert('Login failed: ' + error.message);
                });
            });
        </script>
    </body>
    </html>
    '''
    
    return login_form

@minimal_login_bp.route('/minimal-logout')
def minimal_logout():
    """Minimal logout"""
    session.clear()
    return redirect('/')

@minimal_login_bp.route('/minimal-status')
def minimal_status():
    """Check authentication status"""
    return jsonify({
        'authenticated': session.get('authenticated', False),
        'user_id': session.get('user_id'),
        'user_email': session.get('user_email'),
        'user_name': session.get('user_first_name', 'User')
    })

@minimal_login_bp.route('/minimal-db-test')
def minimal_db_test():
    """Test direct database connectivity"""
    try:
        conn = get_direct_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT email FROM users WHERE email = 'test@example.com'")
        test_user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'total_users': user_count,
            'test_user_exists': bool(test_user),
            'database_host': urlparse(os.environ.get('DATABASE_URL')).hostname
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
"""
Production authentication fix - Create a robust registration and login system
that works reliably on Render deployment
"""
from flask import Blueprint, request, jsonify, render_template_string, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2
import uuid
import logging

production_auth_bp = Blueprint('production_auth', __name__)

# Simple HTML template for registration
REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Register - Dear Teddy</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #E6B980 0%, #A05C2C 100%); min-height: 100vh; }
        .card { border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    </style>
</head>
<body class="d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card border-0">
                    <div class="card-body p-5">
                        <h2 class="text-center mb-4" style="color: #A05C2C;">Join Dear Teddy</h2>
                        {% if error %}
                        <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        {% if success %}
                        <div class="alert alert-success">{{ success }}</div>
                        {% else %}
                        <form method="post">
                            <div class="mb-3">
                                <input type="text" class="form-control" name="username" placeholder="Username" required>
                            </div>
                            <div class="mb-3">
                                <input type="email" class="form-control" name="email" placeholder="Email" required>
                            </div>
                            <div class="mb-3">
                                <input type="password" class="form-control" name="password" placeholder="Password" required>
                            </div>
                            <button type="submit" class="btn w-100" style="background-color: #A05C2C; color: white;">Create Account</button>
                        </form>
                        {% endif %}
                        <div class="text-center mt-3">
                            <a href="/production-login" class="text-decoration-none" style="color: #A05C2C;">Already have an account? Log in</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Simple HTML template for login
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Dear Teddy</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #E6B980 0%, #A05C2C 100%); min-height: 100vh; }
        .card { border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    </style>
</head>
<body class="d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card border-0">
                    <div class="card-body p-5">
                        <h2 class="text-center mb-4" style="color: #A05C2C;">Welcome Back</h2>
                        {% if error %}
                        <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        <form method="post">
                            <div class="mb-3">
                                <input type="email" class="form-control" name="email" placeholder="Email" required>
                            </div>
                            <div class="mb-3">
                                <input type="password" class="form-control" name="password" placeholder="Password" required>
                            </div>
                            <button type="submit" class="btn w-100" style="background-color: #A05C2C; color: white;">Log In</button>
                        </form>
                        <div class="text-center mt-3">
                            <a href="/production-register" class="text-decoration-none" style="color: #A05C2C;">Need an account? Sign up</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@production_auth_bp.route('/production-register', methods=['GET', 'POST'])
def production_register():
    """Production-ready registration endpoint"""
    error = None
    success = None
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            # Validate inputs
            if not all([username, email, password]):
                error = 'All fields are required'
            elif len(password) < 6:
                error = 'Password must be at least 6 characters'
            else:
                # Connect to database
                try:
                    conn = psycopg2.connect(os.environ['DATABASE_URL'])
                    cur = conn.cursor()
                    
                    # Check if user already exists
                    cur.execute('SELECT id FROM "user" WHERE email = %s', (email,))
                    if cur.fetchone():
                        error = 'Email already registered'
                    else:
                        # Create user
                        user_id = str(uuid.uuid4())
                        password_hash = generate_password_hash(password)
                        
                        cur.execute("""
                            INSERT INTO "user" (id, username, email, password_hash, created_at, 
                                              demographics_collected, notifications_enabled, 
                                              morning_reminder_enabled, evening_reminder_enabled, 
                                              sms_notifications_enabled, welcome_message_shown) 
                            VALUES (%s, %s, %s, %s, NOW(), false, true, true, true, false, false)
                        """, (user_id, username, email, password_hash))
                        
                        conn.commit()
                        success = 'Account created successfully! You can now log in.'
                        
                except psycopg2.Error as e:
                    error = f'Database error: {str(e)}'
                except Exception as e:
                    error = f'Registration failed: {str(e)}'
                finally:
                    if 'conn' in locals():
                        conn.close()
                        
        except Exception as e:
            error = f'Unexpected error: {str(e)}'
    
    return render_template_string(REGISTER_TEMPLATE, error=error, success=success)

@production_auth_bp.route('/production-login', methods=['GET', 'POST'])
def production_login():
    """Production-ready login endpoint"""
    error = None
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not all([email, password]):
                error = 'Email and password are required'
            else:
                try:
                    conn = psycopg2.connect(os.environ['DATABASE_URL'])
                    cur = conn.cursor()
                    
                    # Get user
                    cur.execute('SELECT id, password_hash FROM "user" WHERE email = %s', (email,))
                    user = cur.fetchone()
                    
                    if user and check_password_hash(user[1], password):
                        # Login successful - set session
                        session['user_id'] = user[0]
                        session.permanent = True
                        return redirect('/dashboard')
                    else:
                        error = 'Invalid email or password'
                        
                except psycopg2.Error as e:
                    error = f'Database error: {str(e)}'
                except Exception as e:
                    error = f'Login failed: {str(e)}'
                finally:
                    if 'conn' in locals():
                        conn.close()
                        
        except Exception as e:
            error = f'Unexpected error: {str(e)}'
    
    return render_template_string(LOGIN_TEMPLATE, error=error)

# Register the blueprint in app.py with this:
# app.register_blueprint(production_auth_bp)
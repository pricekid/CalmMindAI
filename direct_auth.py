"""
Direct authentication system without CSRF protection
Simple, reliable registration and login for production deployment
"""
from flask import request, render_template_string, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2
import uuid

def register_direct_auth(app):
    """Register direct authentication routes"""
    
    @app.route('/direct-register', methods=['GET', 'POST'])
    def direct_register():
        """Direct registration without CSRF"""
        if request.method == 'GET':
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Register - Dear Teddy</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="bg-light">
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h2 class="text-center mb-4">Join Dear Teddy</h2>
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
                                        <button type="submit" class="btn btn-primary w-100">Create Account</button>
                                    </form>
                                    <div class="text-center mt-3">
                                        <a href="/direct-login">Already have an account? Log in</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
        
        # Handle POST registration
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not all([username, email, password]):
                return jsonify({'error': 'All fields are required'}), 400
            
            # Connect to database
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cur = conn.cursor()
            
            # Check if user exists
            cur.execute('SELECT id FROM "user" WHERE email = %s', (email,))
            if cur.fetchone():
                return jsonify({'error': 'Email already registered'}), 400
            
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
            conn.close()
            
            return jsonify({'success': True, 'message': 'Account created successfully!', 'user_id': user_id})
            
        except Exception as e:
            return jsonify({'error': f'Registration failed: {str(e)}'}), 500
    
    @app.route('/direct-login', methods=['GET', 'POST'])
    def direct_login():
        """Direct login without CSRF"""
        if request.method == 'GET':
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login - Dear Teddy</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="bg-light">
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h2 class="text-center mb-4">Welcome Back</h2>
                                    <form method="post">
                                        <div class="mb-3">
                                            <input type="email" class="form-control" name="email" placeholder="Email" required>
                                        </div>
                                        <div class="mb-3">
                                            <input type="password" class="form-control" name="password" placeholder="Password" required>
                                        </div>
                                        <button type="submit" class="btn btn-primary w-100">Log In</button>
                                    </form>
                                    <div class="text-center mt-3">
                                        <a href="/direct-register">Need an account? Sign up</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
        
        # Handle POST login
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not all([email, password]):
                return jsonify({'error': 'Email and password are required'}), 400
            
            # Connect to database
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cur = conn.cursor()
            
            # Get user
            cur.execute('SELECT id, password_hash FROM "user" WHERE email = %s', (email,))
            user = cur.fetchone()
            conn.close()
            
            if user and check_password_hash(user[1], password):
                # Login successful
                session['user_id'] = user[0]
                session.permanent = True
                return redirect('/dashboard')
            else:
                return jsonify({'error': 'Invalid email or password'}), 401
                
        except Exception as e:
            return jsonify({'error': f'Login failed: {str(e)}'}), 500
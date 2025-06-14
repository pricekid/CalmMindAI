#!/usr/bin/env python3
"""
Production debugging script to identify deployment issues.
This will help diagnose why the production site is returning 500 errors.
"""

import os
import sys
from flask import Flask

def check_production_requirements():
    """Check if all required dependencies and configurations are present"""
    
    print("=== Production Environment Debug ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check environment variables
    required_env_vars = [
        'DATABASE_URL', 'SESSION_SECRET', 'OPENAI_API_KEY',
        'SENDGRID_API_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN'
    ]
    
    print("\n=== Environment Variables ===")
    for var in required_env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var}: Present ({len(value)} chars)")
        else:
            print(f"✗ {var}: Missing")
    
    # Check required Python packages
    required_packages = [
        'flask', 'sqlalchemy', 'psycopg2', 'werkzeug', 
        'openai', 'sendgrid', 'twilio', 'flask_login'
    ]
    
    print("\n=== Python Packages ===")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}: Available")
        except ImportError as e:
            print(f"✗ {package}: Missing - {e}")
    
    # Test basic Flask app creation
    print("\n=== Flask App Test ===")
    try:
        app = Flask(__name__)
        app.secret_key = os.environ.get('SESSION_SECRET', 'test-key')
        print("✓ Flask app creation: Success")
        
        # Test database connection
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            import psycopg2
            try:
                conn = psycopg2.connect(db_url)
                conn.close()
                print("✓ Database connection: Success")
            except Exception as e:
                print(f"✗ Database connection: Failed - {e}")
        else:
            print("✗ Database connection: No DATABASE_URL")
            
    except Exception as e:
        print(f"✗ Flask app creation: Failed - {e}")
    
    # Check file structure
    print("\n=== File Structure ===")
    critical_files = [
        'app.py', 'models.py', 'routes.py', 'main.py',
        'templates/register.html', 'templates/stable_login.html'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}: Present")
        else:
            print(f"✗ {file_path}: Missing")

def create_minimal_production_app():
    """Create a minimal Flask app to test production deployment"""
    
    minimal_app_code = '''
import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'fallback-key')

@app.route('/')
def home():
    return jsonify({
        "status": "production_test",
        "message": "Minimal production app is working",
        "session_secret_configured": bool(os.environ.get('SESSION_SECRET')),
        "database_url_configured": bool(os.environ.get('DATABASE_URL'))
    })

@app.route('/test-register')
def test_register():
    return render_template_string("""
    <html>
    <head><title>Test Registration</title></head>
    <body>
        <h1>Production Test Registration</h1>
        <form method="post" action="/test-register">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="email" name="email" placeholder="Email" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Test Register</button>
        </form>
    </body>
    </html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
'''
    
    with open('minimal_production_test.py', 'w') as f:
        f.write(minimal_app_code)
    
    print("Created minimal_production_test.py for production testing")

if __name__ == "__main__":
    check_production_requirements()
    create_minimal_production_app()
#!/usr/bin/env python3
"""
WSGI entry point for Render.com deployment
This file provides the application object that gunicorn expects
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application
try:
    # Try to import from production.py first (recommended for Render)
    from production import app as application
    print("Loaded application from production.py")
except ImportError:
    try:
        # Fallback to main.py
        from main import app as application
        print("Loaded application from main.py")
    except ImportError:
        # Final fallback - create minimal app
        from flask import Flask
        application = Flask(__name__)
        
        @application.route('/')
        def hello():
            return '<h1>Flask App Running</h1><p>Deployment successful but main app not found</p>'
        
        @application.route('/health')
        def health():
            return {'status': 'ok', 'message': 'Fallback app running'}
        
        print("Using fallback Flask application")

# Ensure the app can be imported as 'application' for gunicorn
app = application

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)
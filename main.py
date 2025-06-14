#!/usr/bin/env python3
"""
Production main.py for Dear Teddy - Render deployment
This file imports from render_app.py to avoid model conflicts
"""

# Import the working app from render_app.py
try:
    from render_app import app
    print("Successfully imported app from render_app.py")
except ImportError as e:
    print(f"Failed to import from render_app: {e}")
    # Fallback to a minimal working app
    import os
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "fallback-key")
    
    @app.route('/')
    def index():
        return '<h1>Dear Teddy - Fallback Mode</h1><p>Please check render_app.py</p>'
    
    @app.route('/health')
    def health():
        return jsonify({"status": "fallback", "message": "Using fallback app"})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
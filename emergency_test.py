#!/usr/bin/env python3
"""
Emergency test application - completely independent of existing code
This will help determine if the issue is systemic to Replit or specific to our app
"""

from flask import Flask, jsonify
from datetime import datetime
import os

# Create completely fresh Flask app
emergency_app = Flask(__name__)

@emergency_app.after_request
def emergency_cache_headers(response):
    """Apply strongest possible cache prevention"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Emergency-Timestamp'] = datetime.utcnow().isoformat() + 'Z'
    response.headers['X-Emergency-Test'] = 'FRESH-RESPONSE'
    return response

@emergency_app.route('/emergency')
def emergency_test():
    timestamp = datetime.utcnow().isoformat()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Test - {timestamp}</title>
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
        <meta http-equiv="Pragma" content="no-cache">
        <meta http-equiv="Expires" content="0">
    </head>
    <body>
        <h1 style="color: green;">🚨 EMERGENCY TEST SUCCESS</h1>
        <p><strong>Fresh Timestamp:</strong> {timestamp}</p>
        <p><strong>Test ID:</strong> EMERGENCY-{timestamp.replace(':', '-')}</p>
        <p><strong>Status:</strong> This is a completely fresh Flask app</p>
        <p><strong>Cache Headers:</strong> Maximum strength applied</p>
        <hr>
        <p>If you see this page, the basic Flask functionality works.</p>
        <p>Refresh to verify timestamp changes.</p>
        <script>
            console.log('Emergency test loaded at:', '{timestamp}');
            document.title = 'Emergency Test - {timestamp}';
        </script>
    </body>
    </html>
    """

@emergency_app.route('/emergency-json')
def emergency_json():
    return jsonify({
        'status': 'emergency_success',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Fresh JSON response from emergency app',
        'test_id': f"JSON-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    })

if __name__ == '__main__':
    print("🚨 Starting Emergency Test Application")
    emergency_app.run(host='0.0.0.0', port=8000, debug=True)

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

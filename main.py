import os

# Use simplified app for Render deployment, full app for development
if os.environ.get('RENDER'):
    from render_app import app
else:
    from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
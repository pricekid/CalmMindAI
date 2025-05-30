from app import app

# Minimal clean app for testing

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
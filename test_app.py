# test_app.py
from flask import Flask

app = Flask(__name__)

@app.route("/basic-test")
def basic_test():
    print("🟢 Entered /basic-test")
    return "✅ Basic test working"

@app.route("/health")
def health():
    print("🟢 Entered /health")
    return "✅ Health check working"

@app.route("/")
def home():
    print("🟢 Entered /")
    return "✅ Root route working"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
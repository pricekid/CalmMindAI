from flask import Flask

app = Flask(__name__)

@app.route("/test-basic")
def test_basic():
    return "✅ Basic test route works!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
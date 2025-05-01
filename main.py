
from app import app, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Ensure database tables exist
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

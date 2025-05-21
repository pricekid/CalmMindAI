"""
Script to directly create or verify a user entry in the database.
This bypasses all app-level abstractions and works directly with SQL.
"""

import os
import sys
from urllib.parse import urlparse

# Check direct database access
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("ERROR: DATABASE_URL environment variable is missing!")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2 import sql
    from werkzeug.security import generate_password_hash
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "werkzeug"])
    import psycopg2
    from psycopg2 import sql
    from werkzeug.security import generate_password_hash

# Parse the DATABASE_URL
parsed = urlparse(db_url)
dbname = parsed.path[1:]  # remove leading slash
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port

# Connect to the database
print(f"Connecting to database {dbname} on {host}:{port}...")
conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)

# Create test user details
test_email = "teddy.leon@alumni.uwi.edu"
test_username = "teddy.leon"
test_password = "Teddy1973"
hashed_password = generate_password_hash(test_password)
user_id = "12345678-1234-5678-1234-567812345678"  # Fixed ID for deterministic lookup

# Create a cursor
cur = conn.cursor()

# Check if users table exists
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
table_exists = cur.fetchone()[0]

if not table_exists:
    print("Creating users table...")
    # Create users table with minimal required fields
    cur.execute("""
    CREATE TABLE users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        username TEXT,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    print("Users table created successfully.")

# Check if test user exists
cur.execute("SELECT id FROM users WHERE email = %s", (test_email,))
user_exists = cur.fetchone()

if user_exists:
    print(f"Test user already exists with ID: {user_exists[0]}")
    
    # Update password hash to ensure it's correct
    cur.execute(
        "UPDATE users SET password_hash = %s WHERE email = %s", 
        (hashed_password, test_email)
    )
    conn.commit()
    print("Password updated for existing user.")
else:
    # Insert test user
    print(f"Creating test user with ID: {user_id}")
    cur.execute(
        "INSERT INTO users (id, email, username, password_hash) VALUES (%s, %s, %s, %s)",
        (user_id, test_email, test_username, hashed_password)
    )
    conn.commit()
    print("Test user created successfully.")

# Close the connection
cur.close()
conn.close()

print("Done! You should now be able to log in with:")
print(f"Email: {test_email}")
print(f"Password: {test_password}")
print("Try using the emergency login at /emergency-login")
"""
Emergency Render User Repair Script

This script repairs the test user account directly using SQL.
It can be run from the Render shell console if login fails.
"""

import os
import sys
import uuid
from datetime import datetime

print("Emergency User Repair for Render")
print("--------------------------------")

# Check environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in environment!")
    sys.exit(1)

try:
    import psycopg2
    from werkzeug.security import generate_password_hash
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "werkzeug"])
    import psycopg2
    from werkzeug.security import generate_password_hash

# Test user credentials
TEST_EMAIL = "teddy.leon@alumni.uwi.edu"
TEST_PASSWORD = "Teddy1973"
TEST_USERNAME = "teddy"

print(f"Connecting to database...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    print("Database connection successful!")
except Exception as e:
    print(f"ERROR: Could not connect to database: {str(e)}")
    sys.exit(1)

# Check tables
print("Checking database structure...")
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'users'
    );
""")
has_users_table = cursor.fetchone()[0]

if not has_users_table:
    print("Creating users table...")
    cursor.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            username TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Users table created!")
else:
    print("Users table exists")

# Check for test user
print(f"Looking for test user with email: {TEST_EMAIL}")
cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (TEST_EMAIL,))
user = cursor.fetchone()

if user:
    user_id = user[0]
    print(f"Found existing user with ID: {user_id}")
    
    # Update user
    hashed_password = generate_password_hash(TEST_PASSWORD)
    cursor.execute("""
        UPDATE users 
        SET password_hash = %s, 
            updated_at = %s 
        WHERE id = %s
    """, (hashed_password, datetime.now(), user_id))
    
    print("Test user password updated successfully!")
else:
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = generate_password_hash(TEST_PASSWORD)
    
    cursor.execute("""
        INSERT INTO users (id, email, username, password_hash, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        TEST_EMAIL,
        TEST_USERNAME,
        hashed_password,
        datetime.now(),
        datetime.now()
    ))
    
    print(f"Created new test user with ID: {user_id}")

# Confirm user exists
cursor.execute("""
    SELECT id, email, username, created_at 
    FROM users 
    WHERE LOWER(email) = LOWER(%s)
""", (TEST_EMAIL,))
user_info = cursor.fetchone()

if user_info:
    print("\nUser details:")
    print(f"  ID: {user_info[0]}")
    print(f"  Email: {user_info[1]}")
    print(f"  Username: {user_info[2]}")
    print(f"  Created: {user_info[3]}")
    print("\nLogin instructions:")
    print("1. Go to: https://dearteddy-4vqj.onrender.com/emergency-login")
    print(f"2. Login with these credentials:")
    print(f"   - Email: {TEST_EMAIL}")
    print(f"   - Password: {TEST_PASSWORD}")
else:
    print("ERROR: Failed to verify user was created!")

# Close connections
cursor.close()
conn.close()

print("\nUser repair script completed!")
"""
Script to verify database connection on Render and ensure tables exist.
"""

import os
import sys
import datetime
import uuid

# Get environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set!")
    sys.exit(1)

# Install required packages
try:
    import psycopg2
except ImportError:
    print("Installing psycopg2...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

print(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'DB'}")

try:
    # Connect to the database
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check connection
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"PostgreSQL version: {db_version[0]}")
    
    # Check if users table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
    """)
    users_table_exists = cursor.fetchone()[0]
    
    if users_table_exists:
        print("Users table exists!")
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"Total users in database: {user_count}")
        
        # Check if test user exists
        test_email = "teddy.leon@alumni.uwi.edu"
        cursor.execute("SELECT id, email, username FROM users WHERE LOWER(email) = LOWER(%s);", (test_email,))
        test_user = cursor.fetchone()
        
        if test_user:
            print(f"Test user exists with ID: {test_user[0]}")
            print(f"Email: {test_user[1]}")
            print(f"Username: {test_user[2]}")
        else:
            print(f"Test user with email {test_email} not found!")
    else:
        print("Users table does not exist!")
        
    # Close connection
    cursor.close()
    conn.close()
    
    print("Database verification completed successfully!")
    
except Exception as e:
    print(f"ERROR: Failed to connect to the database: {str(e)}")
    sys.exit(1)
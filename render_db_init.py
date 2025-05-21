"""
Render Database Initialization Script

This script runs automatically on Render deployment to ensure
the database is properly configured with the test user.

It performs the following:
1. Verifies database connection
2. Creates tables if needed
3. Creates the test user if it doesn't exist
4. Validates database schema

IMPORTANT: This script is called from the build.sh script on Render deployment
"""

import os
import sys
import time
import uuid
import logging
from datetime import datetime
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("render_db_init")

# Check if we're running on Render
if os.environ.get('RENDER', '').lower() != 'true':
    logger.info("Not running on Render, skipping initialization")
    sys.exit(0)

# Get database connection info
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    logger.error("DATABASE_URL environment variable not found!")
    sys.exit(1)

logger.info("Starting database initialization for Render deployment")

# Install required packages
try:
    import psycopg2
    from psycopg2 import sql
    from werkzeug.security import generate_password_hash
except ImportError:
    logger.info("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "werkzeug"])
    import psycopg2
    from psycopg2 import sql
    from werkzeug.security import generate_password_hash

# Test user details
TEST_USER_EMAIL = "teddy.leon@alumni.uwi.edu"
TEST_USER_USERNAME = "teddy"
TEST_USER_PASSWORD = "Teddy1973"
TEST_USER_ID = str(uuid.uuid4())

# Wait for database to be ready
max_retries = 10
retry_count = 0
connected = False

while retry_count < max_retries and not connected:
    try:
        logger.info(f"Attempting to connect to database (attempt {retry_count+1}/{max_retries})...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT 1")
        connected = True
        logger.info("Successfully connected to database!")
    except Exception as e:
        logger.warning(f"Failed to connect to database: {str(e)}")
        retry_count += 1
        
        if retry_count < max_retries:
            wait_time = 5
            logger.info(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
        else:
            logger.error("Maximum retry attempts reached. Could not connect to database.")
            sys.exit(1)

# Function to check if a table exists
def table_exists(table_name):
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

# Function to check if a column exists in a table
def column_exists(table_name, column_name):
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s 
            AND column_name = %s
        );
    """, (table_name, column_name))
    return cursor.fetchone()[0]

# Check if users table exists
if not table_exists('users'):
    logger.warning("Users table does not exist. Creating it now...")
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
    logger.info("Users table created successfully!")
else:
    logger.info("Users table already exists")

# Add any missing columns to users table
required_columns = {
    'id': 'TEXT PRIMARY KEY',
    'email': 'TEXT UNIQUE',
    'username': 'TEXT',
    'password_hash': 'TEXT',
    'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
}

for col_name, col_type in required_columns.items():
    if not column_exists('users', col_name):
        logger.warning(f"Column '{col_name}' missing from users table. Adding it now...")
        cursor.execute(sql.SQL("ALTER TABLE users ADD COLUMN {} {}").format(
            sql.Identifier(col_name), sql.SQL(col_type)
        ))
        logger.info(f"Column '{col_name}' added successfully!")

# Check if test user exists
cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (TEST_USER_EMAIL,))
test_user = cursor.fetchone()

if test_user:
    logger.info(f"Test user already exists with ID: {test_user[0]}")
    
    # Ensure password is correct
    hashed_password = generate_password_hash(TEST_USER_PASSWORD)
    cursor.execute(
        "UPDATE users SET password_hash = %s, updated_at = %s WHERE LOWER(email) = LOWER(%s)",
        (hashed_password, datetime.now(), TEST_USER_EMAIL)
    )
    logger.info("Test user password updated")
else:
    # Create test user
    logger.warning(f"Test user does not exist. Creating it now...")
    
    hashed_password = generate_password_hash(TEST_USER_PASSWORD)
    cursor.execute("""
        INSERT INTO users (id, email, username, password_hash, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        TEST_USER_ID,
        TEST_USER_EMAIL,
        TEST_USER_USERNAME,
        hashed_password,
        datetime.now(),
        datetime.now()
    ))
    
    logger.info(f"Test user created successfully with ID: {TEST_USER_ID}")

# Check if journal_entries table exists
if not table_exists('journal_entries'):
    logger.warning("Journal entries table does not exist. Creating it now...")
    cursor.execute("""
        CREATE TABLE journal_entries (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES users(id),
            title TEXT,
            content TEXT,
            anxiety_level INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ai_insight TEXT,
            ai_followup TEXT
        )
    """)
    logger.info("Journal entries table created successfully!")
else:
    logger.info("Journal entries table already exists")

# Close database connection
cursor.close()
conn.close()

logger.info("Database initialization completed successfully")
print("✅ Database initialized successfully for Render deployment")
print(f"✅ Test user available: {TEST_USER_EMAIL} / {TEST_USER_PASSWORD}")
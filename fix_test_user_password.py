#!/usr/bin/env python3
"""
Fix the test user password hash in the database.
"""
import os
import psycopg2
from werkzeug.security import generate_password_hash

def fix_test_user_password():
    """Fix the password hash for test@example.com"""
    print("Fixing test user password...")
    
    # Connect to database
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Generate correct password hash for 'test123'
    correct_hash = generate_password_hash('test123')
    print(f"Generated new password hash: {correct_hash[:50]}...")
    
    # Update the test user's password hash
    cur.execute(
        'UPDATE "user" SET password_hash = %s WHERE email = %s',
        (correct_hash, 'test@example.com')
    )
    
    rows_affected = cur.rowcount
    print(f"Updated {rows_affected} user record(s)")
    
    # Commit the change
    conn.commit()
    
    # Verify the fix
    cur.execute('SELECT username, email, password_hash FROM "user" WHERE email = %s', ('test@example.com',))
    user_data = cur.fetchone()
    
    if user_data:
        username, email, password_hash = user_data
        print(f"Verification - User: {username}, Email: {email}")
        print(f"New hash starts with: {password_hash[:30]}...")
        
        # Test the new password
        from werkzeug.security import check_password_hash
        password_valid = check_password_hash(password_hash, 'test123')
        print(f"Password validation test: {'PASS' if password_valid else 'FAIL'}")
    
    cur.close()
    conn.close()
    
    return True

if __name__ == "__main__":
    fix_test_user_password()
    print("Test user password fix complete!")
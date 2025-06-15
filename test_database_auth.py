#!/usr/bin/env python3
"""
Test database authentication directly to verify user credentials work.
"""
import os
import psycopg2
from werkzeug.security import check_password_hash

def test_user_authentication():
    """Test user authentication directly against the database"""
    print("Testing database authentication...")
    
    # Connect to database
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Test credentials
    test_users = [
        ('test@example.com', 'test123'),
        ('returning@example.com', 'return123')
    ]
    
    for email, password in test_users:
        print(f"\nTesting {email}:")
        
        # Get user from database
        cur.execute('SELECT id, username, email, password_hash FROM "user" WHERE email = %s', (email,))
        user_data = cur.fetchone()
        
        if user_data:
            user_id, username, user_email, password_hash = user_data
            print(f"  User found: {username} ({user_id})")
            print(f"  Has password hash: {'Yes' if password_hash else 'No'}")
            
            if password_hash:
                # Test password verification
                password_valid = check_password_hash(password_hash, password)
                print(f"  Password valid: {'Yes' if password_valid else 'No'}")
                
                if not password_valid:
                    print(f"  Password hash format: {password_hash[:50]}...")
            else:
                print("  ERROR: No password hash found")
        else:
            print(f"  User not found in database")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    test_user_authentication()
#!/usr/bin/env python3
"""
Test user creation directly with database to verify functionality
"""
import os
import uuid
import psycopg2
from werkzeug.security import generate_password_hash

def test_user_creation():
    """Test creating a user directly in the database"""
    try:
        # Connect to database
        database_url = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Create test user
        user_id = str(uuid.uuid4())
        username = f'testuser_{int(uuid.uuid4().int)}'[:20]
        email = f'{username}@example.com'
        password_hash = generate_password_hash('testpass123')
        
        cursor.execute("""
            INSERT INTO "user" (
                id, username, email, password_hash, created_at,
                demographics_collected, notifications_enabled,
                morning_reminder_enabled, evening_reminder_enabled,
                sms_notifications_enabled, welcome_message_shown
            ) VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
            RETURNING id, username, email
        """, (user_id, username, email, password_hash, False, True, True, True, False, False))
        
        result = cursor.fetchone()
        conn.commit()
        
        print(f"SUCCESS: User created - ID: {result[0]}, Username: {result[1]}, Email: {result[2]}")
        
        # Clean up
        cursor.execute('DELETE FROM "user" WHERE id = %s', (user_id,))
        conn.commit()
        print("Test user cleaned up successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    test_user_creation()
#!/usr/bin/env python3
import psycopg2
import os
import traceback

def test_db_connection():
    """Test database connection and user insertion"""
    try:
        # Connect to database
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not set")
            return
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test insert into user table with unique email
        import time
        unique_email = f'test{int(time.time())}@example.com'
        cursor.execute("""
            INSERT INTO "user" (id, username, email, password_hash, created_at, demographics_collected, notifications_enabled, morning_reminder_enabled, evening_reminder_enabled, sms_notifications_enabled, welcome_message_shown) 
            VALUES (gen_random_uuid()::text, 'testuser', %s, 'fakehash', NOW(), false, true, true, true, false, false) 
            RETURNING id;
        """, (unique_email,))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"SUCCESS: inserted user id={new_id}")
        
        # Clean up test user
        cursor.execute('DELETE FROM "user" WHERE id = %s', (new_id,))
        conn.commit()
        print("Test user cleaned up successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print("ERROR: Database connection or insertion failed")
        print(f"Exception: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    test_db_connection()
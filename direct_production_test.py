"""
Direct production database test to identify SQLAlchemy issues.
"""

import os
import logging
import psycopg2
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_database():
    """Test direct database connection and user authentication"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found")
            return False
        
        # Parse database URL
        parsed = urlparse(database_url)
        
        print(f"🔗 Connecting to database: {parsed.hostname}:{parsed.port}")
        
        # Direct connection
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]
        )
        
        cursor = conn.cursor()
        
        # Test queries
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Users table accessible: {user_count} users found")
        
        # Test specific user
        cursor.execute("SELECT id, email, password_hash FROM users WHERE email = %s", ('test@example.com',))
        user_data = cursor.fetchone()
        
        if user_data:
            print(f"✅ Test user found: ID={user_data[0]}, Email={user_data[1]}")
            print(f"✅ Password hash exists: {bool(user_data[2])}")
        else:
            print("❌ Test user not found")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def test_sqlalchemy_import():
    """Test SQLAlchemy import and model loading"""
    try:
        print("🧪 Testing SQLAlchemy imports...")
        
        from extensions import db
        print("✅ Extensions.db imported successfully")
        
        from models import User
        print("✅ User model imported successfully")
        
        # Test if we can access the User model
        print(f"✅ User model table name: {User.__tablename__}")
        
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy import error: {str(e)}")
        return False

def test_flask_app_context():
    """Test Flask app context creation"""
    try:
        print("🧪 Testing Flask app context...")
        
        # Import the correct app based on environment
        if os.environ.get('RENDER'):
            from render_app import app
            print("✅ Using render_app for production")
        else:
            from app import app
            print("✅ Using standard app for development")
        
        with app.app_context():
            from models import User
            
            # Test a simple query
            user = User.query.filter_by(email='test@example.com').first()
            if user:
                print(f"✅ SQLAlchemy query successful: {user.email}")
            else:
                print("❌ User not found via SQLAlchemy")
        
        return True
    except Exception as e:
        print(f"❌ Flask app context error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Production Database Diagnostic")
    print("=" * 50)
    
    # Test 1: Direct database connection
    print("\n1. Testing direct database connection...")
    db_success = test_direct_database()
    
    # Test 2: SQLAlchemy imports
    print("\n2. Testing SQLAlchemy imports...")
    import_success = test_sqlalchemy_import()
    
    # Test 3: Flask app context
    print("\n3. Testing Flask app context...")
    app_success = test_flask_app_context()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"Direct DB: {'✅' if db_success else '❌'}")
    print(f"Imports: {'✅' if import_success else '❌'}")
    print(f"App Context: {'✅' if app_success else '❌'}")
    
    if db_success and import_success and app_success:
        print("🎉 All tests passed - authentication should work")
    else:
        print("⚠️  Issues detected - login may fail")
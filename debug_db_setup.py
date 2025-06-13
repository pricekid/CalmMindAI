
#!/usr/bin/env python3
"""
Debug script to check database setup and registration system
"""

def test_db_setup():
    """Test the database setup"""
    print("Testing database setup...")
    
    try:
        # Import the shared database instance
        from extensions import db
        print("✓ Successfully imported shared db from extensions")
        
        # Import models
        from models import User
        print("✓ Successfully imported User model")
        
        # Test the app creation and db initialization
        from app import create_app
        app = create_app()
        print("✓ Successfully created app instance")
        
        with app.app_context():
            # Test database connection
            try:
                users = User.query.limit(1).all()
                print(f"✓ Database connection working - found {len(users)} users")
            except Exception as e:
                print(f"✗ Database query failed: {str(e)}")
                
            # Test registration blueprint
            try:
                from simple_register_fixed import simple_register_bp
                print("✓ Successfully imported clean registration blueprint")
            except Exception as e:
                print(f"✗ Failed to import registration blueprint: {str(e)}")
                
        print("\nDatabase setup looks good!")
        
    except Exception as e:
        print(f"✗ Database setup error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_setup()

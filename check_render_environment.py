#!/usr/bin/env python3
"""
Check environment variables and secrets for Render deployment.
This helps identify missing or misconfigured environment variables.
"""

import os

def check_environment_variables():
    """Check all required environment variables for production deployment"""
    
    required_vars = {
        'DATABASE_URL': 'PostgreSQL database connection string',
        'SESSION_SECRET': 'Flask session secret key',
        'OPENAI_API_KEY': 'OpenAI API key for AI features',
        'SENDGRID_API_KEY': 'SendGrid API key for email services',
        'TWILIO_ACCOUNT_SID': 'Twilio Account SID for SMS',
        'TWILIO_AUTH_TOKEN': 'Twilio Auth Token for SMS',
        'TWILIO_PHONE_NUMBER': 'Twilio phone number for SMS',
        'RENDER': 'Render environment flag',
        'PORT': 'Port number for the application'
    }
    
    optional_vars = {
        'RENDER_API_KEY': 'Render API key for deployment management',
        'REPL_ID': 'Replit ID (development only)',
        'REPL_SLUG': 'Replit slug (development only)'
    }
    
    print("🔍 Environment Variables Check")
    print("=" * 50)
    
    print("\nREQUIRED VARIABLES:")
    print("-" * 30)
    missing_required = []
    
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Show partial value for security
            if 'KEY' in var or 'SECRET' in var or 'TOKEN' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            elif var == 'DATABASE_URL':
                display_value = f"postgresql://...{value[-10:]}" if 'postgresql' in value else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_required.append(var)
            print(f"   Description: {description}")
    
    print("\nOPTIONAL VARIABLES:")
    print("-" * 30)
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if value:
            if 'KEY' in var or 'SECRET' in var or 'TOKEN' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"⚪ {var}: Not set")
            print(f"   Description: {description}")
    
    print("\nSUMMARY:")
    print("-" * 30)
    if missing_required:
        print(f"❌ {len(missing_required)} required variables missing:")
        for var in missing_required:
            print(f"   - {var}")
        print("\nThese variables must be set in Render dashboard:")
        print("1. Go to https://dashboard.render.com")
        print("2. Select your Dear Teddy service")
        print("3. Go to Environment tab")
        print("4. Add the missing variables")
    else:
        print("✅ All required environment variables are set!")
    
    return len(missing_required) == 0

def check_render_specific_config():
    """Check Render-specific configuration"""
    print("\n🏗️  Render Configuration Check")
    print("=" * 50)
    
    # Check if running on Render
    is_render = os.environ.get('RENDER') == 'true'
    print(f"Render environment: {'✅ Yes' if is_render else '❌ No'}")
    
    # Check port configuration
    port = os.environ.get('PORT')
    if port:
        print(f"Port configuration: ✅ {port}")
    else:
        print("Port configuration: ❌ Not set (should be auto-set by Render)")
    
    # Check build command and start command hints
    print("\nRender Service Configuration:")
    print("Build Command should be: pip install -r requirements.txt")
    print("Start Command should be: gunicorn --bind 0.0.0.0:$PORT --reuse-port --reload main:app")
    print("Root Directory should be: / (or empty)")
    print("Environment should be: Python 3")
    
    return is_render

def test_database_connection():
    """Test database connection with current environment variables"""
    print("\n🗄️  Database Connection Test")
    print("=" * 50)
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set - cannot test connection")
        return False
    
    try:
        import psycopg2
        
        # Test basic connection
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print("✅ Database connection successful")
        print(f"PostgreSQL version: {version[0].split()[0]} {version[0].split()[1]}")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Dear Teddy - Production Environment Check")
    print("=" * 60)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Check Render configuration
    render_ok = check_render_specific_config()
    
    # Test database connection
    db_ok = test_database_connection()
    
    print("\n🎯 FINAL STATUS")
    print("=" * 50)
    if env_ok and render_ok and db_ok:
        print("✅ Environment is properly configured for production")
    else:
        print("❌ Environment configuration issues detected")
        print("\nNext steps:")
        if not env_ok:
            print("1. Set missing environment variables in Render dashboard")
        if not render_ok:
            print("2. Verify Render service configuration")
        if not db_ok:
            print("3. Check database connection and credentials")
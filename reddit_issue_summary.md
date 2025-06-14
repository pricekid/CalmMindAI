# Production Site 500 Errors - Dear Teddy Flask App

## Problem Summary
My Flask application works perfectly in development but returns 500 errors for all authentication endpoints in production at www.dearteddy.app.

## What Works
- ✅ Main site loads (200 status) 
- ✅ Static assets serve correctly
- ✅ Development environment works flawlessly
- ✅ Database connection established
- ✅ All environment variables configured

## What's Broken (500 Errors)
- ❌ `/register` endpoint
- ❌ `/login` and `/stable-login` endpoints  
- ❌ `/health` endpoint
- ❌ All dynamic Flask routes

## Technical Details

**Environment:**
- Python 3.11
- Flask 2.3.3 with Flask-Login, Flask-SQLAlchemy
- PostgreSQL database
- Deployed on Render.com (likely)
- Gunicorn WSGI server

**Error Pattern:**
```
Registration status: 500
Login status: 500  
Health endpoint status: 500
```

**Development vs Production:**
- Development: All endpoints return 200/302 (working)
- Production: Static content works, dynamic routes fail with 500

**Environment Variables (Confirmed Present):**
- DATABASE_URL ✅
- SESSION_SECRET ✅  
- OPENAI_API_KEY ✅
- SENDGRID_API_KEY ✅
- TWILIO credentials ✅

## Code Structure
Main Flask app uses:
- SQLAlchemy with DeclarativeBase
- Flask-Login for authentication
- PostgreSQL with proper connection pooling
- Werkzeug password hashing

## What I've Tried
1. Created streamlined production WSGI app
2. Verified all dependencies in requirements.txt
3. Updated Procfile configuration
4. Tested database connectivity (works in dev)
5. Confirmed environment variables exist

## Deployment Files Created
- `wsgi.py` - Production WSGI application
- `Procfile` - Gunicorn configuration  
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version

## Questions for Reddit
1. **What could cause Flask routes to return 500 in production when they work in development?**
2. **Are there common Render.com/deployment platform issues with Flask-Login?**
3. **How can I debug 500 errors when I can't access server logs directly?**
4. **Could this be a WSGI application object issue?**

## Specific Help Needed
- Debugging strategies for production 500 errors
- Common Flask deployment gotchas
- How to identify if it's a dependency, configuration, or code issue
- Best practices for Flask production deployment

The frustrating part is that everything works perfectly locally, but production fails silently with generic 500 errors across all dynamic endpoints.

---
*Posted to r/flask, r/webdev - looking for production deployment debugging advice*
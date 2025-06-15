# Flask App Deployment Guide: Replit to Render.com

## Overview
This guide provides step-by-step instructions to deploy your Flask app from Replit to Render.com successfully.

## Files Created for Deployment

### 1. `wsgi.py` - WSGI Entry Point
- Provides the `application` object that gunicorn expects
- Handles import fallbacks to ensure deployment works
- Compatible with Render.com's requirements

### 2. `Procfile` - Process Configuration
```
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --log-level info
```

### 3. `render.yaml` - Render Service Configuration
- Defines web service configuration
- Sets up database connection
- Configures environment variables

### 4. `runtime.txt` - Python Version
```
python-3.11.11
```

### 5. `requirements.txt` - Dependencies
All necessary Python packages including gunicorn for production.

## Deployment Steps

### Option 1: Direct GitHub Deployment (Recommended)

1. **Push to GitHub**:
   - Commit all files to your GitHub repository
   - Ensure `wsgi.py`, `Procfile`, `render.yaml`, and `runtime.txt` are included

2. **Connect to Render**:
   - Go to [render.com](https://render.com) and sign in
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository (CalmMindAI)

3. **Configure Service**:
   - **Name**: dear-teddy (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --log-level info`

4. **Set Environment Variables**:
   - `SESSION_SECRET`: Generate a secure random string
   - `DATABASE_URL`: Will be auto-configured if using Render PostgreSQL

5. **Deploy**: Click "Create Web Service"

### Option 2: Using render.yaml (Infrastructure as Code)

1. **Automatic Setup**:
   - The `render.yaml` file will automatically configure:
     - Web service
     - PostgreSQL database
     - Environment variables
     - Health checks

2. **Deploy**:
   - Push to GitHub with `render.yaml` included
   - Render will automatically detect and deploy the configuration

### Option 3: Manual Configuration

1. **Create Web Service Manually**:
   - Runtime: Python 3.11.11
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

2. **Add Database** (if needed):
   - Create PostgreSQL database
   - Copy connection string to `DATABASE_URL` environment variable

## Environment Variables Required

- `SESSION_SECRET`: Secure random string for Flask sessions
- `DATABASE_URL`: PostgreSQL connection string (auto-configured with Render PostgreSQL)
- `PORT`: Automatically set by Render

## Health Check Endpoint

Your app includes a `/health` endpoint that Render uses to verify the service is running:
```
GET /health
Response: {"status": "healthy", "timestamp": "..."}
```

## Common Issues and Solutions

### 1. Gunicorn Import Errors
- **Fixed**: `wsgi.py` handles import fallbacks
- **Solution**: Uses `wsgi:application` instead of `main:app`

### 2. SQLAlchemy Model Conflicts
- **Fixed**: `production.py` uses unique model names
- **Solution**: Isolated database models prevent conflicts

### 3. Session Secret Issues
- **Fixed**: Proper environment variable handling
- **Solution**: Session error handling in the app

### 4. Port Binding Issues
- **Fixed**: Uses `0.0.0.0:$PORT` binding
- **Solution**: Compatible with Render's port assignment

## Verification Steps

After deployment:

1. **Check Health**: Visit `https://your-app.onrender.com/health`
2. **Test Registration**: Try creating a new account
3. **Test Login**: Verify authentication works
4. **Check Logs**: Monitor Render dashboard for any errors

## Local Testing

Before deploying, test the WSGI setup locally:

```bash
# Install gunicorn locally
pip install gunicorn

# Test the WSGI configuration
gunicorn wsgi:application --bind 0.0.0.0:5000

# Visit http://localhost:5000 to verify
```

## Support

If deployment fails:
1. Check Render build logs for specific errors
2. Verify all required files are in the repository
3. Ensure environment variables are properly set
4. Check the health endpoint after deployment

The deployment configuration is now optimized for Render.com and should deploy successfully without the gunicorn errors you experienced previously.
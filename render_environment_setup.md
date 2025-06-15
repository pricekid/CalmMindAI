# Render Environment Variables Setup

## Required Environment Variables for Production

Set these in your Render dashboard under the Environment tab:

### Core Application Variables
- `RENDER=true` - Enables production mode and Render-specific configurations
- `SESSION_SECRET` - ✅ Already set
- `DATABASE_URL` - ✅ Already set (auto-configured by Render)

### API Keys (Already Configured)
- `OPENAI_API_KEY` - ✅ Already set
- `SENDGRID_API_KEY` - ✅ Already set  
- `TWILIO_ACCOUNT_SID` - ✅ Already set
- `TWILIO_AUTH_TOKEN` - ✅ Already set
- `TWILIO_PHONE_NUMBER` - ✅ Already set

### Missing Variables to Add
1. **RENDER** = `true`
   - This enables production-specific configurations
   - Critical for proper app initialization

2. **PORT** 
   - Should be auto-set by Render
   - If missing, Render will assign it automatically
   - Do not manually set unless instructed by Render support

## Render Service Configuration

### Build Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --reuse-port --reload main:app`
- **Python Version**: 3.11 or higher

### Deployment Settings
- **Root Directory**: Leave empty (uses repository root)
- **Auto-Deploy**: Enable for automatic deployments

## Next Steps
1. Add the missing RENDER environment variable
2. Redeploy the service
3. Test login functionality with existing credentials
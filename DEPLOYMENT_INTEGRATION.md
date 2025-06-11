# Dear Teddy - Marketing Site Integration Guide

## Overview
This guide explains how to properly integrate the dearteddy.app marketing site with your Flask app deployed on render.com.

## Current Authentication Flow Status

### ✅ What's Working
- Flask app has stable authentication routes (`/stable-login`, `/register-simple`)
- Render.com compatibility settings are configured
- Marketing integration routes are now available
- CSRF protection is properly configured for render.com

### 🔧 What Needs Configuration

#### 1. Marketing Site Button URLs
Update the dearteddy.app marketing site buttons to use these URLs:

**Login Button:**
```
https://YOUR-RENDER-APP.onrender.com/marketing-login
```

**Sign Up Button:**
```
https://YOUR-RENDER-APP.onrender.com/marketing-signup
```

**Get Started Button:**
```
https://YOUR-RENDER-APP.onrender.com/from-marketing?action=get-started
```

#### 2. Environment Variables for Render.com
Set these environment variables in your Render.com dashboard:

```
RENDER=true
RENDER_APP_URL=https://YOUR-RENDER-APP.onrender.com
SESSION_SECRET=your-secret-key-here
DATABASE_URL=your-postgresql-url-here
OPENAI_API_KEY=your-openai-key-here
SENDGRID_API_KEY=your-sendgrid-key-here
```

## Authentication Flow

### User Journey from Marketing Site
1. User visits dearteddy.app
2. User clicks "Login" or "Sign Up"
3. User is redirected to your render.com Flask app
4. User completes authentication
5. User is redirected to dashboard
6. Session tracks that user came from marketing site

### Available Routes
- `/marketing-login` - Direct login for marketing users
- `/marketing-signup` - Direct signup for marketing users  
- `/from-marketing` - Handles various marketing actions
- `/app-redirect` - Generic redirect handler

## Testing the Integration

### 1. Test Direct URLs
Visit these URLs to verify they work:
- `https://YOUR-RENDER-APP.onrender.com/marketing-login`
- `https://YOUR-RENDER-APP.onrender.com/marketing-signup`

### 2. Test Authentication Flow
1. Go to marketing login URL
2. Complete login process
3. Verify redirect to dashboard
4. Check that session contains marketing source

### 3. Verify CSRF Protection
- Login should work without CSRF errors
- Forms should submit successfully
- Session cookies should persist

## Render.com Deployment Checklist

### ✅ Files Ready for Deployment
- `Procfile` - Gunicorn configuration
- `build.sh` - Build script with database setup
- `requirements.txt` - Python dependencies
- `marketing_integration.py` - Marketing site integration
- `render_compatibility.py` - Render-specific settings

### ✅ Database Setup
- PostgreSQL database configured
- Database initialization script ready
- User creation scripts available

### ✅ Static Assets
- CSS with 3D card styling
- JavaScript for PWA functionality
- Audio directory for TTS features

## Security Considerations

### CSRF Protection
- Configured for render.com proxy setup
- Extended token lifetime for better UX
- SSL strict checking disabled for render.com

### Session Security
- Secure cookies enabled for HTTPS
- HttpOnly cookies for XSS protection
- SameSite=None for cross-site functionality

### Environment Variables
- All sensitive data in environment variables
- No hardcoded secrets in code
- Proper secret key rotation support

## Monitoring and Analytics

### Marketing Source Tracking
The integration tracks users from marketing site:
```python
session['marketing_source'] = 'direct_login'  # or 'direct_signup'
session['marketing_action'] = 'login'  # or 'signup', 'get-started'
```

### Logging
- All marketing redirects are logged
- Authentication attempts tracked
- Error conditions monitored

## Next Steps

1. **Deploy to Render.com** using the configured files
2. **Update dearteddy.app** with the correct redirect URLs
3. **Test the complete flow** from marketing site to app
4. **Monitor logs** for any integration issues
5. **Set up analytics** to track conversion from marketing site

## Troubleshooting

### Common Issues
- **CSRF errors**: Check render.com environment variables
- **Session loss**: Verify cookie settings for HTTPS
- **Redirect loops**: Ensure correct URL configuration
- **Database errors**: Check PostgreSQL connection string

### Debug Routes
- `/from-marketing?debug=true` - Shows debug information
- Check application logs in Render.com dashboard
- Monitor session data in browser dev tools
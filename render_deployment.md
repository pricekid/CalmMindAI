# Deploying Dear Teddy on Render.com

This guide walks through the process of deploying the Dear Teddy application on Render.com.

## Prerequisites

Before deployment, ensure you have:

1. A Render.com account
2. Access to the Dear Teddy GitHub repository
3. Required environment variables:
   - `DATABASE_URL` - PostgreSQL database connection string
   - `SESSION_SECRET` - Secret key for session management
   - `OPENAI_API_KEY` - API key for OpenAI services
   - `SENDGRID_API_KEY` - API key for SendGrid email services (if using)
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` - Twilio credentials (if using)

## Deployment Steps

### Option 1: Using the Dashboard

1. Log in to your Render.com account and navigate to the Dashboard
2. Click "New" and select "Web Service"
3. Connect to your GitHub repository
4. Configure the service with these settings:
   - **Name**: dear-teddy (or your preferred name)
   - **Environment**: Python
   - **Region**: Choose the region closest to your users
   - **Branch**: main (or your deployment branch)
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers=2 --threads=4 --timeout=120 main:app`
   - **Health Check Path**: `/r-login`
   - **Plan**: Starter (or as needed)

5. Add these environment variables:
   - `RENDER`: `true`
   - `PYTHON_VERSION`: `3.11.0`
   - `DATABASE_URL`: Your database URL
   - `SESSION_SECRET`: Generate a secure random string
   - `OPENAI_API_KEY`: Your OpenAI API key
   - Add any other required API keys (SendGrid, Twilio, etc.)

6. Click "Create Web Service"

### Option 2: Using render.yaml (Recommended)

1. Ensure the `render.yaml` file is in your repository
2. Log in to your Render.com account
3. Click "New" and select "Blueprint"
4. Connect to your GitHub repository
5. Render will automatically detect the `render.yaml` file and configure services
6. Update any environment variables that couldn't be set automatically
7. Click "Apply" to start the deployment

## Troubleshooting

### Login Issues
- The application includes a special Render-compatible login system at `/r-login`
- The environment variable `RENDER=true` must be set to activate this system
- Check the logs for "Using Render-optimized login" message to confirm it's active

### Database Connection Issues
- Confirm your `DATABASE_URL` is correctly formatted for PostgreSQL
- Ensure your IP address is allowed in any database firewall settings
- Check that the database exists and has the correct schema

### Static Files Not Loading
- Static files are served from the `/static` directory
- Check your browser console for 404 errors on specific files
- Ensure the `buildCommand` is creating all necessary directories

## Monitoring Deployment

1. After deployment starts, monitor the build logs for errors
2. Once deployed, navigate to the health check path (`/r-login`) to verify the application is running
3. Check the runtime logs for any ongoing issues

If you encounter persistent errors, please check the application logs in the Render dashboard and update environment variables as needed.
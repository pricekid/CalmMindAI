# Dear Teddy - Mental Wellness App

An AI-powered mental wellness journaling application that provides comprehensive user support through intelligent authentication and personalized emotional tracking.

## Deployment Guide for Render.com

### Prerequisites
- A Render.com account
- PostgreSQL database (you can create one on Render.com)
- Required API keys:
  - OpenAI API key
  - SendGrid API key (for email notifications)
  - Twilio credentials (for SMS reminders)

### Steps to Deploy

1. Fork or clone this repository to your GitHub account
2. Create a new Web Service on Render.com
3. Connect your GitHub repository
4. Configure the following settings:
   - Build Command: `poetry install`
   - Start Command: `poetry run gunicorn --bind 0.0.0.0:$PORT main:app`

5. Add the following environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SESSION_SECRET`: A secure random string for session encryption
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SENDGRID_API_KEY`: Your SendGrid API key
   - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER`: Your Twilio Phone Number

6. Deploy the application

### Using render.yaml (Recommended)

This repository includes a `render.yaml` file for easy deployment:

1. Fork or clone this repository to your GitHub account
2. In your Render.com dashboard, click "New" and select "Blueprint"
3. Connect your GitHub repository
4. Render will detect the `render.yaml` file and set up the services
5. Fill in the required environment variables
6. Deploy the blueprint

## Local Development

1. Clone the repository
2. Install dependencies with Poetry: `poetry install`
3. Set up environment variables (see deployment section)
4. Run the application: `poetry run python main.py`

## Troubleshooting Deployment

If you encounter issues with deployment, try these steps:

1. **Database Connection Issues**: 
   - Verify your `DATABASE_URL` is correct
   - Ensure your database is accessible from Render.com's IP addresses

2. **Poetry Installation Problems**: 
   - Check if your `pyproject.toml` file is at the root of the repository
   - Verify that all dependencies are correctly listed

3. **Application Startup Errors**:
   - Check the Render.com logs for specific error messages
   - Make sure all required environment variables are set

4. **API Key Issues**:
   - Ensure all API keys (OpenAI, SendGrid, Twilio) are valid
   - Check for any API usage limitations or restrictions

## Features

- Mental wellness journaling with AI insights
- Secure user authentication
- Personalized emotional tracking
- Progressive Web App (PWA) installation
- Mobile-friendly responsive design
- Crisis resource integration
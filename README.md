# Dear Teddy

Dear Teddy is an AI-powered mental wellness journaling application that provides comprehensive user support through intelligent authentication and personalized user experiences, focusing on mental health tracking and user engagement.

## Features

- **Progressive Web App (PWA)** - Install on desktop or mobile for an app-like experience
- **Secure User Authentication** - Multiple login strategies with enhanced security
- **AI-Assisted Journaling** - Get insights and CBT recommendations for your journal entries
- **Mood Tracking** - Monitor your emotional well-being over time
- **Push Notifications** - Receive timely reminders for journaling and mood tracking
- **Achievements System** - Earn badges and track your progress
- **Responsive Design** - Beautiful interface that works on all devices

## Technical Components

- **Python Flask Backend** - Robust server-side implementation
- **PostgreSQL Database** - Reliable data storage
- **Web Push Notifications** - Real-time user engagement
- **OpenAI Integration** - Intelligent journal analysis
- **Sendgrid Email Integration** - Reliable email delivery
- **Twilio SMS Integration** - Text message notifications

## Setup Instructions

### Basic Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (see below)
4. Run the application: `python main.py`

### Environment Variables

Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://...
SESSION_SECRET=your_session_secret
OPENAI_API_KEY=your_openai_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
```

### Push Notification Setup

To enable push notifications, you need to generate VAPID keys:

1. Run the key generation script: `python generate_vapid_keys.py`
2. Add the generated keys to your environment variables:
   ```
   VAPID_PUBLIC_KEY=your_generated_public_key
   VAPID_PRIVATE_KEY=your_generated_private_key
   ```
3. Restart the application for the changes to take effect

## Usage

1. Create an account or log in
2. Enable push notifications for timely reminders
3. Start journaling to track your thoughts and feelings
4. Use the mood tracker to monitor your emotional well-being
5. Earn achievements as you maintain your journaling habit

## Development Guidelines

- Use `git flow` for feature development
- Follow PEP 8 for Python code style
- Write unit tests for all new features
- Keep dependencies updated for security
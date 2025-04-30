# Notification Setup Guide

## Current Status
- Email and SMS notifications are currently **disabled** because API keys are not configured
- The application will work normally without notifications
- Users can still receive responses in the app interface

## How to Enable Notifications

### For Email Notifications (SendGrid)
1. Obtain a SendGrid API Key from the SendGrid website
2. Add the API key to the Replit environment variables:
   - Name: `SENDGRID_API_KEY`
   - Value: Your SendGrid API key

### For SMS Notifications (Twilio)
1. Obtain Twilio credentials from the Twilio website
2. Add the following Twilio credentials to Replit environment variables:
   - `TWILIO_ACCOUNT_SID`: Your Twilio account SID
   - `TWILIO_AUTH_TOKEN`: Your Twilio auth token
   - `TWILIO_PHONE_NUMBER`: Your Twilio phone number (with country code)

## Testing Notifications
After adding the API keys, you can test notifications using:

1. For email: `python send_test_email_now.py`
2. For SMS: `python send_immediate_sms.py`

## Scheduled Notifications
Scheduled notifications will automatically begin working once the API keys are added. The system will:

1. Check for valid API keys at startup
2. Log notification status in the application logs
3. Use the API keys for scheduled notifications if available
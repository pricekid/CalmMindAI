#!/usr/bin/env python3
"""
Simple script to show which environment variables are set.
This helps you verify your secrets are configured.
"""
import os

# List of secrets we need for Render
required_secrets = [
    'OPENAI_API_KEY',
    'SENDGRID_API_KEY', 
    'TWILIO_ACCOUNT_SID',
    'TWILIO_AUTH_TOKEN',
    'TWILIO_PHONE_NUMBER',
    'DATABASE_URL'
]

print("🔍 Checking environment variables...")
print("=" * 50)

for secret in required_secrets:
    value = os.environ.get(secret)
    if value:
        # Show first 10 characters for verification
        masked_value = value[:10] + "..." if len(value) > 10 else value
        print(f"✅ {secret}: {masked_value}")
    else:
        print(f"❌ {secret}: NOT SET")

print("\n💡 Copy the full values from your Replit environment to Render")
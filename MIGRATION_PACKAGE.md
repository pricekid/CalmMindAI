# Dear Teddy - Complete Migration Package

## 1. Current Application State Summary

### Architecture Overview
- **Framework**: Python Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with comprehensive user and journal models
- **Authentication**: Replit OAuth integration with session management
- **AI Integration**: OpenAI GPT-4o for therapeutic conversations
- **External Services**: SendGrid (email), Twilio (SMS), Azure TTS (text-to-speech)
- **Frontend**: Server-side rendered templates with responsive design

### Core Features Implemented
1. **User Authentication & Onboarding**
   - Secure login/signup with Replit OAuth
   - Optional demographic collection for personalized AI responses
   - Age range, relationship status, children status, life focus areas

2. **AI-Powered Journaling**
   - Multi-turn conversations with "Mira" AI therapist
   - CBT-based therapeutic responses
   - Anxiety level tracking (1-10 scale)
   - Reflective pause feature for deeper engagement

3. **Mood Tracking & Analytics**
   - Daily mood logging system
   - Weekly trend analysis
   - Visual progress tracking
   - Pattern recognition algorithms

4. **Notification System**
   - Email reminders via SendGrid
   - SMS notifications through Twilio
   - Web push notifications
   - Customizable timing preferences

5. **Text-to-Speech Integration**
   - Azure Cognitive Services TTS
   - Multiple premium neural voices
   - SSML support for natural speech

6. **Administrative Dashboard**
   - User management and analytics
   - Content moderation tools
   - API configuration management
   - System health monitoring

### Current Infrastructure Issue
- **Problem**: Replit infrastructure caching layer serving old error pages
- **Evidence**: Server logs show successful route execution while browsers receive cached responses
- **Status**: Support ticket submitted, awaiting resolution
- **Workaround**: Stable app version created for alternative deployment

## 2. Database Schema Export

### Core Tables Structure

```sql
-- Users table with demographics and preferences
CREATE TABLE "user" (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(64) UNIQUE,
    email VARCHAR(120) UNIQUE,
    password_hash VARCHAR(256),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Replit Auth profile data
    first_name VARCHAR(64),
    last_name VARCHAR(64),
    profile_image_url VARCHAR(256),
    
    -- Notification preferences
    notifications_enabled BOOLEAN DEFAULT TRUE,
    notification_time TIME DEFAULT '09:00:00',
    morning_reminder_enabled BOOLEAN DEFAULT TRUE,
    morning_reminder_time TIME DEFAULT '08:00:00',
    evening_reminder_enabled BOOLEAN DEFAULT TRUE,
    evening_reminder_time TIME DEFAULT '20:00:00',
    
    -- SMS settings
    phone_number VARCHAR(20),
    sms_notifications_enabled BOOLEAN DEFAULT FALSE,
    
    -- UI state
    welcome_message_shown BOOLEAN DEFAULT FALSE,
    
    -- Demographics for AI personalization
    age_range VARCHAR(20),
    relationship_status VARCHAR(50),
    has_children BOOLEAN,
    life_focus TEXT -- JSON string for multi-select
);

-- Journal entries with conversation tracking
CREATE TABLE journal_entry (
    id SERIAL PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_analyzed BOOLEAN DEFAULT FALSE,
    anxiety_level INTEGER, -- 1-10 scale
    
    -- Multi-turn conversation fields
    initial_insight TEXT,
    user_reflection TEXT,
    followup_insight TEXT,
    second_reflection TEXT,
    closing_message TEXT,
    conversation_complete BOOLEAN DEFAULT FALSE,
    
    -- Foreign key
    user_id VARCHAR REFERENCES "user"(id) NOT NULL
);

-- CBT recommendations
CREATE TABLE cbt_recommendation (
    id SERIAL PRIMARY KEY,
    thought_pattern VARCHAR(255) NOT NULL,
    recommendation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    journal_entry_id INTEGER REFERENCES journal_entry(id) NOT NULL
);

-- Mood tracking
CREATE TABLE mood_log (
    id SERIAL PRIMARY KEY,
    mood_score INTEGER NOT NULL, -- 1-10 scale
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR REFERENCES "user"(id) NOT NULL
);

-- OAuth tokens for Replit Auth
CREATE TABLE flask_dance_oauth (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(256),
    token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR REFERENCES "user"(id),
    browser_session_key VARCHAR NOT NULL,
    
    CONSTRAINT uq_user_browser_session_key_provider 
    UNIQUE (user_id, browser_session_key, provider)
);

-- Push notification subscriptions
CREATE TABLE push_subscription (
    id SERIAL PRIMARY KEY,
    subscription_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_notification_at TIMESTAMP,
    
    -- Notification preferences
    journal_reminders BOOLEAN DEFAULT TRUE,
    mood_reminders BOOLEAN DEFAULT TRUE,
    feature_updates BOOLEAN DEFAULT TRUE,
    
    user_id VARCHAR REFERENCES "user"(id) NOT NULL
);

-- Admin users
CREATE TABLE admin (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Sample Data Relationships
```sql
-- Example user with complete profile
INSERT INTO "user" (email, age_range, relationship_status, has_children, life_focus) 
VALUES ('user@example.com', '25-34', 'married', true, 'family');

-- Example journal entry with AI conversation
INSERT INTO journal_entry (user_id, title, content, anxiety_level, initial_insight, user_reflection, followup_insight) 
VALUES ('user-id', 'Work Stress', 'Feeling overwhelmed at work...', 7, 'I notice you''re experiencing...', 'That helps me understand...', 'Building on your insight...');
```

## 3. Deployment Requirements & Configuration

### Environment Variables Required
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Authentication
SESSION_SECRET=your-secret-key-here
REPL_ID=your-repl-id (for Replit OAuth)

# AI Services
OPENAI_API_KEY=your-openai-api-key

# Email Notifications
SENDGRID_API_KEY=your-sendgrid-api-key

# SMS Notifications
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number

# Text-to-Speech (Optional)
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=your-azure-region

# Database Connection Details (for manual setup)
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=password
PGDATABASE=dear_teddy
```

### Python Dependencies (requirements.txt)
```txt
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-WTF==1.1.1
WTForms==3.0.1
Flask-Dance==7.0.0
python-dotenv==1.0.0
gunicorn==21.2.0
psycopg2-binary==2.9.7
openai==1.3.0
sendgrid==6.10.0
twilio==8.5.0
azure-cognitiveservices-speech==1.32.0
requests==2.31.0
Werkzeug==2.3.7
```

### System Dependencies
```bash
# Ubuntu/Debian
apt-get update
apt-get install -y python3 python3-pip postgresql-client

# For audio processing (if using TTS)
apt-get install -y ffmpeg

# For SSL certificates
apt-get install -y ca-certificates
```

### Deployment Configurations

#### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create audio directory for TTS
RUN mkdir -p static/audio

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

#### Heroku Configuration (Procfile)
```
web: gunicorn main:app --bind 0.0.0.0:$PORT --workers 4
release: python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### Railway Configuration (railway.toml)
```toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "always"
```

### Database Migration Scripts
```python
# migrations/create_tables.py
from app import app, db
import models

def create_all_tables():
    with app.app_context():
        db.create_all()
        print("All tables created successfully")

if __name__ == "__main__":
    create_all_tables()
```

### Health Check Endpoint
```python
@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
```

### Security Considerations
1. **CSRF Protection**: Flask-WTF with token validation
2. **Password Security**: Werkzeug password hashing
3. **Session Security**: Secure session configuration
4. **SQL Injection Prevention**: SQLAlchemy ORM usage
5. **Input Validation**: WTForms validators
6. **Environment Variables**: Sensitive data in env vars, not code

### Performance Optimizations
1. **Database Connection Pooling**: SQLAlchemy engine options
2. **Query Optimization**: Lazy loading and selective queries
3. **Caching Headers**: No-cache for dynamic content
4. **Static File Serving**: CDN-ready asset structure
5. **Database Indexing**: Proper indexes on foreign keys and frequently queried fields

### Monitoring & Logging
```python
# Configure logging for production
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/dear_teddy.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

## Alternative Deployment Platforms

### Recommended Services
1. **Railway**: Excellent for Flask apps, built-in PostgreSQL
2. **Render**: Free tier available, good for MVPs
3. **Heroku**: Established platform, many add-ons
4. **DigitalOcean App Platform**: Cost-effective, good performance
5. **AWS Elastic Beanstalk**: Scalable, enterprise-ready
6. **Google Cloud Run**: Serverless, pay-per-use

### Migration Checklist
- [ ] Set up new PostgreSQL database
- [ ] Configure environment variables
- [ ] Deploy application code
- [ ] Run database migrations
- [ ] Test authentication flow
- [ ] Verify external service integrations
- [ ] Set up monitoring and logging
- [ ] Configure custom domain (if needed)
- [ ] Test all core features
- [ ] Set up backup procedures

This migration package provides everything needed to deploy Dear Teddy on any modern cloud platform while maintaining all current functionality.
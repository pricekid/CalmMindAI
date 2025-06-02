# Dear Teddy - Deployment Requirements & Platform Setup

## Platform-Specific Deployment Guides

### 1. Railway Deployment

#### Setup Steps
1. **Create Railway Account** and connect GitHub repository
2. **Add Environment Variables** in Railway dashboard:
   ```
   DATABASE_URL=postgresql://postgres:password@database:5432/dear_teddy
   SESSION_SECRET=your-session-secret-key
   OPENAI_API_KEY=your-openai-key
   SENDGRID_API_KEY=your-sendgrid-key
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   TWILIO_PHONE_NUMBER=your-twilio-number
   ```
3. **Add PostgreSQL Plugin** from Railway marketplace
4. **Deploy** using Railway's automatic deployment

#### railway.toml Configuration
```toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "always"

[[services]]
name = "web"
source = "."

[services.web.env]
PORT = { default = "5000" }
```

#### Procfile for Railway
```
web: gunicorn main:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
```

### 2. Render Deployment

#### Setup Steps
1. **Create Render Account** and connect repository
2. **Create Web Service** with these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT`
   - **Environment**: Python 3.11
3. **Add PostgreSQL Database** from Render dashboard
4. **Configure Environment Variables** in service settings

#### render.yaml Configuration
```yaml
services:
  - type: web
    name: dear-teddy
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn main:app --bind 0.0.0.0:$PORT --workers 4
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: dear-teddy-db
          property: connectionString
      - key: SESSION_SECRET
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.11.0

  - type: pserv
    name: dear-teddy-db
    env: postgresql
    plan: free
```

### 3. Heroku Deployment

#### Setup Steps
1. **Install Heroku CLI** and login
2. **Create Heroku App**: `heroku create dear-teddy-app`
3. **Add PostgreSQL**: `heroku addons:create heroku-postgresql:mini`
4. **Set Environment Variables**:
   ```bash
   heroku config:set SESSION_SECRET=your-secret
   heroku config:set OPENAI_API_KEY=your-key
   heroku config:set SENDGRID_API_KEY=your-key
   ```
5. **Deploy**: `git push heroku main`

#### Procfile for Heroku
```
web: gunicorn main:app --bind 0.0.0.0:$PORT --workers 4
release: python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### runtime.txt for Heroku
```
python-3.11.7
```

### 4. DigitalOcean App Platform

#### Setup Steps
1. **Create DigitalOcean Account** and access App Platform
2. **Connect GitHub Repository**
3. **Configure Build Settings**:
   - **Source Directory**: `/`
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn main:app --bind 0.0.0.0:$PORT`
4. **Add Managed Database** (PostgreSQL)
5. **Set Environment Variables** in app settings

#### .do/app.yaml Configuration
```yaml
name: dear-teddy
services:
- name: web
  source_dir: /
  github:
    repo: your-username/dear-teddy
    branch: main
  run_command: gunicorn main:app --bind 0.0.0.0:$PORT --workers 4
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  env:
  - key: SESSION_SECRET
    value: your-session-secret
  - key: DATABASE_URL
    value: ${dear-teddy-db.DATABASE_URL}

databases:
- name: dear-teddy-db
  engine: PG
  version: "13"
  size: db-s-dev-database
```

### 5. Google Cloud Run

#### Setup Steps
1. **Install Google Cloud CLI** and authenticate
2. **Create Project**: `gcloud projects create dear-teddy-app`
3. **Enable Services**:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   ```
4. **Create Cloud SQL Instance**:
   ```bash
   gcloud sql instances create dear-teddy-db --database-version=POSTGRES_13 --tier=db-f1-micro --region=us-central1
   ```
5. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy dear-teddy --source . --platform managed --region us-central1
   ```

#### Dockerfile for Cloud Run
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 4 --timeout 0 main:app
```

### 6. AWS Elastic Beanstalk

#### Setup Steps
1. **Install EB CLI**: `pip install awsebcli`
2. **Initialize**: `eb init dear-teddy`
3. **Create Environment**: `eb create production`
4. **Add RDS Database** through AWS Console
5. **Configure Environment Variables** in EB Console
6. **Deploy**: `eb deploy`

#### .ebextensions/01_packages.config
```yaml
packages:
  yum:
    postgresql-devel: []
```

#### .ebextensions/02_python.config
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: main:app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/opt/python/current/app:$PYTHONPATH"
```

## Required Environment Variables

### Core Application Variables
```bash
# Database connection
DATABASE_URL=postgresql://user:pass@host:port/database

# Session security
SESSION_SECRET=your-secure-random-string-here

# External service APIs
OPENAI_API_KEY=sk-your-openai-api-key
SENDGRID_API_KEY=SG.your-sendgrid-api-key
TWILIO_ACCOUNT_SID=ACyour-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Optional services
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=your-azure-region

# Platform-specific (if needed)
PORT=5000
REPL_ID=your-repl-id (for Replit OAuth)
```

### Environment Variable Security
- Use platform's secret management for sensitive values
- Never commit API keys to version control
- Rotate keys regularly for production deployments
- Use different keys for staging and production

## Database Setup Scripts

### Initial Database Creation
```python
# setup_database.py
import os
from app import app, db
import models

def setup_database():
    """Create all database tables and initial data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Create default admin user if needed
        from models import Admin
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin')
            admin.set_password('change_me_in_production')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin user created")
        
        print("🎉 Database setup complete!")

if __name__ == "__main__":
    setup_database()
```

### Database Migration Script
```python
# migrate_database.py
from app import app, db
from sqlalchemy import text

def run_migrations():
    """Run any necessary database migrations"""
    with app.app_context():
        try:
            # Add any new columns or tables here
            migrations = [
                # Example migration
                """
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS demographics_completed BOOLEAN DEFAULT FALSE;
                """
            ]
            
            for migration in migrations:
                db.session.execute(text(migration))
            
            db.session.commit()
            print("✅ Database migrations completed")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    run_migrations()
```

## Health Check Implementations

### Basic Health Check
```python
@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, 200
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 500
```

### Comprehensive Health Check
```python
@app.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with service status"""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        db.session.execute(text('SELECT 1'))
        status["services"]["database"] = "connected"
    except Exception as e:
        status["services"]["database"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    # Check OpenAI API
    try:
        if os.environ.get('OPENAI_API_KEY'):
            status["services"]["openai"] = "configured"
        else:
            status["services"]["openai"] = "not_configured"
    except Exception:
        status["services"]["openai"] = "error"
    
    # Check SendGrid
    try:
        if os.environ.get('SENDGRID_API_KEY'):
            status["services"]["sendgrid"] = "configured"
        else:
            status["services"]["sendgrid"] = "not_configured"
    except Exception:
        status["services"]["sendgrid"] = "error"
    
    return status, 200 if status["status"] == "healthy" else 500
```

## Performance Optimization

### Database Optimization
```python
# Database connection pooling
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 10,
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 20,
    "max_overflow": 20
}

# Query optimization
class User(db.Model):
    # Add indexes for frequently queried columns
    __table_args__ = (
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_created_at', 'created_at'),
    )
```

### Caching Strategy
```python
# Static file caching
@app.after_request
def add_cache_headers(response):
    if request.endpoint and request.endpoint.startswith('static'):
        response.cache_control.max_age = 31536000  # 1 year for static files
    else:
        response.cache_control.no_cache = True
    return response
```

## Monitoring and Logging

### Production Logging Configuration
```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Configure logging for production"""
    if not app.debug and not app.testing:
        # File logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/dear_teddy.log', 
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Dear Teddy application startup')
```

### Error Tracking
```python
@app.errorhandler(500)
def internal_error(error):
    """Log internal server errors"""
    app.logger.error(f'Server Error: {error}', exc_info=True)
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404
```

## Security Configuration

### Production Security Settings
```python
# CSRF protection
csrf = CSRFProtect(app)
csrf.init_app(app)

# Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,  # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,  # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

This deployment guide provides comprehensive instructions for deploying Dear Teddy on major cloud platforms while maintaining security, performance, and reliability standards.
"""
Production Configuration and Deployment Optimization
Centralizes all production settings, optimizations, and monitoring
"""

import os
import logging
from datetime import timedelta

class ProductionConfig:
    """Production configuration with security and performance optimizations"""
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours for better UX
    WTF_CSRF_SSL_STRICT = False  # Disabled for Render.com compatibility
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_timeout': 20,
        'max_overflow': 20
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Mail Configuration
    MAIL_SERVER = 'smtp.sendgrid.net'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'apikey'
    MAIL_PASSWORD = os.environ.get('SENDGRID_API_KEY')
    MAIL_DEFAULT_SENDER = 'noreply@dearteddy.app'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Logging Configuration
    LOG_LEVEL = logging.INFO
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Cache Configuration
    CACHE_TYPE = 'redis' if os.environ.get('REDIS_URL') else 'simple'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4o'
    OPENAI_MAX_TOKENS = 800
    
    # Feature Flags
    ENABLE_RATE_LIMITING = True
    ENABLE_SECURITY_MONITORING = True
    ENABLE_PERFORMANCE_MONITORING = True
    ENABLE_ERROR_REPORTING = True

class DevelopmentConfig(ProductionConfig):
    """Development configuration with debugging enabled"""
    
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False
    LOG_LEVEL = logging.DEBUG
    ENABLE_RATE_LIMITING = False

def get_config():
    """Return appropriate configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'production')
    
    if env == 'development':
        return DevelopmentConfig()
    else:
        return ProductionConfig()

def setup_logging():
    """Configure production logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=get_config().LOG_LEVEL,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log') if os.path.exists('.') else logging.StreamHandler()
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        'SESSION_SECRET',
        'DATABASE_URL',
        'OPENAI_API_KEY',
        'SENDGRID_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    logging.info("Environment validation passed")

def setup_production_optimizations(app):
    """Apply all production optimizations to the Flask app"""
    config = get_config()
    
    # Apply configuration
    app.config.from_object(config)
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
    
    # Performance monitoring
    if config.ENABLE_PERFORMANCE_MONITORING:
        setup_performance_monitoring(app)
    
    # Error reporting
    if config.ENABLE_ERROR_REPORTING:
        setup_error_reporting(app)
    
    logging.info("Production optimizations applied")

def setup_performance_monitoring(app):
    """Setup performance monitoring"""
    import time
    from flask import g, request
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            
            # Log slow requests
            if duration > 2.0:
                logging.warning(f"Slow request: {request.path} took {duration:.3f}s")
        
        return response

def setup_error_reporting(app):
    """Setup comprehensive error reporting"""
    import traceback
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log the full error
        logging.error(f"Unhandled exception: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        
        # Don't expose internal errors in production
        return "Internal server error", 500

def health_check_routes(app):
    """Add health check and monitoring routes"""
    
    @app.route('/health')
    def health():
        """Basic health check"""
        try:
            # Test database connection
            from extensions import db
            db.session.execute('SELECT 1')
            
            return {
                'status': 'healthy',
                'database': 'connected',
                'timestamp': time.time()
            }
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': 'Database connection failed'}, 500
    
    @app.route('/ready')
    def ready():
        """Readiness probe for container orchestration"""
        return {'status': 'ready', 'timestamp': time.time()}
    
    @app.route('/metrics')
    def metrics():
        """Application metrics"""
        import psutil
        
        return {
            'memory_percent': psutil.virtual_memory().percent,
            'cpu_percent': psutil.cpu_percent(interval=1),
            'timestamp': time.time()
        }

# Environment variable validation on import
if __name__ != "__main__":
    try:
        validate_environment()
    except ValueError as e:
        logging.warning(f"Environment validation failed: {e}")
        # Don't fail import in development
        pass
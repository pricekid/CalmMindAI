"""
Performance Optimization Module for Dear Teddy
Implements caching, database optimization, and response compression
"""

import os
import time
import logging
import gzip
from functools import wraps
from flask import Flask, request, g, Response
from flask_caching import Cache
import redis
from datetime import datetime, timedelta
import psutil

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Comprehensive performance optimization for the application"""
    
    def __init__(self, app):
        self.app = app
        self.cache = None
        self.setup_caching()
        self.setup_compression()
        self.setup_database_optimization()
        self.setup_monitoring()
    
    def setup_caching(self):
        """Configure Redis-based caching with fallback to simple cache"""
        try:
            # Try Redis first for production
            redis_url = os.environ.get('REDIS_URL')
            if redis_url:
                cache_config = {
                    'CACHE_TYPE': 'redis',
                    'CACHE_REDIS_URL': redis_url,
                    'CACHE_DEFAULT_TIMEOUT': 300
                }
            else:
                # Fallback to simple cache for development
                cache_config = {
                    'CACHE_TYPE': 'simple',
                    'CACHE_DEFAULT_TIMEOUT': 300
                }
            
            self.app.config.update(cache_config)
            self.cache = Cache(self.app)
            logger.info(f"Caching initialized: {cache_config['CACHE_TYPE']}")
            
        except Exception as e:
            logger.warning(f"Caching setup failed, continuing without cache: {e}")
            self.cache = None
    
    def setup_compression(self):
        """Enable gzip compression for responses"""
        @self.app.after_request
        def compress_response(response):
            # Only compress if client accepts gzip and response is large enough
            if (response.status_code == 200 and 
                'gzip' in request.headers.get('Accept-Encoding', '') and
                response.content_length and response.content_length > 1000):
                
                # Compress the response data
                compressed_data = gzip.compress(response.get_data())
                response.set_data(compressed_data)
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(compressed_data)
            
            return response
    
    def setup_database_optimization(self):
        """Configure database connection pooling and query optimization"""
        # Database connection pool settings already configured in app.py
        # Add query monitoring
        @self.app.before_request
        def log_slow_queries():
            g.start_time = time.time()
        
        @self.app.after_request
        def monitor_request_time(response):
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                if duration > 1.0:  # Log slow requests (>1 second)
                    logger.warning(f"Slow request: {request.endpoint} took {duration:.2f}s")
            return response
    
    def setup_monitoring(self):
        """Setup performance monitoring endpoints"""
        @self.app.route('/health')
        def health_check():
            """Health check endpoint for monitoring"""
            try:
                # Check database connectivity
                from extensions import db
                db.session.execute('SELECT 1')
                
                # Check memory usage
                memory_percent = psutil.virtual_memory().percent
                
                # Check cache status
                cache_status = "enabled" if self.cache else "disabled"
                
                return {
                    'status': 'healthy',
                    'database': 'connected',
                    'memory_usage': f"{memory_percent}%",
                    'cache': cache_status,
                    'timestamp': datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {'status': 'unhealthy', 'error': str(e)}, 500
        
        @self.app.route('/metrics')
        def performance_metrics():
            """Performance metrics endpoint"""
            try:
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=1)
                
                return {
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent
                    },
                    'cpu_percent': cpu,
                    'cache_status': 'enabled' if self.cache else 'disabled',
                    'timestamp': datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {'error': str(e)}, 500
    
    def cache_response(self, timeout=300, key_prefix='view'):
        """Decorator to cache view responses"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not self.cache:
                    return f(*args, **kwargs)
                
                # Generate cache key
                cache_key = f"{key_prefix}:{request.full_path}"
                
                # Try to get from cache
                cached_response = self.cache.get(cache_key)
                if cached_response:
                    return cached_response
                
                # Generate response and cache it
                response = f(*args, **kwargs)
                self.cache.set(cache_key, response, timeout=timeout)
                return response
            
            return decorated_function
        return decorator
    
    def cache_expensive_query(self, timeout=600):
        """Decorator to cache expensive database queries"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not self.cache:
                    return f(*args, **kwargs)
                
                # Generate cache key from function name and arguments
                cache_key = f"query:{f.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute query and cache result
                result = f(*args, **kwargs)
                self.cache.set(cache_key, result, timeout=timeout)
                return result
            
            return decorated_function
        return decorator
    
    def invalidate_cache(self, pattern=None):
        """Invalidate cache entries matching pattern"""
        if not self.cache:
            return
        
        if pattern:
            # This would require Redis for pattern matching
            logger.info(f"Cache invalidation requested for pattern: {pattern}")
        else:
            self.cache.clear()
            logger.info("All cache cleared")

def setup_performance_optimization(app):
    """Initialize performance optimization for the app"""
    optimizer = PerformanceOptimizer(app)
    return optimizer

# Utility functions for common optimizations
def optimize_database_queries():
    """Apply database query optimizations"""
    from extensions import db
    
    # Add database indexes for common queries
    sql_commands = [
        "CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_journal_user_id ON journal_entries(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_journal_created_at ON journal_entries(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_notification_user_id ON notification_log(user_id);",
    ]
    
    try:
        for sql in sql_commands:
            db.session.execute(sql)
        db.session.commit()
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")
        db.session.rollback()

def cleanup_old_data():
    """Clean up old data to maintain performance"""
    from extensions import db
    from models import NotificationLog
    from datetime import datetime, timedelta
    
    try:
        # Clean up old notification logs (older than 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_notifications = NotificationLog.query.filter(
            NotificationLog.sent_at < cutoff_date
        ).delete()
        
        db.session.commit()
        logger.info(f"Cleaned up {old_notifications} old notification records")
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        db.session.rollback()

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    optimizer = setup_performance_optimization(app)
    print("Performance optimization configured")
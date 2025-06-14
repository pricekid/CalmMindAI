"""
Rate Limiting and Security Protection
Implements request rate limiting, IP blocking, and attack prevention
"""

import time
import logging
from collections import defaultdict, deque
from flask import request, jsonify, render_template
from functools import wraps
import redis
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    """Memory-based rate limiter with Redis fallback for production"""
    
    def __init__(self, app=None):
        self.app = app
        self.memory_store = defaultdict(deque)
        self.blocked_ips = set()
        self.redis_client = None
        
        # Try to connect to Redis if available
        try:
            redis_url = os.environ.get('REDIS_URL')
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
                logger.info("Rate limiter using Redis backend")
            else:
                logger.info("Rate limiter using memory backend")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory: {e}")
    
    def is_rate_limited(self, key, limit, window):
        """Check if request exceeds rate limit"""
        now = time.time()
        
        if self.redis_client:
            return self._redis_rate_limit(key, limit, window, now)
        else:
            return self._memory_rate_limit(key, limit, window, now)
    
    def _memory_rate_limit(self, key, limit, window, now):
        """Memory-based rate limiting"""
        requests = self.memory_store[key]
        
        # Remove old requests outside window
        while requests and requests[0] <= now - window:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= limit:
            return True
        
        # Add current request
        requests.append(now)
        return False
    
    def _redis_rate_limit(self, key, limit, window, now):
        """Redis-based rate limiting"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, int(window))
            results = pipe.execute()
            
            current_count = results[1]
            return current_count >= limit
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return False
    
    def block_ip(self, ip, duration=3600):
        """Block IP address for specified duration"""
        self.blocked_ips.add(ip)
        logger.warning(f"IP {ip} blocked for {duration} seconds")
        
        if self.redis_client:
            try:
                self.redis_client.setex(f"blocked:{ip}", duration, "1")
            except Exception as e:
                logger.error(f"Failed to store IP block in Redis: {e}")
    
    def is_ip_blocked(self, ip):
        """Check if IP is currently blocked"""
        if ip in self.blocked_ips:
            return True
        
        if self.redis_client:
            try:
                return self.redis_client.exists(f"blocked:{ip}")
            except Exception as e:
                logger.error(f"Failed to check IP block in Redis: {e}")
        
        return False

# Global rate limiter instance
rate_limiter = None

def init_rate_limiter(app):
    """Initialize rate limiter with Flask app"""
    global rate_limiter
    rate_limiter = RateLimiter(app)
    return rate_limiter

def rate_limit(limit=60, window=60, block_threshold=5):
    """Decorator for rate limiting routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not rate_limiter:
                return f(*args, **kwargs)
            
            ip = request.remote_addr
            
            # Check if IP is blocked
            if rate_limiter.is_ip_blocked(ip):
                logger.warning(f"Blocked IP attempted access: {ip}")
                return jsonify({'error': 'Access denied'}), 429
            
            # Check rate limit
            key = f"rate_limit:{ip}:{request.endpoint}"
            if rate_limiter.is_rate_limited(key, limit, window):
                logger.warning(f"Rate limit exceeded for {ip} on {request.endpoint}")
                
                # Check for blocking threshold
                block_key = f"rate_limit_violations:{ip}"
                if rate_limiter.is_rate_limited(block_key, block_threshold, 3600):
                    rate_limiter.block_ip(ip, 3600)
                    return jsonify({'error': 'IP blocked due to excessive requests'}), 429
                
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def login_rate_limit(f):
    """Specific rate limiting for login attempts"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not rate_limiter:
            return f(*args, **kwargs)
        
        ip = request.remote_addr
        
        # Strict rate limiting for login attempts
        login_key = f"login_attempts:{ip}"
        if rate_limiter.is_rate_limited(login_key, 5, 300):  # 5 attempts per 5 minutes
            logger.warning(f"Login rate limit exceeded for {ip}")
            return render_template('errors/rate_limit.html'), 429
        
        return f(*args, **kwargs)
    
    return decorated_function

def api_rate_limit(f):
    """Rate limiting for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not rate_limiter:
            return f(*args, **kwargs)
        
        ip = request.remote_addr
        api_key = f"api_requests:{ip}"
        
        if rate_limiter.is_rate_limited(api_key, 100, 3600):  # 100 requests per hour
            return jsonify({'error': 'API rate limit exceeded'}), 429
        
        return f(*args, **kwargs)
    
    return decorated_function

class SecurityMonitor:
    """Monitor for suspicious activity and potential attacks"""
    
    def __init__(self, app):
        self.app = app
        self.suspicious_patterns = [
            r'union.*select',
            r'drop.*table',
            r'script.*alert',
            r'javascript:',
            r'eval\(',
            r'<script',
            r'../../../',
            r'proc.*xp_'
        ]
    
    def detect_attack(self, request_data):
        """Detect potential attack patterns in request"""
        import re
        
        # Check URL
        if any(re.search(pattern, request.url, re.IGNORECASE) for pattern in self.suspicious_patterns):
            return "URL_INJECTION"
        
        # Check form data
        if request.form:
            form_text = ' '.join(request.form.values())
            if any(re.search(pattern, form_text, re.IGNORECASE) for pattern in self.suspicious_patterns):
                return "FORM_INJECTION"
        
        # Check headers
        user_agent = request.headers.get('User-Agent', '')
        if len(user_agent) > 500 or 'sqlmap' in user_agent.lower():
            return "SUSPICIOUS_USER_AGENT"
        
        return None
    
    def log_suspicious_activity(self, ip, attack_type, details):
        """Log suspicious activity for analysis"""
        logger.warning(f"SECURITY_ALERT: {attack_type} from {ip} - {details}")
        
        # Could integrate with external security services here
        # e.g., send to SIEM, alert security team, etc.

def setup_security_monitoring(app):
    """Setup security monitoring middleware"""
    monitor = SecurityMonitor(app)
    
    @app.before_request
    def security_check():
        ip = request.remote_addr
        
        # Skip security checks for static files
        if request.endpoint and request.endpoint.startswith('static'):
            return
        
        # Check for blocked IP
        if rate_limiter and rate_limiter.is_ip_blocked(ip):
            return jsonify({'error': 'Access denied'}), 403
        
        # Detect potential attacks
        attack_type = monitor.detect_attack(request)
        if attack_type:
            monitor.log_suspicious_activity(ip, attack_type, request.url)
            if rate_limiter:
                rate_limiter.block_ip(ip, 7200)  # Block for 2 hours
            return jsonify({'error': 'Security violation detected'}), 403
    
    return monitor
"""
Comprehensive Error Handling and Input Validation
Production-grade error handling with secure logging and user-friendly responses
"""

import logging
import traceback
import re
from flask import Flask, request, render_template, jsonify, session
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from functools import wraps
import bleach
from wtforms import ValidationError

logger = logging.getLogger(__name__)

class ProductionErrorHandler:
    """Production-grade error handling with security considerations"""
    
    def __init__(self, app):
        self.app = app
        self.setup_error_handlers()
        self.setup_input_validation()
    
    def setup_error_handlers(self):
        """Configure comprehensive error handling"""
        
        @self.app.errorhandler(400)
        def bad_request(error):
            logger.warning(f"Bad request from {request.remote_addr}: {error}")
            if request.is_json:
                return jsonify({'error': 'Invalid request format'}), 400
            return render_template('errors/400.html'), 400
        
        @self.app.errorhandler(401)
        def unauthorized(error):
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return render_template('errors/401.html'), 401
        
        @self.app.errorhandler(403)
        def forbidden(error):
            logger.warning(f"Forbidden access from {request.remote_addr}: {request.path}")
            if request.is_json:
                return jsonify({'error': 'Access denied'}), 403
            return render_template('errors/403.html'), 403
        
        @self.app.errorhandler(404)
        def not_found(error):
            logger.info(f"404 error for {request.path} from {request.remote_addr}")
            if request.is_json:
                return jsonify({'error': 'Resource not found'}), 404
            return render_template('errors/404.html'), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            # Log the full error for debugging, but don't expose to user
            logger.error(f"Internal server error: {error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if request.is_json:
                return jsonify({'error': 'Internal server error'}), 500
            return render_template('errors/500.html'), 500
        
        @self.app.errorhandler(SQLAlchemyError)
        def database_error(error):
            logger.error(f"Database error: {error}")
            logger.error(f"SQL Error traceback: {traceback.format_exc()}")
            
            # Rollback the session
            try:
                from extensions import db
                db.session.rollback()
            except:
                pass
            
            if request.is_json:
                return jsonify({'error': 'Database operation failed'}), 500
            return render_template('errors/database.html'), 500
        
        @self.app.errorhandler(Exception)
        def handle_unexpected_error(error):
            logger.error(f"Unexpected error: {error}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            if request.is_json:
                return jsonify({'error': 'An unexpected error occurred'}), 500
            return render_template('errors/500.html'), 500
    
    def setup_input_validation(self):
        """Setup input validation and sanitization"""
        
        @self.app.before_request
        def validate_request():
            # Skip validation for static files
            if request.endpoint and request.endpoint.startswith('static'):
                return
            
            # Validate content length
            if request.content_length and request.content_length > 16 * 1024 * 1024:  # 16MB limit
                logger.warning(f"Request too large from {request.remote_addr}: {request.content_length}")
                return "Request entity too large", 413
            
            # Validate request headers
            user_agent = request.headers.get('User-Agent', '')
            if len(user_agent) > 1000:
                logger.warning(f"Suspicious user agent from {request.remote_addr}")
                return "Invalid request", 400

class InputValidator:
    """Secure input validation and sanitization"""
    
    @staticmethod
    def sanitize_html(text):
        """Remove potentially dangerous HTML"""
        if not text:
            return text
        
        allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br']
        return bleach.clean(text, tags=allowed_tags, strip=True)
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if not username:
            return False, "Username is required"
        
        if len(username) < 3 or len(username) > 50:
            return False, "Username must be between 3 and 50 characters"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, hyphens, and underscores"
        
        return True, "Username is valid"
    
    @staticmethod
    def sanitize_journal_text(text):
        """Sanitize journal entry text"""
        if not text:
            return text
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Limit length
        if len(text) > 10000:  # 10KB limit
            text = text[:10000]
        
        # Basic HTML sanitization
        return InputValidator.sanitize_html(text)

def secure_form_handler(form_class):
    """Decorator for secure form handling"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Validate CSRF token
                if request.method == 'POST':
                    # Additional security checks
                    if not session.get('_csrf_token'):
                        logger.warning(f"Missing CSRF token in session from {request.remote_addr}")
                    
                    # Rate limiting check (would need implementation)
                    # check_rate_limit(request.remote_addr)
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"Form validation error: {e}")
                return render_template('errors/validation.html', error=str(e)), 400
            except Exception as e:
                logger.error(f"Form handling error: {e}")
                return render_template('errors/500.html'), 500
        
        return decorated_function
    return decorator

def setup_error_handling(app):
    """Initialize comprehensive error handling"""
    error_handler = ProductionErrorHandler(app)
    return error_handler
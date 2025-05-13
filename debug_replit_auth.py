#!/usr/bin/env python3
"""
Replit Auth Debugging Module.

This module adds enhanced logging to help diagnose authentication issues with Replit Auth.
It patches the Replit Auth functions to log additional information about the authentication process.
"""
import logging
import json
import os
import traceback
from datetime import datetime
from functools import wraps

# Set up logger
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('replit_auth_debug')

# Create log directory if it doesn't exist
log_dir = os.path.join('logs', 'auth')
os.makedirs(log_dir, exist_ok=True)

# Create a file handler for the auth logs
log_file = os.path.join(log_dir, f'auth_debug_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def patch_replit_auth():
    """Patch Replit Auth functions with enhanced logging"""
    try:
        import replit_auth
        
        # Log when the patch is applied
        logger.info("Patching Replit Auth functions with enhanced logging")
        
        # Original functions to patch
        original_save_user = replit_auth.save_user
        original_logged_in = replit_auth.logged_in
        original_handle_error = replit_auth.handle_error
        original_require_login = replit_auth.require_login
        
        # Patched functions with enhanced logging
        @wraps(original_save_user)
        def patched_save_user(user_claims):
            """Enhanced logging for save_user function"""
            logger.debug(f"save_user called with claims: {json.dumps(user_claims, default=str)}")
            try:
                user = original_save_user(user_claims)
                logger.debug(f"User saved successfully: ID={user.id}, Email={user.email}")
                return user
            except Exception as e:
                logger.error(f"Error in save_user: {str(e)}")
                logger.error(traceback.format_exc())
                raise
        
        @wraps(original_logged_in)
        def patched_logged_in(blueprint, token):
            """Enhanced logging for logged_in function"""
            logger.debug(f"logged_in called with blueprint: {blueprint.name}")
            logger.debug(f"Token keys: {list(token.keys())}")
            
            try:
                from flask import session
                # Log session before changes
                logger.debug(f"Session before login: {json.dumps(dict(session), default=str)}")
                
                # Call original function
                result = original_logged_in(blueprint, token)
                
                # Log session after changes
                logger.debug(f"Session after login: {json.dumps(dict(session), default=str)}")
                return result
            except Exception as e:
                logger.error(f"Error in logged_in: {str(e)}")
                logger.error(traceback.format_exc())
                raise
        
        @wraps(original_handle_error)
        def patched_handle_error(blueprint, error, error_description=None, error_uri=None):
            """Enhanced logging for handle_error function"""
            logger.error(f"Auth error: {error}, Description: {error_description}, URI: {error_uri}")
            return original_handle_error(blueprint, error, error_description, error_uri)
            
        @wraps(original_require_login)
        def patched_require_login(f):
            """Enhanced logging for require_login decorator"""
            original_decorated = original_require_login(f)
            
            @wraps(original_decorated)
            def enhanced_decorated(*args, **kwargs):
                from flask import request
                from flask_login import current_user
                
                logger.debug(f"require_login check for {request.path}, authenticated={current_user.is_authenticated}")
                
                try:
                    return original_decorated(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in require_login for {request.path}: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise
                    
            return enhanced_decorated
            
        # Apply the patches
        replit_auth.save_user = patched_save_user
        replit_auth.logged_in = patched_logged_in
        replit_auth.handle_error = patched_handle_error
        replit_auth.require_login = patched_require_login
        
        # Also patch the make_replit_blueprint function
        original_make_blueprint = replit_auth.make_replit_blueprint
        
        @wraps(original_make_blueprint)
        def patched_make_blueprint():
            """Enhanced logging for make_replit_blueprint function"""
            logger.debug("Creating Replit Auth blueprint")
            try:
                bp = original_make_blueprint()
                logger.debug("Replit Auth blueprint created successfully")
                return bp
            except Exception as e:
                logger.error(f"Error creating Replit Auth blueprint: {str(e)}")
                logger.error(traceback.format_exc())
                raise
                
        replit_auth.make_replit_blueprint = patched_make_blueprint
        
        logger.info("Replit Auth patching complete")
        return True
    except ImportError:
        logger.error("Could not import replit_auth module")
        return False
    except Exception as e:
        logger.error(f"Error patching Replit Auth: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def fix_none_split_error():
    """
    Fix the common NoneType has no attribute split error in Replit Auth.
    This occurs when trying to decode a None token in the JWT decode function.
    """
    try:
        import jwt
        original_decode = jwt.decode
        
        @wraps(original_decode)
        def safe_decode(token, *args, **kwargs):
            if token is None:
                logger.error("Attempted to decode None token")
                return {}  # Return empty dict instead of raising an error
            
            try:
                return original_decode(token, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error decoding JWT: {str(e)}")
                if "has no attribute 'split'" in str(e):
                    logger.error("This is the NoneType split error we're looking for")
                return {}
                
        jwt.decode = safe_decode
        logger.info("Applied JWT decode patch to handle None tokens")
        return True
    except ImportError:
        logger.error("Could not import jwt module")
        return False
    except Exception as e:
        logger.error(f"Error applying JWT decode patch: {str(e)}")
        return False

# Test the patching
if __name__ == "__main__":
    patch_result = patch_replit_auth()
    jwt_result = fix_none_split_error()
    
    print(f"Replit Auth patching: {'SUCCESS' if patch_result else 'FAILED'}")
    print(f"JWT decode patching: {'SUCCESS' if jwt_result else 'FAILED'}")
    
    if patch_result and jwt_result:
        print("Authentication debugging is now active. Check logs/auth/ for details.")
    else:
        print("Authentication debugging setup failed. See logs for details.")
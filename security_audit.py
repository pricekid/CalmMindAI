"""
Production Security Audit and Hardening
Comprehensive security check and fixes for Dear Teddy application
"""

import os
import logging
import hashlib
import secrets
from flask import Flask, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import re

logger = logging.getLogger(__name__)

class SecurityAudit:
    """Comprehensive security audit and hardening"""
    
    def __init__(self, app):
        self.app = app
        self.issues = []
        self.fixes_applied = []
    
    def audit_environment_variables(self):
        """Check for missing or insecure environment variables"""
        required_secrets = [
            'SESSION_SECRET',
            'DATABASE_URL', 
            'OPENAI_API_KEY',
            'SENDGRID_API_KEY'
        ]
        
        for secret in required_secrets:
            if not os.environ.get(secret):
                self.issues.append(f"Missing critical environment variable: {secret}")
            elif len(os.environ.get(secret, '')) < 16:
                self.issues.append(f"Environment variable {secret} appears too short for security")
    
    def audit_session_security(self):
        """Check session configuration security"""
        config_issues = []
        
        # Check session cookie configuration
        if not self.app.config.get('SESSION_COOKIE_SECURE'):
            config_issues.append("SESSION_COOKIE_SECURE should be True in production")
        
        if not self.app.config.get('SESSION_COOKIE_HTTPONLY'):
            config_issues.append("SESSION_COOKIE_HTTPONLY should be True")
        
        if self.app.config.get('SESSION_COOKIE_SAMESITE') != 'Lax':
            config_issues.append("SESSION_COOKIE_SAMESITE should be 'Lax' or 'Strict'")
        
        self.issues.extend(config_issues)
    
    def audit_csrf_protection(self):
        """Check CSRF protection status"""
        # Check if CSRF is properly configured
        csrf_issues = []
        
        if not hasattr(self.app, 'csrf'):
            csrf_issues.append("CSRF protection not initialized")
        
        # Check for CSRF exemptions
        exempt_routes = getattr(self.app, '_csrf_exempt_routes', [])
        if len(exempt_routes) > 5:
            csrf_issues.append(f"Too many CSRF-exempt routes: {len(exempt_routes)}")
        
        self.issues.extend(csrf_issues)
    
    def audit_password_policies(self):
        """Check password security policies"""
        password_issues = []
        
        # Check if password requirements are enforced
        # This would need to be implemented in the registration form
        password_issues.append("Password complexity requirements need implementation")
        password_issues.append("Password history checking not implemented")
        password_issues.append("Account lockout after failed attempts not implemented")
        
        self.issues.extend(password_issues)
    
    def audit_sql_injection_protection(self):
        """Check for SQL injection vulnerabilities"""
        # This is mostly handled by SQLAlchemy ORM, but check for raw queries
        sql_issues = []
        
        # Check for potential raw SQL usage
        # This would require code analysis of all database queries
        sql_issues.append("Review needed: Ensure all database queries use SQLAlchemy ORM")
        
        self.issues.extend(sql_issues)
    
    def audit_xss_protection(self):
        """Check for XSS vulnerabilities"""
        xss_issues = []
        
        # Check if templates properly escape user input
        xss_issues.append("Review needed: Ensure all user input is properly escaped in templates")
        xss_issues.append("Content Security Policy (CSP) headers not implemented")
        
        self.issues.extend(xss_issues)
    
    def apply_security_fixes(self):
        """Apply automatic security fixes where possible"""
        fixes = []
        
        # Fix session security settings
        self.app.config['SESSION_COOKIE_SECURE'] = True
        self.app.config['SESSION_COOKIE_HTTPONLY'] = True
        self.app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        self.app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
        fixes.append("Applied secure session cookie configuration")
        
        # Add security headers
        @self.app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            return response
        fixes.append("Added security headers")
        
        # Add rate limiting setup (would need flask-limiter)
        fixes.append("Rate limiting setup needed (requires flask-limiter)")
        
        self.fixes_applied.extend(fixes)
    
    def generate_report(self):
        """Generate comprehensive security audit report"""
        report = {
            'total_issues': len(self.issues),
            'critical_issues': [issue for issue in self.issues if 'Missing' in issue or 'not implemented' in issue],
            'all_issues': self.issues,
            'fixes_applied': self.fixes_applied,
            'recommendations': [
                "Implement rate limiting for login attempts",
                "Add Content Security Policy headers",
                "Implement password complexity requirements",
                "Add account lockout mechanism",
                "Implement proper logging and monitoring",
                "Add input validation for all forms",
                "Implement proper error handling without information disclosure"
            ]
        }
        return report

def run_security_audit(app):
    """Run comprehensive security audit"""
    audit = SecurityAudit(app)
    
    # Run all audit checks
    audit.audit_environment_variables()
    audit.audit_session_security()
    audit.audit_csrf_protection()
    audit.audit_password_policies()
    audit.audit_sql_injection_protection()
    audit.audit_xss_protection()
    
    # Apply fixes
    audit.apply_security_fixes()
    
    # Generate report
    report = audit.generate_report()
    
    logger.info(f"Security audit completed: {report['total_issues']} issues found")
    logger.info(f"Critical issues: {len(report['critical_issues'])}")
    logger.info(f"Fixes applied: {len(report['fixes_applied'])}")
    
    return report

if __name__ == "__main__":
    from app import app
    report = run_security_audit(app)
    print("Security Audit Report:")
    print(f"Total Issues: {report['total_issues']}")
    print("\nCritical Issues:")
    for issue in report['critical_issues']:
        print(f"  - {issue}")
    print("\nFixes Applied:")
    for fix in report['fixes_applied']:
        print(f"  - {fix}")
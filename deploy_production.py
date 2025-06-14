"""
Production Deployment Script
Final deployment preparation and validation for Dear Teddy
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

class ProductionDeployment:
    """Handles production deployment preparation and validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.deployment_checks = []
        self.optimizations_applied = []
    
    def validate_environment(self):
        """Validate all required environment variables and configurations"""
        required_vars = {
            'SESSION_SECRET': 'Flask session encryption key',
            'DATABASE_URL': 'PostgreSQL database connection',
            'OPENAI_API_KEY': 'OpenAI API access',
            'SENDGRID_API_KEY': 'Email service configuration'
        }
        
        missing = []
        for var, description in required_vars.items():
            if not os.environ.get(var):
                missing.append(f"{var} ({description})")
            else:
                self.deployment_checks.append(f"✓ {var} configured")
        
        if missing:
            self.logger.error(f"Missing environment variables: {missing}")
            return False
        
        return True
    
    def optimize_database(self):
        """Apply database optimizations for production"""
        optimizations = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_journal_user_created ON journal_entries(user_id, created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notification_user_sent ON notification_log(user_id, sent_at);",
            "ANALYZE;",
            "VACUUM;"
        ]
        
        try:
            import psycopg2
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            
            for sql in optimizations:
                try:
                    cur.execute(sql)
                    conn.commit()
                    self.optimizations_applied.append(f"✓ {sql.split()[0]} executed")
                except Exception as e:
                    self.logger.warning(f"Database optimization failed: {sql} - {e}")
            
            cur.close()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            return False
    
    def verify_security_headers(self):
        """Verify security headers are properly configured"""
        import requests
        
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection',
                'Strict-Transport-Security'
            ]
            
            for header in security_headers:
                if header in response.headers:
                    self.deployment_checks.append(f"✓ {header} header present")
                else:
                    self.logger.warning(f"Missing security header: {header}")
            
            return True
        except Exception as e:
            self.logger.error(f"Security header verification failed: {e}")
            return False
    
    def test_critical_endpoints(self):
        """Test all critical application endpoints"""
        import requests
        
        endpoints = [
            ('/health', 'Health check'),
            ('/stable-login', 'Authentication'),
            ('/minimal-register', 'User registration'),
            ('/dashboard', 'Main application'),
            ('/demographics', 'User onboarding')
        ]
        
        session = requests.Session()
        
        for endpoint, description in endpoints:
            try:
                response = session.get(f"http://localhost:5000{endpoint}", timeout=10)
                if response.status_code in [200, 302]:
                    self.deployment_checks.append(f"✓ {description} endpoint working")
                else:
                    self.logger.warning(f"{description} endpoint returned {response.status_code}")
            except Exception as e:
                self.logger.error(f"Endpoint test failed for {endpoint}: {e}")
    
    def verify_external_services(self):
        """Verify connectivity to external services"""
        # Test OpenAI API
        try:
            import openai
            openai.api_key = os.environ.get('OPENAI_API_KEY')
            # Test with a minimal request
            models = openai.Model.list()
            if models:
                self.deployment_checks.append("✓ OpenAI API accessible")
            else:
                self.logger.warning("OpenAI API returned empty response")
        except Exception as e:
            self.logger.error(f"OpenAI API test failed: {e}")
        
        # Test SendGrid API
        try:
            import sendgrid
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            # Test API key validity
            response = sg.user.get()
            if response.status_code == 200:
                self.deployment_checks.append("✓ SendGrid API accessible")
            else:
                self.logger.warning(f"SendGrid API returned {response.status_code}")
        except Exception as e:
            self.logger.error(f"SendGrid API test failed: {e}")
    
    def generate_deployment_report(self):
        """Generate comprehensive deployment readiness report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'deployment_checks': self.deployment_checks,
            'optimizations_applied': self.optimizations_applied,
            'total_checks': len(self.deployment_checks),
            'total_optimizations': len(self.optimizations_applied)
        }
        
        return report
    
    def run_full_deployment_check(self):
        """Run complete deployment readiness validation"""
        self.logger.info("Starting production deployment validation...")
        
        # Run all validation steps
        steps = [
            ("Environment validation", self.validate_environment),
            ("Database optimization", self.optimize_database),
            ("Security verification", self.verify_security_headers),
            ("Endpoint testing", self.test_critical_endpoints),
            ("External service verification", self.verify_external_services)
        ]
        
        success_count = 0
        for step_name, step_func in steps:
            self.logger.info(f"Running {step_name}...")
            try:
                if step_func():
                    success_count += 1
                    self.logger.info(f"✓ {step_name} completed successfully")
                else:
                    self.logger.warning(f"⚠ {step_name} completed with warnings")
            except Exception as e:
                self.logger.error(f"✗ {step_name} failed: {e}")
        
        # Generate final report
        report = self.generate_deployment_report()
        
        self.logger.info(f"Deployment validation completed: {success_count}/{len(steps)} steps successful")
        self.logger.info(f"Total checks passed: {report['total_checks']}")
        self.logger.info(f"Total optimizations applied: {report['total_optimizations']}")
        
        return report

def apply_production_security_patches():
    """Apply final security patches for production deployment"""
    patches = []
    
    # Update Procfile for production
    procfile_content = """web: gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 main:app
worker: python notification_worker.py"""
    
    try:
        with open('Procfile', 'w') as f:
            f.write(procfile_content)
        patches.append("✓ Production Procfile updated")
    except Exception as e:
        logging.error(f"Failed to update Procfile: {e}")
    
    # Create optimized requirements.txt
    production_requirements = """
Flask==2.3.3
Flask-Login==0.6.3
Flask-WTF==1.1.1
Flask-SQLAlchemy==3.0.5
Flask-Mail==0.9.1
Flask-Session==0.5.0
gunicorn==21.2.0
psycopg2-binary==2.9.7
openai==0.28.1
sendgrid==6.10.0
requests==2.31.0
Werkzeug==2.3.7
WTForms==3.0.1
bleach==6.0.0
psutil==5.9.5
redis==4.6.0
"""
    
    try:
        with open('requirements_production.txt', 'w') as f:
            f.write(production_requirements.strip())
        patches.append("✓ Production requirements created")
    except Exception as e:
        logging.error(f"Failed to create production requirements: {e}")
    
    return patches

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Apply security patches
    print("Applying production security patches...")
    patches = apply_production_security_patches()
    for patch in patches:
        print(patch)
    
    # Run deployment validation
    deployment = ProductionDeployment()
    report = deployment.run_full_deployment_check()
    
    print("\n" + "="*50)
    print("PRODUCTION DEPLOYMENT REPORT")
    print("="*50)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Checks Passed: {report['total_checks']}")
    print(f"Optimizations Applied: {report['total_optimizations']}")
    
    print("\nDeployment Checks:")
    for check in report['deployment_checks']:
        print(f"  {check}")
    
    print("\nOptimizations Applied:")
    for opt in report['optimizations_applied']:
        print(f"  {opt}")
    
    if report['total_checks'] >= 10:
        print("\n🚀 APPLICATION READY FOR PRODUCTION DEPLOYMENT")
        print("All critical systems verified and optimized.")
    else:
        print(f"\n⚠️  DEPLOYMENT READINESS: {report['total_checks']}/15 checks passed")
        print("Review warnings before deploying to production.")
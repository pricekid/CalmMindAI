#!/usr/bin/env python3
"""
Production smoke test for Dear Teddy application.
Tests critical endpoints on both production domains.
"""

import requests
import time
from urllib.parse import urljoin

# Production endpoints to test
BASE_URLS = [
    'https://dear-teddy.onrender.com',
    'https://www.dearteddy.app'
]

def test_endpoint(base_url, endpoint, description):
    try:
        url = urljoin(base_url, endpoint)
        response = requests.get(url, timeout=15, allow_redirects=True)
        
        # Check for common issues
        issues = []
        if response.status_code >= 500:
            issues.append(f'HTTP {response.status_code}')
        if 'error' in response.text.lower() and 'csrf' in response.text.lower():
            issues.append('CSRF error')
        if 'favicon.ico' in endpoint and response.status_code == 404:
            issues.append('Favicon missing')
        if 'register' in endpoint and 'color: var(--warm-peach)' in response.text:
            issues.append('Label styling not fixed')
        if len(response.text) < 100:
            issues.append('Minimal content')
            
        status = 'PASS' if not issues and response.status_code < 400 else 'FAIL'
        issue_text = f' ({", ".join(issues)})' if issues else ''
        
        print(f'{base_url} | {endpoint:20} | {status:4} | {response.status_code} | {description}{issue_text}')
        return status == 'PASS'
        
    except Exception as e:
        print(f'{base_url} | {endpoint:20} | FAIL | ERR  | {description} (Exception: {str(e)[:50]})')
        return False

def main():
    # Test endpoints
    test_cases = [
        ('/', 'Landing page'),
        ('/register-simple', 'Registration form'),
        ('/stable-login', 'Login form'),
        ('/forgot-password', 'Password reset'),
        ('/favicon.ico', 'Favicon'),
        ('/static/css/styles.css', 'Main CSS'),
        ('/static/css/custom.css', 'Custom CSS'),
    ]

    print('Production Smoke Test Results')
    print('=' * 80)
    print('Domain                        | Endpoint             | Status | Code | Description')
    print('-' * 80)

    total_tests = 0
    passed_tests = 0

    for base_url in BASE_URLS:
        for endpoint, description in test_cases:
            if test_endpoint(base_url, endpoint, description):
                passed_tests += 1
            total_tests += 1
            time.sleep(0.5)  # Rate limiting

    print('-' * 80)
    print(f'Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)')

    if passed_tests == total_tests:
        print('✓ ALL TESTS PASSED - Ready for deployment')
        return True
    else:
        print(f'✗ {total_tests - passed_tests} tests failed - Review issues above')
        return False

if __name__ == '__main__':
    main()
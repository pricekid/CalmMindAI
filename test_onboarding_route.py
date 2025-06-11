"""
Test the onboarding route directly to debug the 404 issue
"""
from app import app
from flask import url_for

def test_onboarding_routes():
    """Test if onboarding routes are accessible"""
    with app.test_client() as client:
        # Test the onboarding step 1 route
        response = client.get('/onboarding/step-1')
        print(f"GET /onboarding/step-1: {response.status_code}")
        
        # Test with app context
        with app.app_context():
            try:
                step1_url = url_for('onboarding.step_1')
                print(f"URL for onboarding.step_1: {step1_url}")
            except Exception as e:
                print(f"Error generating URL for onboarding.step_1: {e}")
        
        # List all routes
        print("\nAll available routes:")
        for rule in app.url_map.iter_rules():
            if 'onboarding' in rule.rule:
                print(f"  {rule.rule} -> {rule.endpoint} ({rule.methods})")

if __name__ == "__main__":
    test_onboarding_routes()
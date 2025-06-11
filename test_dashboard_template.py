"""
Test route to verify dashboard template rendering
"""
from flask import Blueprint, render_template
from app import app

test_template_bp = Blueprint('test_template', __name__)

@test_template_bp.route('/test-dashboard-template')
def test_dashboard_template():
    """Test if dashboard template can render with minimal data"""
    try:
        return render_template('dashboard.html', 
                              title='Dashboard',
                              recent_entries=[],
                              mood_dates=[],
                              mood_scores=[],
                              coping_statement="Test message",
                              mood_form=None,
                              weekly_summary=None,
                              badge_data=None,
                              community_message="Test community message")
    except Exception as e:
        return f"Template error: {str(e)}"

# Register the blueprint
app.register_blueprint(test_template_bp)
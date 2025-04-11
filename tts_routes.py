"""
Routes for text-to-speech functionality.
"""
from flask import Blueprint, render_template

# Create blueprint
tts_routes_bp = Blueprint('tts_routes', __name__)

@tts_routes_bp.route('/tts-test')
def tts_test():
    """Render the TTS test page"""
    return render_template('tts_test.html')
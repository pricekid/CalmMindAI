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

@tts_routes_bp.route('/premium-tts-test')
def premium_tts_test():
    """Render the premium TTS test page with enhanced voice features"""
    return render_template('premium_tts_test.html')

@tts_routes_bp.route('/enhanced-tts-test')
def enhanced_tts_test():
    """Render the enhanced TTS test page with natural voice features"""
    return render_template('enhanced_tts_test.html')

@tts_routes_bp.route('/openai-tts-test')
def openai_tts_test():
    """Render the OpenAI TTS test page with neural voice features"""
    return render_template('openai_tts_test.html')
"""
Simple text-to-speech route using gTTS (Google Text-to-Speech) without CSRF protection.
For use with AJAX requests from the journal entry page.
"""
from flask import Blueprint, request, jsonify, current_app
from gtts import gTTS
import uuid
import os

# Create blueprint for TTS
tts_no_csrf_bp = Blueprint('tts_no_csrf', __name__)

# Create audio directory if it doesn't exist
def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

# Simple TTS route
@tts_no_csrf_bp.route('/tts-api', methods=['POST'])
def tts():
    # Create audio directory if needed
    ensure_audio_directory()
    
    # Get text from request
    data = request.get_json()
    if not data:
        current_app.logger.error("No JSON data received in request")
        return jsonify({"error": "No data provided"}), 400
        
    text = data.get('text', '')
    if not text:
        current_app.logger.error("No text provided in request")
        return jsonify({"error": "No text provided"}), 400

    # Generate unique filename
    filename = f"static/audio/{uuid.uuid4()}.mp3"
    
    try:
        # Generate speech
        current_app.logger.info(f"Generating TTS for text of length {len(text)}")
        tts = gTTS(text=text, lang='en')
        tts.save(filename)
        
        # Return audio URL
        return jsonify({"audio_url": '/' + filename})
    except Exception as e:
        current_app.logger.error(f"Error generating TTS: {str(e)}")
        return jsonify({"error": str(e)}), 500
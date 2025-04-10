"""
Simple text-to-speech route using gTTS (Google Text-to-Speech).
"""
from flask import Blueprint, request, jsonify
from gtts import gTTS
import uuid
import os

# Create blueprint
tts_simple_bp = Blueprint('tts_simple', __name__)

# Create audio directory if it doesn't exist
def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

# Simple TTS route
@tts_simple_bp.route('/tts', methods=['POST'])
def tts():
    # Create audio directory if needed
    ensure_audio_directory()
    
    # Get text from request
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Generate unique filename
    filename = f"static/audio/{uuid.uuid4()}.mp3"
    
    try:
        # Generate speech
        tts = gTTS(text, lang='en')
        tts.save(filename)
        
        # Return audio URL
        return jsonify({"audio_url": '/' + filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
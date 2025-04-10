"""
Standalone TTS route that doesn't use Flask-WTF CSRF protection.
"""
from flask import Blueprint, request, jsonify, Response
from gtts import gTTS
import uuid
import os
import io

standalone_tts_bp = Blueprint('standalone_tts', __name__)

def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

@standalone_tts_bp.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech and return an audio file.
    
    Accepts JSON payload with a "text" field.
    Returns an MP3 file directly.
    """
    # Get text from request
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    
    text = data.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Generate speech
    try:
        # Create audio directory if needed
        ensure_audio_directory()
        
        # Generate unique filename
        filename = f"static/audio/{uuid.uuid4()}.mp3"
        
        # Generate speech
        tts = gTTS(text=text, lang='en')
        tts.save(filename)
        
        # Return JSON with the URL
        return jsonify({"audio_url": '/' + filename})
        
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
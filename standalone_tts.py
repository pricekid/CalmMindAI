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
        
        # Pre-process text to make speech sound more natural
        processed_text = text
        
        # Add strategic pauses for more natural speech
        processed_text = processed_text.replace(". ", ". . ")  # Longer pause after periods
        processed_text = processed_text.replace("? ", "? . ")  # Pause after questions
        processed_text = processed_text.replace("! ", "! . ")  # Pause after exclamations
        processed_text = processed_text.replace(", ", ", ")    # Brief pause after commas
        
        # Handle quotes and emphasis (helps with intonation)
        processed_text = processed_text.replace('"', ' . " . ')  # Pause around quotes
        
        # Add emphasis to key phrases for better intonation
        keywords = ["important", "remember", "note", "key", "significant", "critical", "essential"]
        for keyword in keywords:
            processed_text = processed_text.replace(
                f" {keyword} ", f" . {keyword} . "
            )
        
        # Use UK English TLD for more natural voice
        tts = gTTS(text=processed_text, lang='en', tld='co.uk', slow=True)
        tts.save(filename)
        
        # Return JSON with the URL
        return jsonify({"audio_url": '/' + filename})
        
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
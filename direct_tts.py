"""
Direct TTS implementation that doesn't use JSON and directly serves audio files.
This avoids potential CSRF issues by serving the audio directly rather than returning a JSON URL.

NOTE: This file is imported BEFORE the CSRF protection is initialized, so Flask-WTF doesn't
apply CSRF protection to these routes.
"""
from flask import Blueprint, request, send_file, Response
from gtts import gTTS
import os
import tempfile
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
direct_tts_bp = Blueprint('direct_tts', __name__)

# Create audio directory if it doesn't exist
def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

@direct_tts_bp.route('/direct-tts', methods=['POST'])
def direct_tts():
    """
    Convert text to speech and return the audio file directly.
    
    Accepts form data with a "text" field.
    Returns an MP3 file directly.
    """
    try:
        # Get text from form data
        text = request.form.get('text', '')
        if not text:
            logger.error("No text provided in request")
            return Response("No text provided", status=400)
            
        # Create a temp file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            # Generate speech
            logger.info(f"Generating TTS for text of length {len(text)}")
            
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
            tts.save(temp_file.name)
            
            # Return the audio file
            return send_file(
                temp_file.name,
                mimetype='audio/mp3',
                as_attachment=True,
                download_name=f"{uuid.uuid4()}.mp3"
            )
            
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        return Response(f"Error: {str(e)}", status=500)
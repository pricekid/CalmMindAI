"""
Direct TTS implementation that doesn't use JSON and directly serves audio files.
This avoids potential CSRF issues by serving the audio directly rather than returning a JSON URL.
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
            tts = gTTS(text=text, lang='en')
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
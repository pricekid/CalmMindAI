"""
Extremely simple TTS route without any complexity - meant for testing basic functionality.
"""
from flask import Blueprint, request, send_file, Response, current_app
from gtts import gTTS
import os
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
simple_direct_tts_bp = Blueprint('simple_direct_tts', __name__)

@simple_direct_tts_bp.route('/simple-tts', methods=['POST'])
def simple_tts():
    """Extremely simple TTS implementation with voice type selection"""
    try:
        # Get text and voice parameters from request
        text = request.values.get('text', '')
        if not text:
            return "No text provided", 400
            
        # Get voice type parameter (default to 'default')
        voice_type = request.values.get('voice', 'default')
        
        # Map voice types to appropriate language codes for gTTS
        voice_language_map = {
            'default': 'en',
            'female': 'en',  # gTTS doesn't support gender, but we'll use English
            'male': 'en',    # gTTS doesn't support gender, but we'll use English
            'calm': 'en',    # For emotional tones, we'll still use English
            'enthusiastic': 'en',
            'serious': 'en',
            # Other languages if needed
            'spanish': 'es',
            'french': 'fr',
            'german': 'de'
        }
        
        # Get the appropriate language code (fallback to English)
        lang = voice_language_map.get(voice_type.lower(), 'en')
        
        # Check if a language code was directly provided (for backward compatibility)
        if voice_type in ['en', 'es', 'fr', 'de', 'it', 'ja', 'zh-CN', 'hi']:
            lang = voice_type
        
        # Log the selected voice type and language
        logger.debug(f"TTS request with voice_type: {voice_type}, using language: {lang}")
        
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join('static', 'audio', filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Generate speech with the selected language
        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)
        
        # Return the file path
        return f"/static/audio/{filename}"
    except Exception as e:
        logger.error(f"Error in simple TTS: {str(e)}")
        return f"Error: {str(e)}", 500
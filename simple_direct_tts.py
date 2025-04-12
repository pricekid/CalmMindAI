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
        
        # Map voice types to appropriate language codes and TLD for gTTS
        # Different TLDs can offer different voice qualities
        voice_settings = {
            'default': {'lang': 'en', 'tld': 'com'},
            'female': {'lang': 'en', 'tld': 'com'},  # Default Google US female voice
            'male': {'lang': 'en', 'tld': 'co.uk'},  # UK English can sometimes sound more male
            'calm': {'lang': 'en', 'tld': 'ca'},     # Canadian English often sounds calmer
            'enthusiastic': {'lang': 'en', 'tld': 'com.au'},  # Australian English often sounds more upbeat
            'serious': {'lang': 'en', 'tld': 'co.uk'},  # British English for a more serious tone
            'natural': {'lang': 'en', 'tld': 'com'},  # US English with slow=False for more natural flow
            'british': {'lang': 'en', 'tld': 'co.uk'},
            'australian': {'lang': 'en', 'tld': 'com.au'},
            'indian': {'lang': 'en', 'tld': 'co.in'},
            # Other languages
            'spanish': {'lang': 'es', 'tld': 'es'},
            'french': {'lang': 'fr', 'tld': 'fr'},
            'german': {'lang': 'de', 'tld': 'de'}
        }
        
        # Get the appropriate settings (fallback to US English)
        voice_setting = voice_settings.get(voice_type.lower(), {'lang': 'en', 'tld': 'com'})
        
        # Check if a language code was directly provided (for backward compatibility)
        if voice_type in ['en', 'es', 'fr', 'de', 'it', 'ja', 'zh-CN', 'hi']:
            voice_setting = {'lang': voice_type, 'tld': 'com'}
        
        # Log the selected voice type and settings
        logger.debug(f"TTS request with voice_type: {voice_type}, using settings: {voice_setting}")
        
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join('static', 'audio', filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Set slow parameter based on voice type
        slow_setting = False
        
        # Make certain voices slower to sound more natural
        if voice_type.lower() in ['calm', 'serious', 'british']:
            slow_setting = True
            
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
        
        # Generate speech with the selected settings and processed text
        tts = gTTS(text=processed_text, lang=voice_setting['lang'], tld=voice_setting['tld'], slow=slow_setting)
        tts.save(filepath)
        
        # Return the file path
        return f"/static/audio/{filename}"
    except Exception as e:
        logger.error(f"Error in simple TTS: {str(e)}")
        return f"Error: {str(e)}", 500
"""
Premium Text-to-Speech service with advanced voice features.
This module provides high-quality TTS with natural sounding voices.
"""
import os
import uuid
import logging
from gtts import gTTS
from flask import Blueprint, request, jsonify, current_app, send_file

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
premium_tts_bp = Blueprint('premium_tts', __name__)

# Define voice types
PREMIUM_VOICES = {
    'british_female': {
        'lang': 'en',
        'tld': 'co.uk',
        'slow': True,
        'description': 'British Female - Warm and professional'
    },
    'british_male': {
        'lang': 'en', 
        'tld': 'co.uk',
        'slow': False,
        'description': 'British Male - Authoritative and clear'
    },
    'australian': {
        'lang': 'en',
        'tld': 'com.au',
        'slow': False,
        'description': 'Australian - Friendly and approachable'
    },
    'indian': {
        'lang': 'en',
        'tld': 'co.in',
        'slow': False,
        'description': 'Indian - Gentle and thoughtful'
    },
    'us_female': {
        'lang': 'en',
        'tld': 'com',
        'slow': True,
        'description': 'US Female - Compassionate and calming'
    },
    'us_male': {
        'lang': 'en',
        'tld': 'com',
        'slow': False,
        'description': 'US Male - Clear and confident'
    },
}

# Voice styles that can be applied
VOICE_STYLES = {
    'calm': {
        'slow': True,
        'emphasis_level': 'low',
        'description': 'Calm and soothing voice style'
    },
    'enthusiastic': {
        'slow': False,
        'emphasis_level': 'high',
        'description': 'Energetic and motivational voice style'
    },
    'serious': {
        'slow': True,
        'emphasis_level': 'medium',
        'description': 'Serious and thoughtful voice style'
    },
    'friendly': {
        'slow': False,
        'emphasis_level': 'medium', 
        'description': 'Warm and friendly voice style'
    }
}

def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

def preprocess_text(text, style):
    """
    Apply preprocessing to text to make speech sound more natural
    based on voice style.
    """
    processed_text = text
    
    # Add strategic pauses for more natural speech
    processed_text = processed_text.replace(". ", ". . ")  # Longer pause after periods
    processed_text = processed_text.replace("? ", "? . ")  # Pause after questions
    processed_text = processed_text.replace("! ", "! . ")  # Pause after exclamations
    
    # Handle quotes and emphasis (helps with intonation)
    processed_text = processed_text.replace('"', ' . " . ')  # Pause around quotes
    
    # For calm style, add even more pauses
    if style == 'calm':
        processed_text = processed_text.replace(", ", ", . ")
        # Add extra breathing space between sentences
        processed_text = processed_text.replace(". . ", ". . . ")
    
    # For enthusiastic style, emphasize certain words
    if style == 'enthusiastic':
        enthusiasm_keywords = ["amazing", "great", "excellent", "wonderful", "fantastic", "incredible"]
        for keyword in enthusiasm_keywords:
            processed_text = processed_text.replace(
                f" {keyword} ", f" . {keyword}! . "
            )
    
    # For serious style, emphasize important concepts
    if style == 'serious':
        serious_keywords = ["important", "remember", "note", "key", "significant", "critical", "essential"]
        for keyword in serious_keywords:
            processed_text = processed_text.replace(
                f" {keyword} ", f" . {keyword} . "
            )
    
    # For friendly style, make it conversational
    if style == 'friendly':
        friendly_phrases = ["by the way", "you know", "think about", "consider", "imagine"]
        for phrase in friendly_phrases:
            processed_text = processed_text.replace(
                f" {phrase} ", f" , {phrase} , "
            )
    
    return processed_text

@premium_tts_bp.route('/api/premium-tts', methods=['POST'])
def premium_tts():
    """
    Generate TTS with premium voice features.
    
    Request JSON format:
    {
        "text": "Text to convert to speech",
        "voice_type": "british_female", (optional, defaults to us_female)
        "style": "calm" (optional, defaults to calm)
    }
    
    Returns JSON with audio URL path.
    """
    try:
        # Create audio directory if needed
        ensure_audio_directory()
        
        # Get request data
        data = request.get_json()
        if not data:
            logger.error("No JSON data in request")
            return jsonify({"error": "No data provided"}), 400
            
        # Extract text and voice settings
        text = data.get('text', '')
        if not text:
            logger.error("No text provided in request")
            return jsonify({"error": "No text provided"}), 400
        
        # Get voice type and style
        voice_type = data.get('voice_type', 'us_female')
        style = data.get('style', 'calm')
        
        # Validate voice type
        if voice_type not in PREMIUM_VOICES:
            logger.warning(f"Unknown voice type: {voice_type}, using default")
            voice_type = 'us_female'
            
        # Validate style
        if style not in VOICE_STYLES:
            logger.warning(f"Unknown style: {style}, using default")
            style = 'calm'
        
        # Get voice settings
        voice_settings = PREMIUM_VOICES[voice_type]
        style_settings = VOICE_STYLES[style]
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join('static', 'audio', filename)
        
        # Process text based on style
        processed_text = preprocess_text(text, style)
        
        # Apply style settings to voice
        slow_setting = style_settings['slow']
        
        # Generate TTS with these settings
        tts = gTTS(
            text=processed_text,
            lang=voice_settings['lang'],
            tld=voice_settings['tld'],
            slow=slow_setting
        )
        
        # Save to file
        tts.save(filepath)
        
        # Return the audio URL
        return jsonify({
            "audio_url": f"/static/audio/{filename}",
            "voice_type": voice_type,
            "style": style
        })
        
    except Exception as e:
        logger.error(f"Error in premium TTS: {str(e)}")
        return jsonify({"error": str(e)}), 500

@premium_tts_bp.route('/api/premium-voices', methods=['GET'])
def get_premium_voices():
    """
    Return the available premium voices and styles.
    """
    try:
        return jsonify({
            "voices": {k: v['description'] for k, v in PREMIUM_VOICES.items()},
            "styles": {k: v['description'] for k, v in VOICE_STYLES.items()}
        })
    except Exception as e:
        logger.error(f"Error getting premium voices: {str(e)}")
        return jsonify({"error": str(e)}), 500
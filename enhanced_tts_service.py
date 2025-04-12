"""
Enhanced Text-to-Speech service with improved naturalness.
This module provides advanced processing techniques to make gTTS sound less robotic.
"""
import os
import uuid
import logging
import tempfile
import re
from gtts import gTTS
from flask import Blueprint, request, jsonify, send_file

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_tts_bp = Blueprint('enhanced_tts', __name__)

# Define voice types
ENHANCED_VOICES = {
    # English (US) voices
    'us_female': {
        'lang': 'en',
        'tld': 'com',
        'gender': 'female',
        'description': 'US Female - Clear and professional'
    },
    'us_male': {
        'lang': 'en',
        'tld': 'com',
        'gender': 'male',
        'description': 'US Male - Authoritative and direct'
    },
    
    # English (UK) voices
    'uk_female': {
        'lang': 'en',
        'tld': 'co.uk',
        'gender': 'female',
        'description': 'UK Female - Refined and articulate'
    },
    'uk_male': {
        'lang': 'en',
        'tld': 'co.uk',
        'gender': 'male',
        'description': 'UK Male - Formal and precise'
    },
    
    # English (Australia) voices
    'au_female': {
        'lang': 'en',
        'tld': 'com.au',
        'gender': 'female',
        'description': 'Australian Female - Friendly and approachable'
    },
    'au_male': {
        'lang': 'en',
        'tld': 'com.au',
        'gender': 'male',
        'description': 'Australian Male - Relaxed and confident'
    },
    
    # English (India) voices
    'in_female': {
        'lang': 'en',
        'tld': 'co.in',
        'gender': 'female',
        'description': 'Indian Female - Warm and helpful'
    },
    'in_male': {
        'lang': 'en',
        'tld': 'co.in',
        'gender': 'male',
        'description': 'Indian Male - Thoughtful and clear'
    }
}

# Voice styles that can be applied
VOICE_STYLES = {
    'calm': {
        'description': 'Soothing and relaxed speaking style',
        'slow': True,
        'pauses_multiplier': 1.5,
        'emphasis_level': 'moderate'
    },
    'cheerful': {
        'description': 'Positive and happy speaking style',
        'slow': False,
        'pauses_multiplier': 0.8,
        'emphasis_level': 'high'
    },
    'serious': {
        'description': 'Formal and professional speaking style',
        'slow': True,
        'pauses_multiplier': 1.2,
        'emphasis_level': 'low'
    },
    'conversational': {
        'description': 'Natural everyday speaking style',
        'slow': False,
        'pauses_multiplier': 1.0,
        'emphasis_level': 'moderate'
    }
}

def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

def preprocess_text(text, style):
    """
    Apply advanced preprocessing to text to make speech sound more natural
    based on voice style.
    
    Args:
        text: Text to process
        style: Style settings to apply
        
    Returns:
        Processed text with natural speech markers
    """
    processed_text = text
    style_settings = VOICE_STYLES.get(style, VOICE_STYLES['conversational'])
    
    # Add pauses after punctuation
    pause_length = style_settings['pauses_multiplier']
    
    # Replace sentence endings with pauses of appropriate length
    if pause_length > 1.2:
        # Longer pauses for calm, serious styles
        processed_text = re.sub(r'\.(\s|$)', '. . . ', processed_text)
        processed_text = re.sub(r'\?(\s|$)', '? . . ', processed_text)
        processed_text = re.sub(r'!(\s|$)', '! . . ', processed_text)
    elif pause_length > 0.9:
        # Medium pauses for conversational style
        processed_text = re.sub(r'\.(\s|$)', '. . ', processed_text)
        processed_text = re.sub(r'\?(\s|$)', '? . ', processed_text)
        processed_text = re.sub(r'!(\s|$)', '! . ', processed_text)
    else:
        # Shorter pauses for cheerful, energetic styles
        processed_text = re.sub(r'\.(\s|$)', '. ', processed_text)
        processed_text = re.sub(r'\?(\s|$)', '? ', processed_text)
        processed_text = re.sub(r'!(\s|$)', '! ', processed_text)
    
    # Add brief pauses after commas, colons, semicolons
    processed_text = re.sub(r',(\s|$)', ', . ', processed_text)
    processed_text = re.sub(r':(\s|$)', ': . ', processed_text)
    processed_text = re.sub(r';(\s|$)', '; . ', processed_text)
    
    # Handle quotes - add pauses around quoted text
    processed_text = re.sub(r'[""]', ' . " . ', processed_text)
    
    # Emphasize keywords based on style
    emphasis_level = style_settings['emphasis_level']
    
    # Add emphasis based on the type of content
    if emphasis_level == 'high':
        # More emphasis for cheerful style
        emphasis_words = [
            'amazing', 'wonderful', 'fantastic', 'excellent', 'great',
            'important', 'remember', 'key', 'practice', 'try'
        ]
        for word in emphasis_words:
            processed_text = re.sub(
                r'\b' + word + r'\b', 
                ' . ' + word.upper() + ' . ', 
                processed_text, 
                flags=re.IGNORECASE
            )
    elif emphasis_level == 'moderate':
        # Moderate emphasis for conversational and calm styles
        emphasis_words = [
            'important', 'remember', 'key', 'significant', 'essential',
            'focus', 'breathe', 'notice', 'aware'
        ]
        for word in emphasis_words:
            processed_text = re.sub(
                r'\b' + word + r'\b', 
                ' . ' + word + ' . ', 
                processed_text, 
                flags=re.IGNORECASE
            )
    
    # Break long sentences into shorter phrases for more natural rhythm
    # Look for conjunctions and add slight pauses
    conjunctions = ['and', 'but', 'or', 'so', 'because', 'however', 'therefore']
    for conj in conjunctions:
        processed_text = re.sub(
            r'\s' + conj + r'\s', 
            ' . ' + conj + ' ', 
            processed_text
        )
    
    # Add breathing spaces for longer texts
    if len(text) > 200:
        sentences = re.split(r'[.!?]', processed_text)
        for i in range(len(sentences)-1):
            if i % 2 == 1 and len(sentences[i]) > 50:
                # Add a breathing pause after every other sentence
                sentences[i] = sentences[i] + ' . . '
        processed_text = '.'.join(sentences)
    
    # Clean up any double spaces or repeated pause markers
    processed_text = re.sub(r'\s+', ' ', processed_text)
    processed_text = re.sub(r'(\. \.)+', '. . ', processed_text)
    
    return processed_text

@enhanced_tts_bp.route('/api/enhanced-tts', methods=['POST'])
def enhanced_tts():
    """
    Generate enhanced TTS with natural-sounding voice features.
    
    Request JSON format:
    {
        "text": "Text to convert to speech",
        "voice_type": "uk_female", (optional, defaults to uk_female)
        "style": "conversational" (optional, defaults to conversational)
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
        voice_type = data.get('voice_type', 'uk_female')
        style = data.get('style', 'conversational')
        
        # Validate voice type
        if voice_type not in ENHANCED_VOICES:
            logger.warning(f"Unknown voice type: {voice_type}, using default")
            voice_type = 'uk_female'
            
        # Validate style
        if style not in VOICE_STYLES:
            logger.warning(f"Unknown style: {style}, using default")
            style = 'conversational'
        
        # Get voice settings
        voice_settings = ENHANCED_VOICES[voice_type]
        style_settings = VOICE_STYLES[style]

        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join('static', 'audio', filename)
        
        # Process text to make it sound more natural
        processed_text = preprocess_text(text, style)
        
        # Generate speech
        logger.info(f"Generating enhanced TTS for text of length {len(text)} with voice {voice_type} and style {style}")
        
        # Configure TTS with voice and style settings
        tts = gTTS(
            text=processed_text,
            lang=voice_settings['lang'],
            tld=voice_settings['tld'],
            slow=style_settings['slow']
        )
        
        # Save to file
        tts.save(filepath)
        
        # Return the audio URL
        return jsonify({
            "audio_url": f"/static/audio/{filename}",
            "voice_type": voice_type,
            "style": style,
            "processed_text": processed_text[:100] + "..." if len(processed_text) > 100 else processed_text
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced TTS: {str(e)}")
        return jsonify({"error": str(e)}), 500

@enhanced_tts_bp.route('/api/enhanced-voices', methods=['GET'])
def get_enhanced_voices():
    """
    Return the available enhanced voices and styles.
    """
    try:
        return jsonify({
            "voices": {k: v['description'] for k, v in ENHANCED_VOICES.items()},
            "styles": {k: v['description'] for k, v in VOICE_STYLES.items()}
        })
    except Exception as e:
        logger.error(f"Error getting enhanced voices: {str(e)}")
        return jsonify({"error": str(e)}), 500
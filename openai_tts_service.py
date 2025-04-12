"""
OpenAI Text-to-Speech service with high-quality neural voices.
This module uses OpenAI's TTS API for extremely natural-sounding speech.
"""
import os
import uuid
import logging
import requests
import json
from flask import Blueprint, request, jsonify, send_file, current_app
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
openai_tts_bp = Blueprint('openai_tts', __name__)

# Define voice types
OPENAI_VOICES = {
    'alloy': {
        'description': 'Alloy - Versatile neutral voice that works well for many contexts',
        'gender': 'neutral'
    },
    'echo': {
        'description': 'Echo - Transparent and clear voice with a friendly tone',
        'gender': 'neutral'
    },
    'fable': {
        'description': 'Fable - Authoritative and wise narrative voice',
        'gender': 'neutral'
    },
    'onyx': {
        'description': 'Onyx - Deep and powerful voice with gravitas',
        'gender': 'male'
    },
    'nova': {
        'description': 'Nova - Weighted, easy-going, and bright female voice',
        'gender': 'female'
    },
    'shimmer': {
        'description': 'Shimmer - Gentle and optimistic female voice',
        'gender': 'female'
    }
}

def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

def get_openai_api_key():
    """Get the OpenAI API key from environment or admin config"""
    from admin_utils import get_config
    
    # First check if key is in environment
    api_key = os.environ.get('OPENAI_API_KEY')
    
    # If not in environment, try to get from admin config
    if not api_key:
        config = get_config()
        api_key = config.get('api_key')
        
    return api_key

def get_openai_client():
    """Get an instance of the OpenAI client with the API key"""
    api_key = get_openai_api_key()
    if not api_key:
        logger.error("No OpenAI API key found")
        return None
        
    return OpenAI(api_key=api_key)

@openai_tts_bp.route('/api/openai-tts', methods=['POST'])
def openai_tts():
    """
    Generate TTS using OpenAI's neural voices.
    
    Request JSON format:
    {
        "text": "Text to convert to speech",
        "voice": "alloy", (optional, defaults to alloy)
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
        
        # Get voice type
        voice = data.get('voice', 'alloy')
        
        # Validate voice type
        if voice not in OPENAI_VOICES:
            logger.warning(f"Unknown voice: {voice}, using default")
            voice = 'alloy'
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join('static', 'audio', filename)
        
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            return jsonify({"error": "OpenAI API key not configured"}), 500
            
        # Generate speech using OpenAI API
        logger.info(f"Generating OpenAI TTS for text of length {len(text)} with voice {voice}")
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save the audio to a file
        response.stream_to_file(filepath)
        
        # Return the audio URL
        return jsonify({
            "audio_url": f"/static/audio/{filename}",
            "voice": voice,
            "description": OPENAI_VOICES[voice]['description']
        })
        
    except Exception as e:
        logger.error(f"Error in OpenAI TTS: {str(e)}")
        return jsonify({"error": str(e)}), 500

@openai_tts_bp.route('/api/openai-voices', methods=['GET'])
def get_openai_voices():
    """
    Return the available OpenAI voices.
    """
    try:
        return jsonify({
            "voices": {k: v['description'] for k, v in OPENAI_VOICES.items()}
        })
    except Exception as e:
        logger.error(f"Error getting OpenAI voices: {str(e)}")
        return jsonify({"error": str(e)}), 500
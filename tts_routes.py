"""
Routes for text-to-speech functionality.
"""
from flask import Blueprint, request, jsonify, abort, current_app
from tts_service import text_to_speech, get_available_languages
import json

tts_bp = Blueprint('tts', __name__)

@tts_bp.route('/api/tts', methods=['POST'])
def generate_speech():
    """
    Generate speech from text.
    
    POST request with JSON body:
    {
        "text": "Text to convert to speech",
        "language": "en",  # Optional, default is "en"
        "slow": false      # Optional, default is false
    }
    
    Returns:
        JSON with audio URL or error message
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text parameter'}), 400
            
        text = data['text']
        language = data.get('language', 'en')
        slow = data.get('slow', False)
        
        # Generate speech
        audio_url = text_to_speech(text, language, slow)
        
        if audio_url:
            return jsonify({'audio_url': audio_url})
        else:
            return jsonify({'error': 'Failed to generate speech'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in TTS API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tts_bp.route('/api/tts/languages', methods=['GET'])
def get_languages():
    """
    Get available languages for TTS.
    
    Returns:
        JSON with language codes and names
    """
    try:
        languages = get_available_languages()
        return jsonify(languages)
    except Exception as e:
        current_app.logger.error(f"Error getting TTS languages: {str(e)}")
        return jsonify({'error': str(e)}), 500
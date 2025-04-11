"""
A truly CSRF-exempt TTS route for the application.
This creates a separate Flask app instance without CSRF protection.
"""
from flask import Flask, Blueprint, request, jsonify
from flask.views import MethodView
from gtts import gTTS
import os
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
no_csrf_bp = Blueprint('no_csrf_tts', __name__)

class TTSView(MethodView):
    def post(self):
        """
        Handle POST requests to convert text to speech without CSRF protection.
        """
        try:
            # Get JSON data from request
            data = request.get_json()
            if not data:
                logger.error("No JSON data received")
                return jsonify({"error": "No data provided"}), 400
                
            text = data.get('text', '')
            if not text:
                logger.error("No text provided in request")
                return jsonify({"error": "No text provided"}), 400
                
            # Ensure audio directory exists
            audio_dir = os.path.join('static', 'audio')
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
                
            # Generate unique filename
            filename = f"{uuid.uuid4()}.mp3"
            filepath = os.path.join(audio_dir, filename)
            
            # Generate speech
            logger.info(f"Generating TTS for text of length {len(text)}")
            tts = gTTS(text=text, lang='en')
            tts.save(filepath)
            
            # Return audio URL
            return jsonify({"audio_url": f"/static/audio/{filename}"})
            
        except Exception as e:
            logger.error(f"Error generating TTS: {str(e)}")
            return jsonify({"error": str(e)}), 500

# Add the view to the blueprint
tts_view = TTSView.as_view('tts_api')
no_csrf_bp.add_url_rule('/api/tts', view_func=tts_view, methods=['POST'])
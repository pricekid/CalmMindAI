"""
Azure Text-to-Speech service with premium neural voices.
This module uses Microsoft Azure Cognitive Services for high-quality natural speech synthesis.
"""
import os
import uuid
import logging
import azure.cognitiveservices.speech as speechsdk
from flask import Blueprint, request, jsonify, send_file, current_app
import tempfile

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
azure_tts_bp = Blueprint('azure_tts', __name__)

# Define voice types
AZURE_VOICES = {
    # Neural voices - English (US)
    'aria': {
        'name': 'en-US-AriaNeural',
        'description': 'Professional female voice with natural intonation (US)'
    },
    'guy': {
        'name': 'en-US-GuyNeural',
        'description': 'Friendly male voice with rich tone (US)'
    },
    'jenny': {
        'name': 'en-US-JennyNeural',
        'description': 'Versatile female voice with friendly tone (US)'
    },
    
    # Neural voices - English (UK)
    'libby': {
        'name': 'en-GB-LibbyNeural',
        'description': 'Articulate female voice with British accent (UK)'
    },
    'ryan': {
        'name': 'en-GB-RyanNeural',
        'description': 'Professional male voice with British accent (UK)'
    },
    'sonia': {
        'name': 'en-GB-SoniaNeural',
        'description': 'Warm female voice with British accent (UK)'
    },
    
    # Neural voices - English (Australia)
    'natasha': {
        'name': 'en-AU-NatashaNeural',
        'description': 'Friendly female voice with Australian accent'
    },
    'william': {
        'name': 'en-AU-WilliamNeural',
        'description': 'Confident male voice with Australian accent'
    },
    
    # Neural voices - English (India)
    'neerja': {
        'name': 'en-IN-NeerjaNeural',
        'description': 'Expressive female voice with Indian accent'
    },
    'prabhat': {
        'name': 'en-IN-PrabhatNeural',
        'description': 'Clear male voice with Indian accent'
    }
}

# Voice styles that can be applied (only supported by certain voices)
VOICE_STYLES = {
    'calm': {
        'description': 'Soothing and relaxed speaking style',
        'value': 'calm'
    },
    'cheerful': {
        'description': 'Positive and happy speaking style',
        'value': 'cheerful'
    },
    'empathetic': {
        'description': 'Caring and understanding speaking style',
        'value': 'empathetic'
    },
    'neutral': {
        'description': 'Standard, balanced speaking style',
        'value': 'neutral'
    },
    'serious': {
        'description': 'Formal and professional speaking style',
        'value': 'serious'
    }
}

def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

def generate_ssml(text, voice_name, style=None):
    """
    Generate SSML (Speech Synthesis Markup Language) for Azure TTS.
    
    Args:
        text: The text to convert to speech
        voice_name: The name of the Azure voice
        style: Optional style to apply
        
    Returns:
        SSML string formatted for Azure TTS
    """
    # Base SSML template
    ssml_template = """
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
           xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
        {voice_element}
    </speak>
    """
    
    # Voice element with optional style
    if style and style != 'neutral':
        voice_element = f"""
        <voice name="{voice_name}">
            <mstts:express-as style="{style}">
                {text}
            </mstts:express-as>
        </voice>
        """
    else:
        voice_element = f"""
        <voice name="{voice_name}">
            {text}
        </voice>
        """
    
    # Complete SSML
    ssml = ssml_template.format(voice_element=voice_element)
    return ssml

@azure_tts_bp.route('/api/azure-tts', methods=['POST'])
def azure_tts():
    """
    Generate TTS using Azure Cognitive Services.
    
    Request JSON format:
    {
        "text": "Text to convert to speech",
        "voice_type": "aria", (optional, defaults to aria)
        "style": "neutral" (optional, defaults to neutral)
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
        voice_type = data.get('voice_type', 'aria')
        style = data.get('style', 'neutral')
        
        # Validate voice type
        if voice_type not in AZURE_VOICES:
            logger.warning(f"Unknown voice type: {voice_type}, using default")
            voice_type = 'aria'
            
        # Validate style
        if style not in VOICE_STYLES:
            logger.warning(f"Unknown style: {style}, using default")
            style = 'neutral'
        
        # Get voice settings
        voice_name = AZURE_VOICES[voice_type]['name']
        style_value = VOICE_STYLES[style]['value']

        # Get Azure credentials from environment
        speech_key = os.environ.get("AZURE_SPEECH_KEY")
        speech_region = os.environ.get("AZURE_SPEECH_REGION")
        
        if not speech_key or not speech_region:
            logger.error("Azure Speech credentials not configured")
            return jsonify({"error": "Azure Speech service not configured"}), 500

        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join('static', 'audio', filename)
        
        # Generate SSML with voice and style
        ssml = generate_ssml(text, voice_name, style_value)
        
        # Configure speech synthesizer
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
        
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            # Configure audio output to file
            file_config = speechsdk.audio.AudioOutputConfig(filename=temp_file.name)
            
            # Create the speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)
            
            # Generate speech from SSML
            result = speech_synthesizer.speak_ssml_async(ssml).get()
            
            # Check if synthesis was successful
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Speech synthesized for {len(text)} chars using {voice_name}")
                
                # Copy from temp file to static directory
                import shutil
                shutil.copy(temp_file.name, filepath)
                
                # Return the audio URL
                return jsonify({
                    "audio_url": f"/static/audio/{filename}",
                    "voice_type": voice_type,
                    "style": style
                })
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                logger.error(f"Error details: {cancellation_details.error_details}")
                return jsonify({"error": f"Azure TTS error: {cancellation_details.error_details}"}), 500
            else:
                logger.error(f"Speech synthesis failed with reason: {result.reason}")
                return jsonify({"error": "Speech synthesis failed"}), 500
            
    except Exception as e:
        logger.error(f"Error in Azure TTS: {str(e)}")
        return jsonify({"error": str(e)}), 500

@azure_tts_bp.route('/api/azure-voices', methods=['GET'])
def get_azure_voices():
    """
    Return the available Azure voices and styles.
    """
    try:
        return jsonify({
            "voices": {k: v['description'] for k, v in AZURE_VOICES.items()},
            "styles": {k: v['description'] for k, v in VOICE_STYLES.items()}
        })
    except Exception as e:
        logger.error(f"Error getting Azure voices: {str(e)}")
        return jsonify({"error": str(e)}), 500
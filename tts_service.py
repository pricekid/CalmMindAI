"""
Text-to-speech service using gTTS (Google Text-to-Speech).
This service provides better quality speech synthesis than browser-based solutions.
"""
import os
import uuid
import re
from gtts import gTTS
from flask import url_for, current_app

# Create static audio directory if it doesn't exist
def ensure_audio_directory():
    """Ensure the audio directory exists"""
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
    return audio_dir

def clean_text_for_tts(text):
    """
    Clean and prepare text for TTS by adding appropriate pauses and emphasis.
    """
    # Strip HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Add pauses at sentence boundaries for more natural speech
    text = re.sub(r'(\.\s+)', '. ', text)  # period + space replaced with period + pause
    text = re.sub(r'(\?\s+)', '? ', text)  # question mark + space replaced with question mark + pause
    text = re.sub(r'(!\s+)', '! ', text)   # exclamation + space replaced with exclamation + pause
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def text_to_speech(text, language='en', slow=False):
    """
    Convert text to speech using gTTS and save as an audio file.
    
    Args:
        text: Text to convert to speech
        language: Language code (default: 'en')
        slow: Whether to speak slowly (default: False)
        
    Returns:
        URL to the generated audio file
    """
    # Clean text for better TTS
    text = clean_text_for_tts(text)
    
    # Generate a unique filename
    audio_dir = ensure_audio_directory()
    filename = f"tts_{uuid.uuid4()}.mp3"
    filepath = os.path.join(audio_dir, filename)
    
    try:
        # Generate TTS audio file
        tts = gTTS(text=text, lang=language, slow=slow)
        tts.save(filepath)
        
        # Return URL to the audio file
        return url_for('static', filename=f'audio/{filename}')
        
    except Exception as e:
        current_app.logger.error(f"Error generating TTS: {str(e)}")
        return None

def get_available_languages():
    """
    Get available languages for gTTS.
    
    Returns:
        Dictionary of language codes and names
    """
    from gtts.lang import tts_langs
    return tts_langs()
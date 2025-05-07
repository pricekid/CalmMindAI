"""
Direct test script for the OpenAI followup response that bypasses the app context.
This tests the fix for the OpenAI response_format parameter that requires "json" in the prompt.
"""

import os
import json
import logging
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_openai_api_key():
    """Get the OpenAI API key from environment"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No OpenAI API key found in environment")
    return api_key

def get_openai_client():
    """Get a fresh OpenAI client with the current API key"""
    return OpenAI(api_key=get_openai_api_key())

def test_followup_mode():
    """Test the followup mode functionality"""
    logger.info("Testing followup mode")
    
    # Sample journal text and reflection
    journal_text = "I've been feeling really anxious lately about my work situation. My boss keeps giving me more projects even though I'm already overwhelmed. I don't know how to say no without looking like I'm not a team player."
    reflection_prompt = "What might be driving your reluctance to set boundaries at work?"
    
    # User's reflection response to the initial prompt
    user_reflection = "I think I'm afraid of disappointing people. I always want to be seen as reliable and competent, so I take on more than I can handle."
    
    # Now test the followup mode
    followup_prompt = f"""
Journal entry: {journal_text}
Initial reflection prompt: {reflection_prompt}
User reflection response: {user_reflection}

Please provide a thoughtful followup that acknowledges the user's reflection and offers deeper insight.
"""
    
    # Get the OpenAI client
    client = get_openai_client()
    
    # Test with the new approach for followup mode
    logger.info("Making followup API call with JSON mention in system message")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are Mira, a warm, emotionally intelligent CBT-based coach. Provide a thoughtful followup response in JSON format."},
            {"role": "user", "content": followup_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=1500
    )
    
    # Get and log the response content
    content = response.choices[0].message.content
    logger.info(f"Raw OpenAI response content: {content}")
    
    # Try to parse the JSON response
    try:
        result = json.loads(content)
        logger.info(f"Successfully parsed JSON response")
        logger.info(f"Response structure: {json.dumps(result, indent=2)}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Raw content: {content}")
        return None

if __name__ == "__main__":
    test_followup_mode()
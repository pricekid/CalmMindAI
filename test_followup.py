"""
Test script for the followup response functionality in journal_service.py
This tests the fix for the OpenAI response_format parameter that requires "json" in the prompt.
"""

import os
import json
import logging
from journal_service import analyze_journal_with_gpt

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_followup_mode():
    """Test the followup mode functionality"""
    logger.info("Testing followup mode")
    
    # Sample journal text and reflection
    journal_text = "I've been feeling really anxious lately about my work situation. My boss keeps giving me more projects even though I'm already overwhelmed. I don't know how to say no without looking like I'm not a team player."
    
    # First, get the initial analysis
    initial_response = analyze_journal_with_gpt(
        journal_text=journal_text,
        anxiety_level=7,
        user_id=1,
        mode="initial"
    )
    
    # Print the initial response
    logger.info("Initial response received")
    if "structured_data" in initial_response:
        reflection_prompt = initial_response["structured_data"].get("reflection_prompt", "")
        logger.info(f"Reflection prompt: {reflection_prompt}")
    
    # User's reflection response to the initial prompt
    user_reflection = "I think I'm afraid of disappointing people. I always want to be seen as reliable and competent, so I take on more than I can handle."
    
    # Now test the followup mode
    followup_prompt = f"""
Journal entry: {journal_text}
Initial reflection prompt: {reflection_prompt}
User reflection response: {user_reflection}

Please provide a thoughtful followup that acknowledges the user's reflection and offers deeper insight.
"""
    
    # Get the followup response
    followup_response = analyze_journal_with_gpt(
        journal_text=followup_prompt,
        anxiety_level=7,
        user_id=1,
        mode="followup"
    )
    
    # Print the followup response
    logger.info("Followup response received")
    logger.info(f"Response structure: {json.dumps(followup_response, indent=2)}")
    
    return followup_response

if __name__ == "__main__":
    test_followup_mode()
"""
Simplified journal analysis service that focuses on reliability over feature completeness.
This more robust implementation is designed to ensure journal entries always save, even if 
the AI analysis component encounters problems.
"""
import os
import json
import logging
import traceback
from datetime import datetime
from openai import OpenAI

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_openai_api_key():
    """Get the OpenAI API key from environment"""
    return os.environ.get("OPENAI_API_KEY")

def get_simplified_analysis(journal_text, anxiety_level):
    """
    Simplified analysis function that prioritizes reliability.
    Will return a valid response structure even if API calls fail.
    
    Args:
        journal_text: The content of the journal entry
        anxiety_level: The anxiety level reported by the user (1-10)
        
    Returns:
        Dictionary with gpt_response, cbt_patterns and any error information
    """
    # Default response in case of failure
    default_response = {
        "gpt_response": "Thank you for sharing your journal entry. I've read it and appreciate your honesty.\n\nWarmly,\nCoach Mira",
        "cbt_patterns": [{
            "pattern": "Journal Received",
            "description": "Your journal entry has been saved successfully.",
            "recommendation": "Continue your journaling practice to build insight."
        }],
        "structured_data": None,
        "error": False
    }
    
    # Handle empty content
    if not journal_text or len(journal_text.strip()) < 10:
        logger.warning("Journal text too short for analysis")
        default_response["gpt_response"] = "I see you've started a journal entry. When you're ready to share more of your thoughts, I'll be here to offer insights.\n\nWarmly,\nCoach Mira"
        return default_response
    
    # Check for API key
    api_key = get_openai_api_key()
    if not api_key:
        logger.error("No OpenAI API key found")
        default_response["error"] = True
        default_response["error_type"] = "config"
        return default_response
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Build a simple prompt for analyzing the journal
        prompt = f"""
Journal Entry: {journal_text}

Anxiety Level (1-10): {anxiety_level}

Analyze this journal entry with compassion. Identify thought patterns and provide gentle CBT-based strategies.
"""
        
        # Set a reasonable timeout to avoid hanging the application
        try:
            # Make a simpler API call with conservative settings
            response = client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                messages=[
                    {"role": "system", "content": "You are Mira, a compassionate therapist using CBT techniques. Focus on validating feelings and providing practical advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,  # Limit tokens for faster response
                timeout=30  # Conservative timeout
            )
            
            # Extract response content
            analysis_text = response.choices[0].message.content
            
            # Return successful response
            return {
                "gpt_response": analysis_text,
                "cbt_patterns": [{
                    "pattern": "Journal Analysis",
                    "description": "Your journal entry has been analyzed.",
                    "recommendation": "Review the insights to better understand your thought patterns."
                }],
                "structured_data": None,
                "error": False
            }
            
        except Exception as api_error:
            # Log the error details
            logger.error(f"API error: {str(api_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Create a user-friendly error type
            error_msg = str(api_error).lower()
            if "timeout" in error_msg:
                error_type = "timeout"
            elif "rate limit" in error_msg:
                error_type = "rate_limit"
            else:
                error_type = "api"
                
            # Return error response that still allows the journal to be saved
            return {
                "gpt_response": "Thank you for sharing your thoughts. Your journal has been saved successfully, but I wasn't able to provide insights at this moment. Please check back later.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "Processing Delay",
                    "description": "Your journal entry has been saved successfully.",
                    "recommendation": "Analysis will be available when our system is less busy."
                }],
                "structured_data": None,
                "error": True,
                "error_type": error_type
            }
                
    except Exception as e:
        # Catch all other exceptions
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Still return a valid response structure
        default_response["error"] = True
        default_response["error_type"] = "unknown"
        return default_response
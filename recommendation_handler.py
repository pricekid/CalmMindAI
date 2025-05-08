"""
Recommendation handler utility for different response formats.
This handles the 'recommendation' field error that occurs with different response formats.
"""

import logging
import json

logger = logging.getLogger(__name__)

def safe_process_pattern(pattern):
    """
    Safely process a pattern from the OpenAI response, handling different formats.
    
    Args:
        pattern: The pattern object from the response (dict, string, or other)
        
    Returns:
        tuple: (pattern_name, recommendation_text)
    """
    try:
        # Add detailed logging for pattern format diagnosis
        logger.debug(f"Processing pattern of type: {type(pattern)}")
        if isinstance(pattern, dict):
            logger.debug(f"Pattern keys: {list(pattern.keys())}")
        elif isinstance(pattern, str):
            # For string patterns, check if it might be a JSON string
            if pattern.startswith('{') and pattern.endswith('}'):
                try:
                    parsed = json.loads(pattern)
                    logger.debug(f"Successfully parsed JSON string pattern: {list(parsed.keys())}")
                    pattern = parsed
                except json.JSONDecodeError:
                    logger.debug(f"String pattern is not valid JSON: {pattern[:50]}...")
            else:
                logger.debug(f"Simple string pattern: {pattern[:50]}...")
        else:
            logger.debug(f"Unknown pattern type: {pattern}")
        
        # Check pattern type and extract information safely
        if isinstance(pattern, dict):
            # Get pattern name with fallback
            if "pattern" in pattern:
                pattern_name = pattern["pattern"]
            elif "title" in pattern:
                # New format might use "title" instead of "pattern"
                pattern_name = pattern["title"]
            else:
                # Search for any key that might be a pattern name
                potential_name_keys = ["name", "type", "cognitive_pattern", "thought_pattern"]
                for key in potential_name_keys:
                    if key in pattern:
                        pattern_name = pattern[key]
                        break
                else:
                    pattern_name = "Unknown Pattern"
            
            # Handle different response structures for recommendation text
            if "description" in pattern and "recommendation" in pattern:
                # Standard format
                recommendation_text = f"{pattern['description']} - {pattern['recommendation']}"
            elif "description" in pattern and "action_step" in pattern:
                # New format with action steps instead of recommendations
                recommendation_text = f"{pattern['description']} - {pattern['action_step']}"
            elif "description" in pattern:
                # Format with just description
                recommendation_text = pattern["description"]
            elif "action_step" in pattern:
                # Format with just action step
                recommendation_text = pattern["action_step"]
            elif "explanation" in pattern:
                # Another potential format
                recommendation_text = pattern["explanation"]
            else:
                # Default text for dict without expected fields
                recommendation_text = "See detailed analysis in journal entry"
        elif isinstance(pattern, str):
            # For simple string patterns in new API response format
            pattern_name = pattern
            recommendation_text = f"Cognitive pattern identified: {pattern}"
        else:
            # Fallback for unexpected data types
            pattern_name = "Unknown Pattern"
            recommendation_text = "See detailed analysis in journal entry"
            
        # Final safety check to ensure we have valid strings
        if not isinstance(pattern_name, str):
            pattern_name = str(pattern_name)
        if not isinstance(recommendation_text, str):
            recommendation_text = str(recommendation_text)
            
        return pattern_name, recommendation_text
    
    except Exception as e:
        logger.error(f"Error processing pattern: {str(e)}")
        return "Error Processing Pattern", "Encountered an error while analyzing this pattern"
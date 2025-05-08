"""
Recommendation handler utility for different response formats.
This handles the 'recommendation' field error that occurs with different response formats.
"""

import logging

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
        # Check pattern type and extract information safely
        if isinstance(pattern, dict):
            # Get pattern name with fallback
            pattern_name = pattern.get("pattern", "Unknown Pattern")
            
            # Handle different response structures
            if "description" in pattern and "recommendation" in pattern:
                # Standard format
                recommendation_text = f"{pattern['description']} - {pattern['recommendation']}"
            elif "description" in pattern:
                # Format with just description
                recommendation_text = pattern["description"]
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
            
        return pattern_name, recommendation_text
    
    except Exception as e:
        logger.error(f"Error processing pattern: {str(e)}")
        return "Error Processing Pattern", "Encountered an error while analyzing this pattern"
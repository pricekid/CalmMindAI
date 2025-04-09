import os
import json
import logging
from openai import OpenAI
from admin_utils import get_config
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client with a function to get the API key
def get_openai_api_key():
    """Get the OpenAI API key from environment or admin config"""
    # First try to get from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # If not in environment, try to get from admin config
    if not api_key:
        config = get_config()
        api_key = config.get("openai_api_key")
    
    return api_key

def get_openai_model():
    """Get the OpenAI model from admin config or use default"""
    config = get_config()
    return config.get("model", "gpt-4o")

def get_max_tokens():
    """Get the max tokens setting from admin config or use default"""
    config = get_config()
    return config.get("max_tokens", 800)

# Initialize client with function that will be called each time
def get_openai_client():
    return OpenAI(api_key=get_openai_api_key())

def analyze_journal_entry(journal_text, anxiety_level):
    """
    Analyze a journal entry using OpenAI GPT-4o to identify anxiety patterns
    and provide CBT-based recommendations.
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    do not change this unless explicitly requested by the user
    """
    try:
        # Get API key and model settings
        api_key = get_openai_api_key()
        model = get_openai_model()
        
        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            raise ValueError("OpenAI API key is missing. Please check your environment variables or admin settings.")
            
        prompt = f"""
        You are a therapist specializing in Cognitive Behavioral Therapy (CBT) for anxiety.
        
        Analyze the following journal entry where the user has reported an anxiety level of {anxiety_level}/10:
        
        "{journal_text}"
        
        Identify three thought patterns that might be contributing to anxiety, and provide three specific, actionable CBT techniques to help address them.
        
        Respond with a JSON object in this exact format:
        {{
            "thought_patterns": [
                {{
                    "pattern": "Identified thought pattern",
                    "description": "Brief explanation of the pattern",
                    "recommendation": "Specific CBT technique or exercise to address this pattern"
                }}
            ]
        }}
        
        Keep each recommendation concise, practical and directly actionable by the user.
        """
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a CBT therapist specializing in anxiety. Provide evidence-based advice."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # Parse the response with improved error handling
            try:
                # Get the raw response content and debug log it
                content = response.choices[0].message.content
                logger.debug(f"Raw OpenAI response content: {content}")
                
                # Parse the JSON with error handling
                result = json.loads(content)
                logger.debug(f"OpenAI analysis result: {result}")
                
                # Use get() with a default empty list to prevent KeyError
                thought_patterns = result.get("thought_patterns", [])
                
                # Validate that thought_patterns is actually a list
                if not isinstance(thought_patterns, list):
                    logger.warning("OpenAI result didn't contain a valid thought_patterns list")
                    thought_patterns = []
                    
                return thought_patterns
                
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error: {json_err}")
                # Return a fallback response when JSON parsing fails
                return [{
                    "pattern": "Journal Processing Error",
                    "description": "We couldn't fully analyze this entry due to a technical issue.",
                    "recommendation": "Your journal has been saved successfully. Try analyzing it again later."
                }]
            
        except Exception as api_error:
            # Log the specific API error
            error_details = str(api_error)
            if "insufficient_quota" in error_details or "429" in error_details:
                logger.error(f"OpenAI API quota exceeded: {error_details}")
                error_type = "API_QUOTA_EXCEEDED"
            elif "invalid_api_key" in error_details:
                logger.error(f"Invalid OpenAI API key: {error_details}")
                error_type = "INVALID_API_KEY"
            else:
                logger.error(f"OpenAI API error: {error_details}")
                error_type = "API_ERROR"
                
            # Re-raise with more context
            raise ValueError(f"{error_type}: {error_details}")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error analyzing journal entry: {error_msg}")
        
        # Check error types from the refined error handling
        if "API_QUOTA_EXCEEDED" in error_msg:
            return [{
                "pattern": "API Quota Exceeded",
                "description": "The AI analysis service is currently unavailable due to API usage limits.",
                "recommendation": "Your journal entry has been saved successfully. The AI analysis feature will be available once API quota is renewed."
            }]
        elif "INVALID_API_KEY" in error_msg:
            return [{
                "pattern": "API Configuration Issue",
                "description": "The AI analysis service is currently unavailable due to a configuration issue.",
                "recommendation": "Your journal entry has been saved successfully. Please contact the administrator to resolve this issue."
            }]
        else:
            return [{
                "pattern": "Error analyzing entry",
                "description": "We couldn't analyze your journal entry at this time.",
                "recommendation": "Please try again later or contact support if the problem persists."
            }]

def generate_journaling_coach_response(entry):
    """
    Generate a warm, supportive coaching response to a user's journal entry.
    Uses a more conversational, supportive tone that celebrates achievements
    and gently applies CBT techniques.
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    do not change this unless explicitly requested by the user
    """
    try:
        # Get API key and model settings
        api_key = get_openai_api_key()
        model = get_openai_model()
        max_tokens = get_max_tokens()
        
        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            raise ValueError("OpenAI API key is missing. Please check your environment variables or admin settings.")
        
        journal_text = entry.content
        anxiety_level = entry.anxiety_level
        title = entry.title
        
        prompt = f"""
        You are a warm, supportive CBT journaling coach named Mira. A user has just submitted this journal entry with a reported anxiety level of {anxiety_level}/10:

        '{journal_text}'

        Write a kind, thoughtful response that follows this exact structure:

        Begin with a personal acknowledgment: "I really appreciate you sharing this with me." Then immediately identify and celebrate positive aspects from their entry, such as: "I want to acknowledge the positive side of your journal entry: [specific positive aspect]. This shows you are [positive quality], which is truly admirable."

        Next, warmly explore their thought patterns: "Now, let's gently explore the thoughts and feelings you're experiencing. It seems like you're caught in a cycle of [pattern]. This pattern might be tied to a few cognitive distortions, such as:"

        Then list 2-3 specific cognitive distortions (all-or-nothing thinking, catastrophizing, etc.), numbered with clear explanations of how they appear in the person's situation.

        After that, offer practical CBT techniques: "Here are a few CBT techniques you might find helpful:" and list 3 techniques, numbered, with clear instructions for implementing each one.

        End with a reflection prompt: "Finally, here's a little prompt to help you reflect on a personal strength: [thoughtful question that encourages self-compassion]."

        Close warmly with: "Sending you warmth and encouragement as you navigate this journey. You're taking important steps toward finding balance in your life.

        Take care,
        Mira"

        Your response should read like a personal letter from a caring friend or coach. Use warm, empathetic language throughout. Avoid clinical or academic tone entirely.
        """
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are Mira, a CBT coach who writes in a warm, personal style like a supportive friend. Your responses feel like a kind letter, acknowledging positives before gently exploring cognitive patterns. Use a conversational, caring tone throughout. Follow instructions precisely for response structure. Always sign your messages as 'Mira.'"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            # Get the response content with error handling
            try:
                if not response.choices or not hasattr(response.choices[0], 'message'):
                    logger.error("Unexpected response format from OpenAI API")
                    return "Mira is experiencing some technical difficulties, but your journal has been saved. Thank you for sharing."
                
                coach_response = response.choices[0].message.content
                if not coach_response:
                    logger.error("Empty response content from OpenAI API")
                    return "Mira is here, but having trouble responding right now. Your journal has been saved."
                
                # Strip and apply tone check
                coach_response = coach_response.strip()
                coach_response = tone_check(coach_response)
                
                return coach_response
                
            except Exception as parse_error:
                logger.error(f"Error parsing OpenAI response: {parse_error}")
                return "Mira appreciates you sharing your thoughts. Your journal has been saved, though I'm having some technical difficulties with my response."
            
        except Exception as api_error:
            # Log the specific API error
            error_details = str(api_error)
            if "insufficient_quota" in error_details or "429" in error_details:
                logger.error(f"OpenAI API quota exceeded: {error_details}")
                error_type = "API_QUOTA_EXCEEDED"
            elif "invalid_api_key" in error_details:
                logger.error(f"Invalid OpenAI API key: {error_details}")
                error_type = "INVALID_API_KEY"
            else:
                logger.error(f"OpenAI API error: {error_details}")
                error_type = "API_ERROR"
                
            # Re-raise with more context
            raise ValueError(f"{error_type}: {error_details}")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating coach response: {error_msg}")
        
        # Provide different messages based on error type
        if "API_QUOTA_EXCEEDED" in error_msg:
            return "Hi, this is Mira. Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Mira believes that the act of journaling itself is a powerful tool for self-reflection and growth."
        elif "INVALID_API_KEY" in error_msg:
            return "This is Mira, and I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. Mira wants you to know that the practice of putting your thoughts into words is valuable in itself."
        else:
            return "Mira here. Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey. Your entry has been saved successfully."

def tone_check(response):
    """
    A simple function to ensure the coach's response maintains a warm, supportive tone.
    """
    # List of warm, encouraging phrases to potentially add if tone seems clinical
    warm_openers = [
        "Mira here! I really appreciate you sharing this with me. ",
        "This is Mira. Thank you for opening up about this. ",
        "Mira's thoughts: I'm so glad you're taking time to reflect on this. "
    ]
    
    # If the response seems too clinical or lacks warmth, add a warm opener
    if not any(phrase in response.lower() for phrase in ["thank you", "appreciate", "glad", "wonderful"]):
        import random
        response = random.choice(warm_openers) + response
    
    return response

def generate_coping_statement(anxiety_context):
    """
    Generate a personalized coping statement based on the user's anxiety context.
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    do not change this unless explicitly requested by the user
    """
    # First, provide a fallback statement in case we need it
    fallback_statement = "Mira suggests: Take a moment to breathe deeply. Remember that your thoughts don't define you, and this feeling will pass."
    
    # Safety check for empty context
    if not anxiety_context or anxiety_context.strip() == "":
        logger.warning("Empty anxiety context provided to generate_coping_statement")
        return fallback_statement
    
    try:
        # Get API key and model settings
        api_key = get_openai_api_key()
        model = get_openai_model()
        
        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            return fallback_statement
        
        prompt = f"""
        Create a short, personalized coping statement for someone experiencing anxiety about:
        
        "{anxiety_context}"
        
        The statement should be:
        1. Brief (1-2 sentences)
        2. Empowering
        3. Based on CBT principles
        4. Present-focused
        5. Realistic and grounding
        
        Return only the statement text, no quotation marks, JSON formatting, or additional commentary.
        Start with 'Mira suggests:' and then provide the coping statement.
        """
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            # Specifically NOT requesting JSON format for this plain text response
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are Mira, a CBT therapist specializing in anxiety. Generate brief coping statements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            # Get the response content with improved error handling
            try:
                # Check if we have a valid response
                if not response.choices or len(response.choices) == 0:
                    logger.error("No choices in OpenAI API response")
                    return fallback_statement
                
                # Check if choices[0] has a message attribute
                choice = response.choices[0]
                if not hasattr(choice, 'message') or choice.message is None:
                    logger.error("No message in OpenAI API response choice")
                    return fallback_statement
                
                # Check if message has content attribute
                if not hasattr(choice.message, 'content') or choice.message.content is None:
                    logger.error("No content in OpenAI API response message")
                    return fallback_statement
                
                # Get and clean the content
                content = choice.message.content.strip()
                if not content:
                    logger.error("Empty content in OpenAI API response")
                    return fallback_statement
                
                # Log for debugging
                logger.debug(f"Raw coping statement: {content}")
                
                # Ensure it starts with "Mira suggests:" if it doesn't already
                if not content.startswith("Mira suggests:") and not content.startswith("Mira's suggestion:"):
                    content = f"Mira suggests: {content}"
                
                # Return the final content
                return content
                
            except Exception as parse_error:
                logger.error(f"Error parsing OpenAI response: {parse_error}")
                return fallback_statement
            
        except Exception as api_error:
            # Log the specific API error
            error_details = str(api_error)
            logger.error(f"OpenAI API error: {error_details}")
            
            # No need to re-raise, just return the fallback
            return fallback_statement
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"General error generating coping statement: {error_msg}")
        return fallback_statement

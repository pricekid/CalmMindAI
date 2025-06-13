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
        You are a CBT therapist analyzing a journal entry (anxiety level: {anxiety_level}/10):
        
        "{journal_text}"
        
        Provide a complete analysis in JSON format:
        {{
            "thought_patterns": [
                {{"pattern": "Pattern name", "description": "Brief explanation", "recommendation": "CBT technique"}}
            ]
        }}
        
        Keep responses concise and actionable.
        """
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a CBT therapist. Provide brief, actionable advice."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=300
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
        
        # Determine sentiment based on anxiety level
        sentiment = "Joyful" if anxiety_level <= 2 else "Positive" if anxiety_level <= 4 else "Neutral" if anxiety_level <= 6 else "Concern" if anxiety_level <= 8 else "Distress"
        
        # Use the new system prompt
        system_prompt = """
You are Mira, an emotionally intelligent CBT-based journaling coach inside Calm Journey. Your goal is to help the user reflect on their emotional experiences in a compassionate, supportive, and directive way.

You will be given a journal entry and a sentiment label (e.g., Joyful, Positive, Neutral, Concern, Distress).

Return your output as a JSON object with two main sections:

---

1. **narrative_response** (for Mira's Insights - Listen tab)
A warm, natural-language reflection that reads like a kind journal coach. Include:
- A brief insight summarizing the journal's emotional tone
- A gentle reflection prompt that feels personal and non-repetitive
- A short closing affirmation

Avoid jargon. Do not include section titles. Write like a caring coach speaking directly to the user.

---

2. **structured_response** (for CBT Tools - Interact tab)
This is a breakdown of actionable insight using CBT principles. Only include sections if relevant:

- **insight_text**: Grounded summary of emotional or cognitive themes
- **reflection_prompt**: One specific, tailored question
- **thought_patterns**: List of clearly detected distortions (e.g., Filtering, Catastrophizing)
- **strategies**: List of helpful CBT-based techniques (briefly described)
- **templates**: Optional ready-to-use scripts (for self-expression or anxiety management)
- **relationship_questions**: Optional reflection questions for relational themes
- **followup_text**: Affirming encouragement to close

---

IMPORTANT INSTRUCTIONS:
- For Joyful or Positive entries, do NOT include thought_patterns or strategies unless clearly warranted. Focus on savoring and celebration.
- For Distress or Concern, use CBT gently but clearly.
- Do NOT repeat phrasing across sessions (e.g., "What expectation are you holding…").
- Everything must be clearly grounded in the user's actual journal entry.

Return your response in this exact format:
{
  "narrative_response": "...",
  "structured_response": {
    "insight_text": "...",
    "reflection_prompt": "...",
    "thought_patterns": [...],
    "strategies": [...],
    "templates": [...],
    "relationship_questions": [...],
    "followup_text": "..."
  }
}
Omit any fields that are not relevant or not supported by the journal.
"""
        
        # Using formatted prompt with sentiment assessment
        prompt = f"""
Please analyze the following journal entry with an anxiety level of {anxiety_level}/10 (sentiment: {sentiment}):

"{journal_text}"

Respond according to the system prompt instructions, providing both narrative_response and structured_response as described.
"""
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
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
            return "Hi, this is Mira. Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Mira believes that the act of journaling itself is a powerful tool for self-reflection and growth.\n\nWarmly,\nCoach Mira"
        elif "INVALID_API_KEY" in error_msg:
            return "This is Mira, and I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. Mira wants you to know that the practice of putting your thoughts into words is valuable in itself.\n\nWarmly,\nCoach Mira"
        else:
            return "Mira here. Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey. Your entry has been saved successfully.\n\nWarmly,\nCoach Mira"

def tone_check(response):
    """
    A more sophisticated function to ensure the coach's response maintains a warm, supportive, and
    conversational tone while always including the Coach Mira signature.
    """
    # List of warm, conversational openers to add if tone seems clinical or impersonal
    warm_openers = [
        "Mira here! I really appreciate you sharing this with me. ",
        "This is Mira. Thank you for opening up about this. ",
        "Mira's thoughts: I'm so glad you're taking time to reflect on this. ",
        "Hi there! Mira here. I'm really glad you shared this with me. ",
        "Hello from Mira! I value the trust you've placed in me by sharing this. ",
        "Hey, it's Mira. I want you to know I really hear what you're saying. "
    ]
    
    # Conversational phrases to potentially inject if content feels too clinical
    conversational_elements = [
        " (I've been there too) ",
        " (and that's completely understandable) ",
        " (which is so important) ",
        " (and I'm here with you) ",
        " (I see you) ",
        " (and that takes real courage) "
    ]
    
    # If the response seems too clinical or lacks warmth, add a warm opener
    if not any(phrase in response.lower() for phrase in ["thank you", "appreciate", "glad", "wonderful", "mira here", "this is mira"]):
        import random
        response = random.choice(warm_openers) + response
    
    # Make the response more conversational by potentially adding parenthetical phrases
    # but only if the response is long enough and doesn't already seem conversational
    if len(response) > 200 and response.count("(") < 2 and response.count("I ") < 5:
        import random
        
        # Split into sentences
        sentences = response.split('.')
        if len(sentences) > 4:  # If we have enough sentences to work with
            # Choose 1-2 random spots to insert conversational elements
            insert_positions = random.sample(range(1, min(len(sentences)-1, 8)), min(2, len(sentences)//3))
            
            for pos in sorted(insert_positions, reverse=True):
                sentences[pos] = sentences[pos] + random.choice(conversational_elements)
            
            response = '.'.join(sentences)
    
    # Choose from different signature styles
    signatures = [
        "Warmly,\nCoach Mira",
        "I'm here for you,\nMira",
        "Cheering you on,\nMira",
        "With you on this journey,\nCoach Mira",
        "Believing in you,\nMira"
    ]
    
    # Add signature if it doesn't already exist
    if not any(sig in response for sig in signatures):
        import random
        if not response.endswith("\n\n"):
            response += "\n\n"
        response += random.choice(signatures)
    
    return response

def generate_insightful_message(mood):
    """
    Generate an insightful, personalized message based on the user's mood during onboarding.
    This provides the "last_feedback" message shown in the alert box.
    
    Args:
        mood: The user's reported mood (very_anxious, anxious, neutral, calm, great)
        
    Returns:
        String containing an insightful message about thought patterns
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    do not change this unless explicitly requested by the user
    """
    # First, provide a fallback message in case we need it
    fallback_messages = [
        "It's okay to feel overwhelmed. The first step is noticing the thought.",
        "You're not alone in feeling this way. Let's explore what that thought is telling you.",
        "Anxious thoughts can feel very real, but they're not always true.",
        "This moment will pass. Let's focus on what's in your control.",
        "Your thoughts might be distorted—would you like to reframe one together tomorrow?"
    ]
    import random
    fallback_message = random.choice(fallback_messages)
    
    try:
        # Get API key and model settings
        api_key = get_openai_api_key()
        model = get_openai_model()
        
        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            return fallback_message
        
        # Translate mood to a more descriptive form
        mood_descriptions = {
            'very_anxious': "feeling very anxious",
            'anxious': "feeling anxious",
            'neutral': "feeling neutral",
            'calm': "feeling calm",
            'great': "feeling great"
        }
        mood_description = mood_descriptions.get(mood, "with their current mood")
        
        prompt = f"""
        Create a single insightful sentence for someone who is {mood_description} and starting a mental wellness journaling practice.
        
        The sentence should:
        1. Be brief (1 sentence only)
        2. Acknowledge their current emotional state
        3. Contain a gentle CBT insight about thoughts vs. reality
        4. Be encouraging and warm
        
        Examples:
        - "It's okay to feel overwhelmed. The first step is noticing the thought."
        - "Anxious thoughts can feel very real, but they're not always true."
        - "This moment will pass. Let's focus on what's in your control."
        
        Return only the sentence, no quotation marks or additional text.
        """
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You create brief, insightful CBT messages for people beginning their mental wellness journey."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            # Get the response content with error handling
            try:
                if not response.choices or not hasattr(response.choices[0], 'message'):
                    logger.error("Unexpected response format from OpenAI API")
                    return fallback_message
                
                message = response.choices[0].message.content
                if not message:
                    logger.error("Empty response content from OpenAI API")
                    return fallback_message
                
                # Strip and return
                return message.strip()
                
            except Exception as parse_error:
                logger.error(f"Error parsing OpenAI response: {parse_error}")
                return fallback_message
            
        except Exception as api_error:
            logger.error(f"OpenAI API error: {str(api_error)}")
            return fallback_message
            
    except Exception as e:
        logger.error(f"Error generating insightful message: {str(e)}")
        return fallback_message

def generate_onboarding_feedback(journal_content, mood):
    """
    Generate personalized CBT feedback for first-time users during onboarding.
    This function is specifically designed for the onboarding process and
    returns thoughtful, supportive CBT-style feedback for new users.
    
    Args:
        journal_content: The user's first journal entry
        mood: The user's reported mood (very_anxious, anxious, neutral, calm, great)
        
    Returns:
        String containing personalized CBT feedback
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    do not change this unless explicitly requested by the user
    """
    # First, provide a fallback feedback in case we need it
    fallback_feedback = "Thank you for sharing your thoughts. The practice of journaling is a powerful tool for self-reflection and emotional awareness. As you continue this journey, you'll likely notice patterns in your thinking and develop insights that can help you navigate challenging emotions."
    
    # Safety check for empty content
    if not journal_content or journal_content.strip() == "":
        logger.warning("Empty journal content provided to generate_onboarding_feedback")
        return fallback_feedback
    
    try:
        # Get API key and model settings
        api_key = get_openai_api_key()
        model = get_openai_model()
        
        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            return fallback_feedback
        
        # Translate mood to a more descriptive form
        mood_descriptions = {
            'very_anxious': "feeling very anxious",
            'anxious': "feeling anxious",
            'neutral': "feeling neutral",
            'calm': "feeling calm",
            'great': "feeling great"
        }
        mood_description = mood_descriptions.get(mood, "with the mood they described")
        
        prompt = f"""
        A person has just started using a mental wellness journaling app and shared their first journal entry. They indicated they are {mood_description}. Here's what they wrote:
        
        "{journal_content}"
        
        As a warm, supportive CBT therapist, provide personalized feedback that:
        1. Acknowledges their effort in beginning the journaling practice
        2. Offers 1-2 gentle insights about thought patterns that might be present
        3. Suggests 1-2 specific CBT techniques relevant to their entry
        4. Encourages continued reflection and journaling
        
        Keep your response to around 4-6 sentences total. Use warm, supportive language appropriate for someone beginning their mental wellness journey.
        """
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a warm, supportive CBT therapist specializing in beginner-friendly mental wellness guidance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            # Get the response content with error handling
            try:
                if not response.choices or not hasattr(response.choices[0], 'message'):
                    logger.error("Unexpected response format from OpenAI API")
                    return fallback_feedback
                
                feedback = response.choices[0].message.content
                if not feedback:
                    logger.error("Empty response content from OpenAI API")
                    return fallback_feedback
                
                # Strip and return
                return feedback.strip()
                
            except Exception as parse_error:
                logger.error(f"Error parsing OpenAI response: {parse_error}")
                return fallback_feedback
            
        except Exception as api_error:
            logger.error(f"OpenAI API error: {str(api_error)}")
            return fallback_feedback
            
    except Exception as e:
        logger.error(f"Error generating onboarding feedback: {str(e)}")
        return fallback_feedback

def generate_coping_statement(anxiety_context):
    """
    Generate a personalized coping statement based on the user's journal content.
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    do not change this unless explicitly requested by the user
    """
    # First, provide a fallback statement in case we need it
    fallback_statement = "Mira suggests: Take a moment to breathe deeply. Remember that your thoughts don't define you, and this feeling will pass.\n\nWarmly,\nCoach Mira"
    
    # Safety check for empty context
    if not anxiety_context or anxiety_context.strip() == "":
        logger.warning("Empty journal content provided to generate_coping_statement")
        return fallback_statement
    
    try:
        # Get API key and model settings
        api_key = get_openai_api_key()
        model = get_openai_model()
        
        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            return fallback_statement
        
        # Truncate long content directly to avoid extra API calls
        content_to_use = anxiety_context[:800] + "..." if len(anxiety_context) > 800 else anxiety_context
        
        prompt = f"""Create a brief coping statement for: "{content_to_use}"

Start with 'Mira suggests:' then:
- Name the emotion they're feeling
- Provide CBT reframing 
- Give one actionable step
- Be validating but gently challenging

Example: "Mira suggests: I sense you're feeling overwhelmed about this situation. Remember that uncertainty doesn't mean danger—your mind is trying to protect you. Take three deep breaths and write down one thing you can control today."""
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            # Specifically NOT requesting JSON format for this plain text response
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are Mira, a CBT therapist. Generate brief coping statements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=80
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
                
                # Add signature if it doesn't already exist
                if not "Warmly,\nCoach Mira" in content:
                    if not content.endswith("\n\n"):
                        content += "\n\n"
                    content += "Warmly,\nCoach Mira"
                
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

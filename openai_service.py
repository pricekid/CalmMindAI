import os
import json
import logging
from openai import OpenAI

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def analyze_journal_entry(journal_text, anxiety_level):
    """
    Analyze a journal entry using OpenAI GPT-4o to identify anxiety patterns
    and provide CBT-based recommendations.
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    do not change this unless explicitly requested by the user
    """
    try:
        # Check if API key is available
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set")
            raise ValueError("OpenAI API key is missing. Please check your environment variables.")
            
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
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a CBT therapist specializing in anxiety. Provide evidence-based advice."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            logger.debug(f"OpenAI analysis result: {result}")
            
            return result["thought_patterns"]
            
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
        # Check if API key is available
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set")
            raise ValueError("OpenAI API key is missing. Please check your environment variables.")
        
        journal_text = entry.content
        anxiety_level = entry.anxiety_level
        title = entry.title
        
        prompt = f"""
        You are a warm, supportive CBT journaling coach inside an app called Calm Journey. A user has just submitted this journal entry with title "{title}" and reported anxiety level of {anxiety_level}/10:

        "{journal_text}"

        First, if the entry expresses a positive event or achievement, begin with a sincere and specific celebration. Keep it human and encouraging.

        Then, gently apply Cognitive Behavioral Therapy (CBT) techniques to reflect on the user's thoughts. Identify any thought patterns (e.g., all-or-nothing thinking, catastrophizing, overgeneralization) and offer 2–3 practical, actionable CBT techniques the user can try.

        End with a calm daily prompt that helps the user reflect on a personal strength or inner value.

        Respond in a warm, structured, first-person tone as if you're writing back to the user directly.
        """
        
        # Attempt to make the API call with error handling
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a warm, empathetic journaling coach who uses CBT techniques to help users process their thoughts and feelings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            coach_response = response.choices[0].message.content.strip()
            # Simple tone check to ensure the response is warm and supportive
            coach_response = tone_check(coach_response)
            
            return coach_response
            
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
            return "Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Remember that the act of journaling itself is a powerful tool for self-reflection and growth."
        elif "INVALID_API_KEY" in error_msg:
            return "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself."
        else:
            return "Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey. Your entry has been saved successfully."

def tone_check(response):
    """
    A simple function to ensure the coach's response maintains a warm, supportive tone.
    """
    # List of warm, encouraging phrases to potentially add if tone seems clinical
    warm_openers = [
        "I really appreciate you sharing this with me. ",
        "Thank you for opening up about this. ",
        "I'm so glad you're taking time to reflect on this. "
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
    try:
        # Check if API key is available
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set")
            raise ValueError("OpenAI API key is missing. Please check your environment variables.")
        
        prompt = f"""
        Create a short, personalized coping statement for someone experiencing anxiety about:
        
        "{anxiety_context}"
        
        The statement should be:
        1. Brief (1-2 sentences)
        2. Empowering
        3. Based on CBT principles
        4. Present-focused
        5. Realistic and grounding
        
        Return only the statement text, no quotation marks or additional commentary.
        """
        
        # Attempt to make the API call with error handling
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a CBT therapist specializing in anxiety. Generate brief coping statements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
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
        logger.error(f"Error generating coping statement: {error_msg}")
        
        # Provide different messages based on error type
        if "API_QUOTA_EXCEEDED" in error_msg:
            return "I notice you're feeling anxious. While I can't generate a personalized statement right now due to API limits, remember that this feeling is temporary, and you have overcome challenges before."
        elif "INVALID_API_KEY" in error_msg:
            return "Take a deep breath. This moment is temporary, and you have the strength to handle what comes next."
        else:
            return "In this moment of anxiety, remember that you have the tools and strength within you to navigate through these feelings."

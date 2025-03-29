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
        
    except Exception as e:
        logger.error(f"Error analyzing journal entry: {str(e)}")
        return [{
            "pattern": "Error analyzing entry",
            "description": "We couldn't analyze your journal entry at this time.",
            "recommendation": "Please try again later or contact support if the problem persists."
        }]

def generate_coping_statement(anxiety_context):
    """
    Generate a personalized coping statement based on the user's anxiety context.
    """
    try:
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
        
    except Exception as e:
        logger.error(f"Error generating coping statement: {str(e)}")
        return "Take a deep breath. This moment is temporary, and you have the strength to handle it."

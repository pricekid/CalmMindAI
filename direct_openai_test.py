"""
Direct OpenAI test to verify the prompts used for multi-turn conversation.
This script uses OpenAI directly without importing any app modules.
"""

import json
import logging
import os
from datetime import datetime
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Sample test data
TEST_JOURNAL_ENTRY = """I've been feeling really anxious about my work situation lately. There's so much pressure to perform well, and I'm worried I might not meet expectations. Every time I think about the upcoming deadline, I feel my heart racing and my thoughts spiraling. I keep thinking that if I don't do a perfect job, everyone will think I'm incompetent and I might lose my position. I know rationally that one project won't define my entire career, but emotionally it feels like everything is riding on this."""

TEST_REFLECTION = """When I think about it more, I realize that I've always put a lot of pressure on myself to be perfect. I think it comes from my childhood when I felt I had to be the best at everything to get attention and approval. I notice that I often catastrophize situations, assuming the worst possible outcome will happen."""

TEST_FOLLOWUP_REFLECTION = """That's a really good point. I've never connected my need for perfectionism with my fear of abandonment before. I think I'm afraid that if I'm not valuable enough through my work, people will leave me or decide I'm not worth their time. Maybe I need to work on separating my self-worth from my productivity."""

def test_initial_prompt():
    """Test the initial analysis prompt for a journal entry"""
    logger.info("Testing initial journal analysis prompt...")
    
    # Create the initial prompt similar to what we use in analyze_journal_with_gpt
    prompt = f"""
    You are Mira, a warm, compassionate CBT journaling coach inside an app called Dear Teddy. 
    
    ## JOURNAL ENTRY:
    "{TEST_JOURNAL_ENTRY}"
    
    ## YOUR TASK:
    1. Validate specific emotions by naming them precisely (e.g., "neglected," "anxious," "unimportant") rather than using general statements
    2. Identify cognitive distortions with depth, connecting them to underlying emotional needs (need for safety, validation, connection)
    3. Offer practical, actionable steps including specific scripts or templates the user can directly apply
    4. Encourage meaningful self-reflection that identifies core emotional needs
    
    ## RESPONSE STRUCTURE: 
    You MUST create a response in three distinct parts:
    1. INSIGHT TEXT: Initial empathy with precise emotion labeling + gentle reframe (acknowledge specific emotions, highlight patterns, begin cognitive exploration)
    2. REFLECTION PROMPT: A single, focused question that explores relationship context or emotional needs (start with "Take a moment. ")
    3. FOLLOW-UP TEXT: Support and mini reframe with practical action steps (provide scripted language, validation and concrete behavioral guidance)
    
    ## TONE REQUIREMENTS:
    - Warm, empathetic, and professional yet conversational
    - Avoid vague reassurances; be specific and personalized
    - Balance validation with gentle challenge
    - Always offer a clear, actionable path forward
    
    IMPORTANT: You must respond with ONLY valid JSON in the exact format below.
    DO NOT add any text, commentary, or explanation outside the JSON structure.
    
    {{
        "insight_text": "Your empathetic initial response that specifically names emotions",
        "reflection_prompt": "Take a moment. What's one expectation you've been holding about this work situation that feels heavy?",
        "followup_text": "Your supportive follow-up that provides a specific script or practical exercise"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        if result and "insight_text" in result:
            logger.info("Initial analysis successful")
            logger.info(f"Insight text: {result['insight_text'][:100]}...")
            logger.info(f"Reflection prompt: {result.get('reflection_prompt', 'N/A')[:100]}...")
            return result
        else:
            logger.error("Failed to get proper initial analysis")
            return None
    except Exception as e:
        logger.error(f"Error in initial analysis: {str(e)}")
        return None

def test_followup_prompt(reflection):
    """Test the followup analysis with a user's reflection"""
    logger.info("Testing followup analysis with user reflection...")
    
    # Create the followup prompt similar to what we use in analyze_journal_with_gpt
    prompt = f"""
    You are Mira, a CBT-informed journaling guide in Dear Teddy. You've already responded to a journal entry with an emotional insight and reflection prompt. The user has now shared their answer.

    Original Journal Entry: 
    "{TEST_JOURNAL_ENTRY}"
    
    User's Reflection: 
    "{reflection}"

    Based on both the original journal entry and the user's follow-up, return a new, deeper prompt that helps them:
    - Explore their emotion
    - Reframe their thinking
    - Or consider a next step

    Do not repeat previous reflections. Stay grounded in their reply.
    Return your response in JSON:
    {{
        "followup_text": "Your thoughtful, empathetic response that builds on their reflection and offers a new insight or question"
    }}
    
    Keep your response concise (1-3 sentences), warm, and focused on deepening their insight.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        if result and "followup_text" in result:
            logger.info("Followup analysis successful")
            logger.info(f"Followup text: {result['followup_text'][:100]}...")
            return result
        else:
            logger.error("Failed to get proper followup analysis")
            return None
    except Exception as e:
        logger.error(f"Error in followup analysis: {str(e)}")
        return None

def test_second_followup(second_reflection):
    """Test a second round of followup with another user reflection"""
    logger.info("Testing second followup analysis...")
    
    # Create the second followup prompt
    prompt = f"""
    You are Mira, a CBT-informed journaling guide in Dear Teddy. The conversation has progressed through several reflections:

    Original Journal Entry: 
    "{TEST_JOURNAL_ENTRY}"
    
    First Reflection: 
    "{TEST_REFLECTION}"
    
    Second Reflection:
    "{second_reflection}"

    Based on this deepening conversation, offer a warm, validating response that acknowledges their insight about connecting perfectionism with fear of abandonment. Then provide a specific action step they can take.

    Return your response in JSON:
    {{
        "followup_text": "Your thoughtful, empathetic response that validates their insight and offers a specific action step"
    }}
    
    Keep your response warm, specific, and actionable.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        if result and "followup_text" in result:
            logger.info("Second followup analysis successful")
            logger.info(f"Second followup text: {result['followup_text'][:100]}...")
            return result
        else:
            logger.error("Failed to get proper second followup analysis")
            return None
    except Exception as e:
        logger.error(f"Error in second followup analysis: {str(e)}")
        return None

def main():
    """Run all the tests in sequence to simulate a conversation"""
    logger.info("Starting OpenAI direct reflection testing...")
    
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found in environment variables")
        return
    
    # Test initial journal analysis
    initial_result = test_initial_prompt()
    if not initial_result:
        logger.error("Initial analysis test failed")
        return
    
    # Test first followup with user reflection
    followup_result = test_followup_prompt(TEST_REFLECTION)
    if not followup_result:
        logger.error("Followup analysis test failed")
        return
    
    # Test second followup with another user reflection
    second_followup = test_second_followup(TEST_FOLLOWUP_REFLECTION)
    if not second_followup:
        logger.error("Second followup analysis test failed")
        return
    
    logger.info("All tests completed successfully")
    logger.info("\nConversation flow summary:")
    logger.info("1. User journal: " + TEST_JOURNAL_ENTRY[:50] + "...")
    if initial_result and "insight_text" in initial_result:
        logger.info("2. Teddy insight: " + initial_result["insight_text"][:50] + "...")
    if initial_result and "reflection_prompt" in initial_result:
        logger.info("3. Teddy prompt: " + initial_result["reflection_prompt"][:50] + "...")
    logger.info("4. User reflection: " + TEST_REFLECTION[:50] + "...")
    if followup_result and "followup_text" in followup_result:
        logger.info("5. Teddy followup: " + followup_result["followup_text"][:50] + "...")
    logger.info("6. User second reflection: " + TEST_FOLLOWUP_REFLECTION[:50] + "...")
    if second_followup and "followup_text" in second_followup:
        logger.info("7. Teddy final response: " + second_followup["followup_text"][:50] + "...")

if __name__ == "__main__":
    main()
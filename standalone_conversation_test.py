"""
Standalone test for the multi-turn conversation feature.
This script can be run directly to test the reflection functionality
without requiring HTTP requests.
"""

import json
import logging
from datetime import datetime
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to sys.path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the function to test
from journal_service import analyze_journal_with_gpt

# Test data
TEST_JOURNAL = """
I've been feeling really anxious about my work situation lately. There's so much pressure to perform well, and I'm worried I might not meet expectations. Every time I think about the upcoming deadline, I feel my heart racing and my thoughts spiraling. I keep thinking that if I don't do a perfect job, everyone will think I'm incompetent and I might lose my position. I know rationally that one project won't define my entire career, but emotionally it feels like everything is riding on this.
"""

TEST_REFLECTION = """
When I reflect on it more, I realize that I've always put a lot of pressure on myself to be perfect. I think it comes from my childhood when I felt I had to be the best at everything to get attention and approval. I notice that I often catastrophize situations, assuming the worst possible outcome will happen.
"""

TEST_FOLLOWUP_REFLECTION = """
That's a really good point. I've never connected my need for perfectionism with my fear of abandonment before. I think I'm afraid that if I'm not valuable enough through my work, people will leave me or decide I'm not worth their time. Maybe I need to work on separating my self-worth from my productivity.
"""

def print_formatted_json(data):
    """Print JSON data in a nicely formatted way"""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            print(data)
            return
            
    print(json.dumps(data, indent=2))

def main():
    """Run the test sequence"""
    logger.info("Starting standalone conversation test")
    
    # Step 1: Initial analysis
    logger.info("\n=== STEP 1: INITIAL ANALYSIS ===")
    try:
        initial_result = analyze_journal_with_gpt(
            journal_text=TEST_JOURNAL,
            anxiety_level=7,
            user_id=0,
            mode="initial"
        )
        
        logger.info("Initial Analysis Result:")
        print_formatted_json(initial_result)
        
        if "insight_text" in initial_result:
            insight_text = initial_result["insight_text"]
            reflection_prompt = initial_result.get("reflection_prompt", "")
            logger.info(f"Insight Text: {insight_text[:100]}...")
            logger.info(f"Reflection Prompt: {reflection_prompt[:100]}...")
        else:
            logger.error("Missing expected fields in initial result")
            return
            
    except Exception as e:
        logger.error(f"Error in initial analysis: {e}")
        return
        
    # Step 2: First followup with user reflection
    logger.info("\n=== STEP 2: FIRST FOLLOWUP ===")
    try:
        followup_result = analyze_journal_with_gpt(
            journal_text=f"{TEST_JOURNAL}\n\nUser Reflection: {TEST_REFLECTION}",
            anxiety_level=7, 
            user_id=0,
            mode="followup"
        )
        
        logger.info("Followup Analysis Result:")
        print_formatted_json(followup_result)
        
        if "followup_text" in followup_result:
            followup_text = followup_result["followup_text"]
            logger.info(f"Followup Text: {followup_text[:100]}...")
        else:
            logger.error("Missing expected fields in followup result")
            return
            
    except Exception as e:
        logger.error(f"Error in first followup: {e}")
        return
        
    # Step 3: Second followup with another user reflection
    logger.info("\n=== STEP 3: SECOND FOLLOWUP ===")
    try:
        second_followup_result = analyze_journal_with_gpt(
            journal_text=f"{TEST_JOURNAL}\n\nUser Reflection: {TEST_REFLECTION}\n\nSecond Reflection: {TEST_FOLLOWUP_REFLECTION}",
            anxiety_level=7,
            user_id=0,
            mode="followup"
        )
        
        logger.info("Second Followup Analysis Result:")
        print_formatted_json(second_followup_result)
        
        if "followup_text" in second_followup_result:
            second_followup_text = second_followup_result["followup_text"]
            logger.info(f"Second Followup Text: {second_followup_text[:100]}...")
        else:
            logger.error("Missing expected fields in second followup result")
            return
            
    except Exception as e:
        logger.error(f"Error in second followup: {e}")
        return
        
    # Test successful
    logger.info("\n=== TEST COMPLETE ===")
    logger.info("All tests completed successfully!")
    
    # Display conversation flow
    logger.info("\n=== CONVERSATION FLOW SUMMARY ===")
    logger.info("1. USER JOURNAL: " + TEST_JOURNAL[:100] + "...")
    logger.info("2. TEDDY INSIGHT: " + initial_result.get("insight_text", "")[:100] + "...")
    logger.info("3. TEDDY PROMPT: " + initial_result.get("reflection_prompt", "")[:100] + "...")
    logger.info("4. USER REFLECTION: " + TEST_REFLECTION[:100] + "...")
    logger.info("5. TEDDY FOLLOWUP: " + followup_result.get("followup_text", "")[:100] + "...")
    logger.info("6. USER SECOND REFLECTION: " + TEST_FOLLOWUP_REFLECTION[:100] + "...")
    logger.info("7. TEDDY SECOND FOLLOWUP: " + second_followup_result.get("followup_text", "")[:100] + "...")

if __name__ == "__main__":
    main()
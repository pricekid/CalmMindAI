"""
Direct test for the multi-turn reflection capability in analyze_journal_with_gpt.
This script tests the function directly without requiring a server or login.
"""

import json
import logging
from datetime import datetime
from journal_service import analyze_journal_with_gpt

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample test data
TEST_JOURNAL_ENTRY = """I've been feeling really anxious about my work situation lately. There's so much pressure to perform well, and I'm worried I might not meet expectations. Every time I think about the upcoming deadline, I feel my heart racing and my thoughts spiraling. I keep thinking that if I don't do a perfect job, everyone will think I'm incompetent and I might lose my position. I know rationally that one project won't define my entire career, but emotionally it feels like everything is riding on this."""

TEST_REFLECTION = """When I think about it more, I realize that I've always put a lot of pressure on myself to be perfect. I think it comes from my childhood when I felt I had to be the best at everything to get attention and approval. I notice that I often catastrophize situations, assuming the worst possible outcome will happen."""

TEST_FOLLOWUP_REFLECTION = """That's a really good point. I've never connected my need for perfectionism with my fear of abandonment before. I think I'm afraid that if I'm not valuable enough through my work, people will leave me or decide I'm not worth their time. Maybe I need to work on separating my self-worth from my productivity."""

def test_initial_analysis():
    """Test the initial analysis of a journal entry"""
    logger.info("Testing initial journal analysis...")
    
    try:
        result = analyze_journal_with_gpt(
            journal_text=TEST_JOURNAL_ENTRY,
            anxiety_level=7,
            user_id=1,  # Use a test user ID
            mode="initial"  # Explicitly set initial mode
        )
        
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

def test_followup_analysis(initial_journal, reflection):
    """Test the followup analysis with a user's reflection"""
    logger.info("Testing followup analysis with user reflection...")
    
    combined_text = f"{initial_journal}\n\nUser Reflection: {reflection}"
    
    try:
        result = analyze_journal_with_gpt(
            journal_text=combined_text,
            anxiety_level=7,
            user_id=1,  # Use a test user ID
            mode="followup"  # Use followup mode
        )
        
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

def test_second_followup(initial_journal, first_reflection, second_reflection):
    """Test a second round of followup with another user reflection"""
    logger.info("Testing second followup analysis...")
    
    # Combine the original journal, first reflection, and second reflection
    combined_text = f"{initial_journal}\n\nUser Reflection: {first_reflection}\n\nSecond Reflection: {second_reflection}"
    
    try:
        result = analyze_journal_with_gpt(
            journal_text=combined_text,
            anxiety_level=7,
            user_id=1,
            mode="followup"
        )
        
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
    logger.info("Starting direct reflection testing...")
    
    # Test initial journal analysis
    initial_result = test_initial_analysis()
    if not initial_result:
        logger.error("Initial analysis test failed")
        return
    
    # Test first followup with user reflection
    followup_result = test_followup_analysis(TEST_JOURNAL_ENTRY, TEST_REFLECTION)
    if not followup_result:
        logger.error("Followup analysis test failed")
        return
    
    # Test second followup with another user reflection
    second_followup = test_second_followup(
        TEST_JOURNAL_ENTRY, 
        TEST_REFLECTION,
        TEST_FOLLOWUP_REFLECTION
    )
    if not second_followup:
        logger.error("Second followup analysis test failed")
        return
    
    logger.info("All tests completed successfully")

if __name__ == "__main__":
    main()
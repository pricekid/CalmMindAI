"""
Direct test of the different prompts for reflection responses.
This script tests both the original and improved prompts to compare the output quality.
"""

import json
import logging
import os
import sys
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI API Setup
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Test data
JOURNAL_ENTRY = """I've been feeling really overwhelmed by how one-sided some of my relationships feel lately. I'm always the one checking in, making plans, and being there for others, but when I need support, it seems like no one notices. I understand everyone is busy with their own lives, but it's hard not to feel taken for granted. I don't want to be needy, but I wish someone would ask how I'm doing for once."""

USER_REFLECTION = """I just want to feel like someone would notice if I stopped trying. Sometimes I worry that if I didn't reach out first, these relationships would just fade away completely, and that makes me feel really unimportant."""

def test_original_prompt():
    """Test the original followup reflection prompt"""
    logger.info("Testing ORIGINAL prompt format...")
    
    prompt = f"""
    You are Mira, a CBT-informed journaling guide. You've already responded to a journal entry with an emotional insight and reflection prompt. The user has now shared their answer.

    Original Journal Entry: 
    "{JOURNAL_ENTRY}"
    
    User's Reflection: 
    "{USER_REFLECTION}"

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
        
        result = response.choices[0].message.content
        logger.info(f"ORIGINAL prompt raw response: {result}")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(result)
            if "followup_text" in parsed:
                logger.info(f"ORIGINAL prompt followup_text: {parsed['followup_text']}")
            else:
                logger.warning(f"ORIGINAL prompt response missing followup_text key. Keys: {list(parsed.keys())}")
        except json.JSONDecodeError:
            logger.error("ORIGINAL prompt response is not valid JSON")
            
        return result
        
    except Exception as e:
        logger.error(f"Error testing original prompt: {str(e)}")
        return None

def test_enhanced_prompt():
    """Test the enhanced followup reflection prompt"""
    logger.info("Testing ENHANCED prompt format...")
    
    prompt = f"""
    You are Mira, a warm, emotionally intelligent journaling coach using CBT principles.

    You've already responded once to a user's journal entry with a reflection prompt. The user has now replied with their reflection.

    Original Journal Entry: 
    "{JOURNAL_ENTRY}"
    
    User's Reflection: 
    "{USER_REFLECTION}"

    Your task is to continue the conversation with a deeper, emotionally aware follow-up. Do not repeat the original insight or prompt. Do not be generic.

    Build specifically on what the user just revealed:
    - If they expressed sadness, acknowledge it and gently explore what's behind it.
    - If they revealed anger, invite a safe outlet or reframe.
    - If they showed resignation, ask what boundary or shift might protect them.
    - If they mentioned perfectionism, explore how it relates to their self-worth.
    - If they revealed fears of abandonment, connect this to their relationship patterns.
    - If they shared a vulnerability, honor it with validation and a thoughtful question.

    Return your response in JSON format with this structure:
    {{
      "followup_text": "Your thoughtful, empathetic response that builds on their reflection and offers a new insight or question"
    }}
    
    Use a warm, human tone and keep the response (1-3 sentences) specific to what they shared. Your response must clearly show you understood their reflection and are building on it meaningfully.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        logger.info(f"ENHANCED prompt raw response: {result}")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(result)
            if "followup_text" in parsed:
                logger.info(f"ENHANCED prompt followup_text: {parsed['followup_text']}")
            else:
                logger.warning(f"ENHANCED prompt response missing followup_text key. Keys: {list(parsed.keys())}")
        except json.JSONDecodeError:
            logger.error("ENHANCED prompt response is not valid JSON")
            
        return result
        
    except Exception as e:
        logger.error(f"Error testing enhanced prompt: {str(e)}")
        return None

def compare_results(original, enhanced):
    """Compare the results from the two prompts"""
    logger.info("====== COMPARISON ======")
    
    try:
        original_json = json.loads(original) if original else {}
        enhanced_json = json.loads(enhanced) if enhanced else {}
        
        original_text = original_json.get("followup_text", "N/A")
        enhanced_text = enhanced_json.get("followup_text", "N/A")
        
        logger.info("ORIGINAL response:")
        logger.info(original_text)
        logger.info("")
        logger.info("ENHANCED response:")
        logger.info(enhanced_text)
        
        # More detailed quality check
        specificity_words = [
            "you mentioned", "you shared", "you expressed", "you felt", "you're feeling", 
            "your reflection", "you noted", "you described", "you indicated", 
            "notice if", "stopped trying", "unimportant", "reaching out", "painful",
            "importance", "solely", "efforts", "step back", "true nature", "relationships",
            "feel valued", "reciprocation", "mutual support", "balanced", "dynamic"
        ]
        
        emotional_depth_words = [
            "painful", "vulnerable", "hurt", "neglected", "abandoned", "lonely", "dismissed",
            "unappreciated", "validation", "connection", "importance", "valued", "worthy",
            "meaningful", "fear", "anxiety", "worry", "sad", "disappointed", "frustrated"
        ]
        
        relationship_pattern_words = [
            "relationship pattern", "dynamic", "connection", "interaction", "communication",
            "give and take", "reciprocity", "mutual", "one-sided", "imbalance", "effort"
        ]
        
        # Check for specificity and relevance to the user's reflection
        original_specificity = sum(1 for word in specificity_words if word.lower() in original_text.lower())
        enhanced_specificity = sum(1 for word in specificity_words if word.lower() in enhanced_text.lower())
        
        # Check for emotional depth
        original_emotional = sum(1 for word in emotional_depth_words if word.lower() in original_text.lower())
        enhanced_emotional = sum(1 for word in emotional_depth_words if word.lower() in enhanced_text.lower())
        
        # Check for relationship pattern insights
        original_pattern = sum(1 for word in relationship_pattern_words if word.lower() in original_text.lower())
        enhanced_pattern = sum(1 for word in relationship_pattern_words if word.lower() in enhanced_text.lower())
        
        logger.info(f"Quality metrics (higher is better):")
        logger.info(f"ORIGINAL - Specificity: {original_specificity}, Emotional depth: {original_emotional}, Relationship insights: {original_pattern}")
        logger.info(f"ENHANCED - Specificity: {enhanced_specificity}, Emotional depth: {enhanced_emotional}, Relationship insights: {enhanced_pattern}")
        
        # Overall score
        original_total = original_specificity + original_emotional + original_pattern
        enhanced_total = enhanced_specificity + enhanced_emotional + enhanced_pattern
        logger.info(f"TOTAL SCORE - ORIGINAL: {original_total}, ENHANCED: {enhanced_total}")
        
    except Exception as e:
        logger.error(f"Error comparing results: {str(e)}")

def main():
    """Run the prompt comparison test"""
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found in environment")
        return
        
    logger.info("Starting reflection prompt comparison test...")
    
    # Test both prompts
    original_result = test_original_prompt()
    enhanced_result = test_enhanced_prompt()
    
    # Compare the results
    compare_results(original_result, enhanced_result)
    
    logger.info("Test completed")

if __name__ == "__main__":
    main()
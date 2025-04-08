import os
import json
import logging
from datetime import datetime
from openai import OpenAI
from admin_utils import get_config
import os
from typing import List, Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Define data directory and journals file path
DATA_DIR = "data"
JOURNALS_FILE = os.path.join(DATA_DIR, "journals.json")

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

def get_openai_client():
    return OpenAI(api_key=get_openai_api_key())

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def ensure_journals_file():
    """Ensure the journals.json file exists with valid JSON"""
    ensure_data_directory()
    if not os.path.exists(JOURNALS_FILE):
        with open(JOURNALS_FILE, 'w') as f:
            json.dump([], f)
    else:
        # Verify that the file contains valid JSON
        try:
            with open(JOURNALS_FILE, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted, reset it
            with open(JOURNALS_FILE, 'w') as f:
                json.dump([], f)

def get_journal_entries_for_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all journal entries for a specific user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        A list of journal entries
    """
    ensure_journals_file()
    with open(JOURNALS_FILE, 'r') as f:
        entries = json.load(f)
    
    # Filter entries for this user
    user_entries = [entry for entry in entries if entry.get('user_id') == user_id]
    # Sort by created_at in descending order
    user_entries.sort(key=lambda entry: entry.get('created_at', ''), reverse=True)
    
    return user_entries

def save_journal_entry(
    entry_id: int,
    user_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    anxiety_level: Optional[int] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
    is_analyzed: bool = False,
    gpt_response: Optional[str] = None,
    cbt_patterns: Optional[List[Dict[str, str]]] = None
) -> None:
    """
    Save a journal entry to the journals.json file.
    
    Args:
        entry_id: The ID of the journal entry
        user_id: The ID of the user
        title: The title of the journal entry
        content: The content of the journal entry
        anxiety_level: The anxiety level (1-10)
        created_at: The creation timestamp
        updated_at: The update timestamp
        is_analyzed: Whether the entry has been analyzed
        gpt_response: The GPT-generated response
        cbt_patterns: List of CBT patterns identified
    """
    logger.debug(f"Saving journal entry {entry_id} for user {user_id}")
    try:
        ensure_journals_file()
        
        with open(JOURNALS_FILE, 'r') as f:
            entries = json.load(f)
        
        # Convert datetime objects to ISO format strings
        created_at_str = created_at.isoformat() if isinstance(created_at, datetime) else created_at
        updated_at_str = updated_at.isoformat() if isinstance(updated_at, datetime) else updated_at
        
        # Clean up cbt_patterns to ensure it's a valid list
        clean_patterns = cbt_patterns if cbt_patterns else []
        
        # Check if we're updating an existing entry
        entry_found = False
        for i, entry in enumerate(entries):
            if entry.get('id') == entry_id and entry.get('user_id') == user_id:
                logger.debug(f"Updating existing journal entry {entry_id}")
                entries[i] = {
                    'id': entry_id,
                    'user_id': user_id,
                    'title': title,
                    'content': content,
                    'anxiety_level': anxiety_level,
                    'created_at': created_at_str,
                    'updated_at': updated_at_str,
                    'is_analyzed': is_analyzed,
                    'gpt_response': gpt_response,
                    'cbt_patterns': clean_patterns
                }
                entry_found = True
                break
        
        if not entry_found:
            # Entry not found, add a new one
            logger.debug(f"Adding new journal entry {entry_id}")
            entries.append({
                'id': entry_id,
                'user_id': user_id,
                'title': title,
                'content': content,
                'anxiety_level': anxiety_level,
                'created_at': created_at_str,
                'updated_at': updated_at_str,
                'is_analyzed': is_analyzed,
                'gpt_response': gpt_response,
                'cbt_patterns': clean_patterns
            })
        
        with open(JOURNALS_FILE, 'w') as f:
            json.dump(entries, f, indent=2)
            
        logger.debug(f"Successfully saved journal entry {entry_id}")
    except Exception as e:
        logger.error(f"Error saving journal entry to JSON file: {str(e)}")
        # Continue without failing the app - we already have DB record

def count_user_entries(user_id: int) -> int:
    """
    Count how many journal entries a user has submitted.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        The number of entries
    """
    return len(get_journal_entries_for_user(user_id))

def delete_journal_entry(entry_id: int, user_id: int) -> bool:
    """
    Delete a journal entry from the journals.json file.
    
    Args:
        entry_id: The ID of the journal entry to delete
        user_id: The ID of the user who owns the entry
        
    Returns:
        True if entry was found and deleted, False otherwise
    """
    logger.debug(f"Deleting journal entry {entry_id} for user {user_id} from JSON file")
    try:
        ensure_journals_file()
        
        with open(JOURNALS_FILE, 'r') as f:
            entries = json.load(f)
        
        # Filter out the entry to be deleted
        original_length = len(entries)
        entries = [entry for entry in entries if not (entry.get('id') == entry_id and entry.get('user_id') == user_id)]
        
        # Check if an entry was removed
        if len(entries) < original_length:
            logger.debug(f"Journal entry {entry_id} found and removed from JSON file")
            with open(JOURNALS_FILE, 'w') as f:
                json.dump(entries, f, indent=2)
            return True
        else:
            logger.debug(f"Journal entry {entry_id} not found in JSON file")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting journal entry from JSON file: {str(e)}")
        return False

def get_recurring_patterns(user_id: int, min_entries: int = 3) -> List[Dict[str, int]]:
    """
    Identify recurring thought patterns from a user's journal entries.
    Only returns patterns if the user has at least min_entries entries.
    
    Args:
        user_id: The ID of the user
        min_entries: Minimum number of entries required
    
    Returns:
        A list of dictionaries with pattern and count
    """
    entries = get_journal_entries_for_user(user_id)
    
    # Only analyze if user has enough entries
    if len(entries) < min_entries:
        return []
    
    # Extract all patterns from all entries
    all_patterns = []
    for entry in entries:
        patterns = entry.get('cbt_patterns', [])
        if patterns:
            for pattern in patterns:
                pattern_name = pattern.get('pattern')
                if pattern_name and pattern_name not in ["Error analyzing entry", "API Quota Exceeded", "API Configuration Issue"]:
                    all_patterns.append(pattern_name)
    
    # Count occurrences of each pattern
    pattern_counts = {}
    for pattern in all_patterns:
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    # Sort patterns by count (descending) and return top patterns
    sorted_patterns = [{"pattern": p, "count": c} for p, c in pattern_counts.items()]
    sorted_patterns.sort(key=lambda x: x["count"], reverse=True)
    
    return sorted_patterns[:3]  # Return top 3 patterns

def analyze_journal_with_gpt(journal_text: Optional[str] = None, anxiety_level: Optional[int] = None, user_id: int = 0) -> Dict[str, Any]:
    """
    Generate an improved AI analysis of a journal entry that's concise and focused.
    
    Args:
        journal_text: The journal entry text
        anxiety_level: Anxiety level (1-10)
        user_id: User ID for pattern analysis
        
    Returns:
        Dictionary with response and identified patterns
    """
    # Handle None or empty values
    safe_text = journal_text if journal_text else "No journal content provided"
    safe_anxiety = anxiety_level if anxiety_level is not None else 5  # Default to mid-level anxiety
    try:
        # Get API key and model settings
        api_key = get_openai_api_key()
        model = get_openai_model()
        
        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            raise ValueError("OpenAI API key is missing. Please check your environment variables or admin settings.")
        
        # Get count of user entries to determine if we should include pattern analysis
        entry_count = count_user_entries(user_id)
        include_patterns = entry_count >= 2  # We need at least 2 previous entries
        
        # Get recurring patterns if needed
        recurring_patterns_text = ""
        if include_patterns:
            recurring_patterns = get_recurring_patterns(user_id)
            if recurring_patterns:
                recurring_patterns_text = "Based on previous journal entries, these thought patterns appear frequently:\n"
                for pattern in recurring_patterns:
                    recurring_patterns_text += f"- {pattern['pattern']} (appeared {pattern['count']} times)\n"
        
        prompt = f"""
        You are a warm, supportive journaling coach in a mental health app called Calm Journey. 
        The user has submitted a journal entry with anxiety level {safe_anxiety}/10.
        
        JOURNAL ENTRY:
        "{safe_text}"
        
        {recurring_patterns_text if include_patterns else ''}
        
        RESPONSE GUIDELINES:
        1. Be concise! The entire response must be no more than 3 short paragraphs.
        2. Return two separate JSON elements:
           a) 'response': The supportive, warm response to the user
           b) 'patterns': A list of 1-2 CBT thought patterns identified
        
        FORMAT YOUR RESPONSE AS FOLLOWS:
        - First: A short positive reflection (1 paragraph, max 2-3 sentences)
        - Second: 1-2 CBT patterns or cognitive distortions with very brief explanations (bullet points)
        - Third: One simple, actionable suggestion or coping skill (1 line)
        
        AVOID:
        - Long reflections
        - Lengthy lists
        - Repeating the prompt
        - More than 3 short paragraphs total
        
        Respond with a JSON object in this exact format:
        {{
            "response": "The warm, concise response text with the 3 elements described above",
            "patterns": [
                {{
                    "pattern": "Name of CBT thought pattern 1",
                    "description": "2-sentence explanation",
                    "recommendation": "Brief, practical suggestion to address this pattern"
                }},
                {{
                    "pattern": "Name of CBT thought pattern 2 (optional)",
                    "description": "2-sentence explanation",
                    "recommendation": "Brief, practical suggestion to address this pattern"
                }}
            ]
        }}
        """
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a warm, empathetic journaling coach who uses CBT techniques to help users process their thoughts and feelings."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Format response to add recurring patterns analysis for users with 3+ entries
            coach_response = result["response"]
            recurring_patterns = get_recurring_patterns(user_id)
            if entry_count >= 3 and recurring_patterns:
                pattern_insight = "\n\nWe're starting to notice a few thought patterns in your journals. Here's what we're seeing:\n"
                for pattern in recurring_patterns[:2]:  # Limit to top 2
                    pattern_insight += f"- {pattern['pattern']}\n"
                coach_response += pattern_insight
            
            return {
                "gpt_response": coach_response,
                "cbt_patterns": result["patterns"]
            }
            
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
            return {
                "gpt_response": "Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Remember that the act of journaling itself is a powerful tool for self-reflection and growth.",
                "cbt_patterns": [{
                    "pattern": "API Quota Exceeded",
                    "description": "The AI analysis service is currently unavailable due to API usage limits.",
                    "recommendation": "Your journal entry has been saved successfully. The AI analysis feature will be available once API quota is renewed."
                }]
            }
        elif "INVALID_API_KEY" in error_msg:
            return {
                "gpt_response": "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself.",
                "cbt_patterns": [{
                    "pattern": "API Configuration Issue",
                    "description": "The AI analysis service is currently unavailable due to a configuration issue.",
                    "recommendation": "Your journal entry has been saved successfully. Please contact the administrator to resolve this issue."
                }]
            }
        else:
            return {
                "gpt_response": "Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey. Your entry has been saved successfully.",
                "cbt_patterns": [{
                    "pattern": "Error analyzing entry",
                    "description": "We couldn't analyze your journal entry at this time.",
                    "recommendation": "Please try again later or contact support if the problem persists."
                }]
            }
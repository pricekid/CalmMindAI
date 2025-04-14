import os
import json
import logging
from datetime import datetime
from openai import OpenAI
from admin_utils import get_config
import os
from typing import List, Dict, Any, Optional

# Set up logging with more details
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define data directory and journals file path
DATA_DIR = "data"
JOURNALS_FILE = os.path.join(DATA_DIR, "journals.json")

# Initialize OpenAI client with a function to get the API key
def get_openai_api_key():
    """Get the OpenAI API key from environment or admin config"""
    # First try to get from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # Log key source for debugging (sanitized)
    if api_key:
        logger.debug(f"Using OpenAI API key from environment variable (length: {len(api_key)})")
    else:
        # If not in environment, try to get from admin config
        config = get_config()
        admin_key = config.get("openai_api_key")
        if admin_key:
            logger.debug(f"Using OpenAI API key from admin config (length: {len(admin_key)})")
            api_key = admin_key
        else:
            logger.warning("No OpenAI API key found in environment or admin config")
    
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
        # Get API key and model settings with detailed logging
        api_key = get_openai_api_key()
        model = get_openai_model()
        
        # Log the configuration details (sanitized)
        if api_key:
            logger.debug(f"API key found (length: {len(api_key)}, starts with: {api_key[:3]}...)")
        else:
            logger.debug("No API key found in environment or admin settings")
            
        logger.debug(f"Using model: {model}")
        
        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            raise ValueError("INVALID_API_KEY: OpenAI API key is missing. Please check your environment variables or admin settings.")
        
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
        You are Mira, a warm, compassionate CBT journaling coach inside an app called Calm Journey. A user has just shared the following journal entry with an anxiety level of {safe_anxiety}/10:

        "{safe_text}"
        
        {recurring_patterns_text if include_patterns else ''}

        IMPORTANT: You must respond with valid JSON in the following format only:

        {{
            "response": "Your complete response text following the structure below",
            "patterns": [
                {{
                    "pattern": "Name of CBT thought pattern 1",
                    "description": "Brief explanation of the pattern",
                    "recommendation": "Specific CBT technique or exercise to address this pattern"
                }},
                {{
                    "pattern": "Name of CBT thought pattern 2",
                    "description": "Brief explanation of the pattern",
                    "recommendation": "Specific CBT technique or exercise to address this pattern"
                }}
            ]
        }}

        Your response (in the "response" field) should follow this therapeutic structure:

        1. **Emotional Validation**  
           - Begin by acknowledging the user's effort in opening up.  
           - Recognize and validate their emotional state with empathy.

        2. **Reflection & Clarification**  
           - Gently summarize what they're experiencing, showing understanding.

        3. **Identify Cognitive Distortions**  
           - Highlight 1–2 possible unhelpful thought patterns (e.g., catastrophizing, comparison trap, all-or-nothing thinking, emotional reasoning, mind reading).  
           - Use clear CBT terms with a short, plain explanation.

        4. **CBT Techniques to Try**  
           - Suggest 2 or 3 practical tools based on the journal content.  
           - Examples: thought reframing, behavioral experiments, thought records, gratitude practice, boundary setting, etc.  
           - Keep suggestions specific, supportive, and gentle.

        5. **Daily Reflection Prompt**  
           - End with a question or journal prompt that helps the user reflect on a strength, reframe a thought, or take small action.

        6. **Warm Close**  
           - Reassure the user they're doing valuable inner work.  
           - Use kind, non-clinical language.

        Tone: supportive, calm, human, non-judgmental. Use second person ("you"). Avoid generic lists or robotic tone. Write as if Mira is personally writing a thoughtful note back to the user.

        Respond directly to the journal content in a way that builds trust, insight, and emotional safety.
        
        Here's an example of the style and structure I want for the response field (adapt to the journal content):
        
        "I want to start by saying how common and valid your feelings are. Wanting to connect, yet fearing judgment, creates such an emotional tug-of-war — and your self-awareness in noticing that is truly a strength.

        It sounds like you're caught between two needs: the comfort of safety, and the desire to be seen and connected. That tension can be exhausting — especially when anxiety fills in the blanks with harsh predictions.

        Here are a few thought patterns that may be surfacing:

        Mind Reading: You're imagining others will find you awkward or boring — but is that something they've actually said, or something anxiety is projecting?
        Emotional Reasoning: Because you feel anxious, it feels like something bad will happen. But feelings aren't always facts.

        Here are a few gentle CBT strategies you could try:

        Behavioral Experiment: Could you go for just 20 minutes? This breaks the all-or-nothing loop and lets you test reality gently.
        Reframe the "what ifs": Instead of "What if I say something weird?", try "What if someone is glad I came?"
        Compassionate Voice: What would you say to a friend who was afraid of being judged at a gathering?

        And a little reflection for today:
        "What part of me wants connection right now — and what could I do to honor that gently?"

        You're doing meaningful inner work by just noticing this. One small step at a time is still forward."
        
        REMEMBER: Return ONLY valid JSON as described above, with no additional text or formatting.
        """
        
        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()
            
            # Log the API parameters for debugging
            logger.debug(f"Making OpenAI API call with model: {model}, API key (sanitized): {'*****' + api_key[-4:] if api_key else 'None'}")
            
            # Make the API call with explicit instructions to return JSON
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are Mira, writing as a warm, personable CBT journaling coach who works with anxiety. Your style is conversational, authentic, and never clinical. You write like you're having a one-on-one conversation with a friend who needs support. Use contractions, simple language, and specific examples relevant to the person's situation. Your responses should feel like they were written especially for this person, addressing their unique circumstances with warmth and understanding. ALWAYS RETURN VALID JSON FORMAT."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},  # Explicitly require JSON response
                temperature=0.7,
                max_tokens=1500  # Ensure we have enough tokens for the response
            )
            
            # Log successful API call
            logger.debug("OpenAI API call completed successfully")
            
            # Parse the response with improved error handling
            try:
                # Get the raw response content 
                content = response.choices[0].message.content
                logger.debug(f"Raw OpenAI response content: ")  # Don't log the full content as it might be too large
                
                # Parse the JSON with more robust error handling
                try:
                    # Safety trim in case the response is too large
                    if len(content) > 20000:
                        logger.warning(f"Response content is very large ({len(content)} chars), trimming for parsing")
                        content = content[:20000]
                    
                    # Sometimes the API returns content with non-JSON text before or after the JSON
                    # Try to extract just the JSON part using regex
                    import re
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                    
                    if json_match:
                        # Extract just the JSON part
                        json_content = json_match.group(1)
                        result = json.loads(json_content)
                        logger.debug("Successfully parsed JSON response using regex extraction")
                    else:
                        # If regex fails, try the full content
                        result = json.loads(content)
                        logger.debug("Successfully parsed JSON response from full content")
                except Exception as json_parse_error:
                    logger.error(f"Failed to parse JSON response: {str(json_parse_error)}")
                    
                    # Look for patterns that suggest it's a valid response but not in JSON format
                    if "warmly" in content.lower() or "coach mira" in content.lower():
                        # It seems to be a valid text response but not in JSON format
                        logger.info("Found valid text response but not in JSON format")
                        result = {
                            "response": content,
                            "patterns": [{
                                "pattern": "Journal Analysis",
                                "description": "Your journal entry has been analyzed.",
                                "recommendation": "Continue writing in your journal to develop insights into your thought patterns."
                            }]
                        }
                    else:
                        # Provide a default response format if parsing fails
                        result = {
                            "response": "Thank you for sharing your journal entry. I've read through your thoughts.",
                            "patterns": [{
                                "pattern": "Processing Limitation",
                                "description": "We encountered a technical issue analyzing your entry.",
                                "recommendation": "Your journal has been saved. The insights will be available soon."
                            }]
                        }
                
                # Format response to add recurring patterns analysis for users with 3+ entries
                # The API might return "response" or "content" keys depending on the model and format
                # Check for both and fall back to a default if neither is found
                coach_response = result.get("response", None)
                if coach_response is None or coach_response == "":
                    # Try alternate keys that might be returned by the API
                    coach_response = result.get("content", None)
                    if coach_response is None or coach_response == "":
                        coach_response = result.get("message", None)
                        if coach_response is None or coach_response == "":
                            # Ultimate fallback
                            coach_response = "Thank you for sharing your journal entry."
                
                # Log what we found to help debug
                logger.debug(f"After key checking, coach_response is {len(coach_response) if coach_response else 0} chars")
                
                recurring_patterns = get_recurring_patterns(user_id)
                
                if entry_count >= 3 and recurring_patterns:
                    pattern_insight = "\n\nWe're starting to notice a few thought patterns in your journals. Here's what we're seeing:\n"
                    for pattern in recurring_patterns[:2]:  # Limit to top 2
                        pattern_insight += f"- {pattern['pattern']}\n"
                    coach_response += pattern_insight
                
                # Add a sign-off by Coach Mira if not already present
                if "Coach Mira" not in coach_response:
                    coach_response += "\n\nWarmly,\nCoach Mira"
                
                # Ensure patterns is a valid list - check for both "patterns", "cbt_patterns", and "thought_patterns" 
                # since the API might use different property names
                cbt_patterns = result.get("patterns", None)
                if cbt_patterns is None or not isinstance(cbt_patterns, list) or len(cbt_patterns) == 0:
                    cbt_patterns = result.get("cbt_patterns", None)
                    if cbt_patterns is None or not isinstance(cbt_patterns, list) or len(cbt_patterns) == 0:
                        cbt_patterns = result.get("thought_patterns", [])
                if not isinstance(cbt_patterns, list) or len(cbt_patterns) == 0:
                    # Provide default patterns if none are available
                    cbt_patterns = [{
                        "pattern": "Journal Reflection",
                        "description": "Your journal entry has been saved.",
                        "recommendation": "Continue journaling regularly to build self-awareness."
                    }]
                
                # Return formatted results
                return {
                    "gpt_response": coach_response,
                    "cbt_patterns": cbt_patterns
                }
                
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error: {json_err}")
                # Provide a fallback response when JSON parsing fails
                return {
                    "gpt_response": "Thank you for sharing your journal entry. I've read through your thoughts, but am experiencing some technical difficulties in generating a detailed response.\n\nWarmly,\nCoach Mira",
                    "cbt_patterns": [{
                        "pattern": "Journal Processing Error",
                        "description": "We couldn't fully analyze this entry due to a technical issue.",
                        "recommendation": "Your journal has been saved successfully. Try analyzing it again later."
                    }]
                }
            
        except Exception as api_error:
            # Log the specific API error with detailed error handling
            error_details = str(api_error)
            logger.error(f"Full OpenAI API error details: {error_details}")
            
            if "insufficient_quota" in error_details or "429" in error_details:
                logger.error(f"OpenAI API quota exceeded: {error_details}")
                error_type = "API_QUOTA_EXCEEDED"
            elif "invalid_api_key" in error_details or "key" in error_details.lower():
                logger.error(f"Invalid OpenAI API key: {error_details}")
                error_type = "INVALID_API_KEY"
            elif "model" in error_details.lower():
                logger.error(f"OpenAI model error: {error_details}")
                error_type = "MODEL_ERROR"
            elif "timed out" in error_details.lower() or "timeout" in error_details.lower():
                logger.error(f"OpenAI API timeout: {error_details}")
                error_type = "API_TIMEOUT"
            elif "rate" in error_details.lower() and "limit" in error_details.lower():
                logger.error(f"OpenAI rate limit exceeded: {error_details}")
                error_type = "RATE_LIMIT_EXCEEDED"
            else:
                logger.error(f"OpenAI API error: {error_details}")
                error_type = "API_ERROR"
            
            # Try to create a fallback response before raising the error
            response_message = "Thank you for sharing your journal entry. I've read it but am experiencing some technical difficulties right now."
            
            # Re-raise with more context
            raise ValueError(f"{error_type}: {error_details}")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error analyzing journal entry: {error_msg}")
        
        # Check error types from the refined error handling with more specific messages
        if "API_QUOTA_EXCEEDED" in error_msg or "RATE_LIMIT_EXCEEDED" in error_msg:
            logger.warning("Rate limit or quota exceeded for OpenAI API")
            return {
                "gpt_response": "Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Remember that the act of journaling itself is a powerful tool for self-reflection and growth.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "API Quota Exceeded",
                    "description": "The AI analysis service is currently unavailable due to API usage limits.",
                    "recommendation": "Your journal entry has been saved successfully. The AI analysis feature will be available once API quota is renewed."
                }]
            }
        elif "INVALID_API_KEY" in error_msg:
            logger.warning("Invalid API key for OpenAI API")
            return {
                "gpt_response": "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "API Configuration Issue",
                    "description": "The AI analysis service is currently unavailable due to a configuration issue.",
                    "recommendation": "Your journal entry has been saved successfully. Please contact the administrator to resolve this issue."
                }]
            }
        elif "MODEL_ERROR" in error_msg:
            logger.warning("Model error for OpenAI API")
            return {
                "gpt_response": "Thank you for sharing your thoughts in this journal entry. Currently, our AI analysis feature is experiencing technical difficulties with the language model. Your entry has been saved, and we're working to resolve this issue.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "Model Configuration Issue",
                    "description": "The AI language model is currently unavailable.",
                    "recommendation": "Your journal entry has been saved successfully. Please try again later while we resolve this issue."
                }]
            }
        elif "API_TIMEOUT" in error_msg:
            logger.warning("Timeout error for OpenAI API")
            return {
                "gpt_response": "Thank you for sharing your journal entry today. It seems our AI coach is taking a bit longer than usual to respond. Your entry has been saved, and you're welcome to try again in a few moments.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "Connection Timeout",
                    "description": "The connection to our AI service timed out.",
                    "recommendation": "Your journal entry has been saved successfully. Please try again in a few minutes when network conditions may improve."
                }]
            }
        else:
            logger.warning(f"Unknown error for OpenAI API: {error_msg}")
            return {
                "gpt_response": "Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey. Your entry has been saved successfully.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "Error analyzing entry",
                    "description": "We couldn't analyze your journal entry at this time.",
                    "recommendation": "Please try again later or contact support if the problem persists."
                }]
            }
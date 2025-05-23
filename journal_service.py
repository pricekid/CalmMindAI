import os
import json
import logging
import re
from datetime import datetime
from openai import OpenAI
from admin_utils import get_config
from typing import List, Dict, Any, Optional

# Set up logging with more details
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define data directory and journals file path
DATA_DIR = "data"
JOURNALS_FILE = os.path.join(DATA_DIR, "journals.json")

# Define helper function for journal content summarization
def summarize_journal_content(content: str, max_length: int = 100) -> str:
    """
    Create a short summary of journal content.

    Args:
        content: The journal content to summarize
        max_length: Maximum length of summary

    Returns:
        Summarized content
    """
    if not content:
        return ""

    # Simple truncation with ellipsis for now
    if len(content) <= max_length:
        return content

    # Try to find a sentence break near the desired length
    # This gives a more natural summary
    end_pos = min(max_length, len(content))
    sentence_ends = ['.', '!', '?']

    for i in range(end_pos - 1, max(0, end_pos - 30), -1):
        if content[i] in sentence_ends:
            return content[:i+1] + "..."

    # No good sentence break found, just truncate
    return content[:max_length] + "..."

# Initialize OpenAI client with a function to get the API key
def get_openai_api_key():
    """Get the OpenAI API key from environment or admin config"""
    # First try to get from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")

    # Log key source for debugging (sanitized)
    if api_key:
        logger.debug(f"Using OpenAI API key from environment variable (length: {len(api_key)})")
        
        # Validate API key format
        if '@' in api_key and '.' in api_key:
            logger.warning(f"Environment OPENAI_API_KEY appears to be an email address ({api_key}), not a valid API key")
            api_key = None
        elif not (api_key.startswith('sk-') or api_key.startswith('org-')):
            logger.warning(f"Environment OPENAI_API_KEY has invalid format: starts with '{api_key[:10]}...'")
            # Try using a placeholder to test the validation
            api_key = None
    
    # If not in environment or invalid format, try to get from admin config
    if not api_key:
        config = get_config()
        admin_key = config.get("openai_api_key")
        if admin_key:
            logger.debug(f"Using OpenAI API key from admin config (length: {len(admin_key)})")
            # Validate admin API key format
            if '@' in admin_key or not admin_key.startswith('sk-'):
                logger.warning(f"Admin config API key has invalid format")
                admin_key = None
            api_key = admin_key
        
        if not api_key:
            logger.warning("No valid OpenAI API key found in environment or admin config")
            
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
    cbt_patterns: Optional[List[Dict[str, str]]] = None,
    structured_data: Optional[Dict] = None,
    user_reflection: Optional[str] = None
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
        structured_data: Structured data with distortions, strategies, and reflection prompts
        user_reflection: The user's reflection response to Mira's prompt
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
                    'cbt_patterns': clean_patterns,
                    'structured_data': structured_data,
                    'user_reflection': user_reflection
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
                'cbt_patterns': clean_patterns,
                'structured_data': structured_data,
                'user_reflection': user_reflection
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
    Uses the database to count entries directly instead of loading all entries from JSON.

    Args:
        user_id: The ID of the user

    Returns:
        The number of entries
    """
    try:
        # Import models here to avoid circular imports
        from models import JournalEntry
        
        # Count entries directly in the database
        entry_count = JournalEntry.query.filter(JournalEntry.user_id == user_id).count()
        logger.debug(f"Found {entry_count} entries for user {user_id} in database")
        return entry_count
    except Exception as e:
        # Log the error and fall back to JSON method
        logger.error(f"Error counting user entries from database: {str(e)}")
        logger.warning("Falling back to JSON-based entry counting")
        return len(get_journal_entries_for_user(user_id))

def detect_emotional_tone(text: str) -> Dict[str, Any]:
    """
    Detect the primary emotional tone of the journal entry.
    Simple keyword-based approach for lightweight processing.

    Args:
        text: The journal entry text

    Returns:
        Dictionary with detected emotional tones and confidence levels
    """
    # Initialize emotion categories with common keywords
    emotions = {
        "anger": ["angry", "furious", "mad", "irritated", "outraged", "annoyed", "frustrated", "enraged"],
        "sadness": ["sad", "depressed", "grief", "sorrow", "miserable", "heartbroken", "gloomy", "unhappy", "disappointed", "crying"],
        "fear": ["scared", "afraid", "terrified", "anxious", "worried", "nervous", "panicked", "dread", "frightened"],
        "hopelessness": ["hopeless", "helpless", "despair", "worthless", "pointless", "lost", "trapped", "giving up"],
        "stress": ["stressed", "overwhelmed", "pressure", "burden", "exhausted", "burnout", "overloaded"],
        "joy": ["happy", "excited", "joyful", "delighted", "pleased", "content", "thrilled", "glad", "grateful"],
        "neutral": []  # Default state if no strong emotions detected
    }

    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()

    # Count occurrences of emotion keywords
    emotion_counts = {}
    for emotion, keywords in emotions.items():
        if emotion == "neutral":
            continue  # Skip neutral category in counting

        count = 0
        for keyword in keywords:
            # Count whole word matches
            count += sum(1 for match in re.finditer(r'\b' + keyword + r'\b', text_lower))

        if count > 0:
            emotion_counts[emotion] = count

    # If no emotions detected, mark as neutral
    if not emotion_counts:
        emotion_counts["neutral"] = 1

    # Calculate confidence levels (simple normalization)
    total_matches = sum(emotion_counts.values())
    emotion_confidence = {emotion: count / total_matches for emotion, count in emotion_counts.items()}

    # Return detected emotions with confidence levels
    return {
        "primary_emotion": max(emotion_confidence, key=emotion_confidence.get),
        "emotion_confidence": emotion_confidence
    }

def detect_crisis_indicators(text: str) -> Dict[str, Any]:
    """
    Detect potential crisis indicators in the journal entry.

    Args:
        text: The journal entry text

    Returns:
        Dictionary with detected crisis indicators and risk level
    """
    # Define crisis keywords by category
    crisis_indicators = {
        "self_harm": ["kill myself", "suicide", "end my life", "hurt myself", "self harm", "cut myself", 
                     "don't want to live", "wanting to die", "better off dead"],
        "violence": ["hurt someone", "kill them", "violent thoughts", "attack", "rage", "revenge", 
                    "make them pay", "want to hurt"],
        "extreme_distress": ["can't take it anymore", "falling apart", "breaking down", "crisis", 
                            "emergency", "extreme", "unbearable", "can't cope", "at my limit"],
        "substance_abuse": ["overdose", "drunk", "drinking too much", "high", "addicted", 
                           "pills", "drugs", "substance", "relapse"]
    }

    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()

    # Check for indicators
    detected_indicators = {}
    for category, phrases in crisis_indicators.items():
        matches = []
        for phrase in phrases:
            if phrase in text_lower:
                matches.append(phrase)

        if matches:
            detected_indicators[category] = matches

    # Determine risk level
    risk_level = "none"
    if "self_harm" in detected_indicators:
        risk_level = "high"
    elif "violence" in detected_indicators:
        risk_level = "high"
    elif "extreme_distress" in detected_indicators or "substance_abuse" in detected_indicators:
        risk_level = "medium"
    elif detected_indicators:
        risk_level = "low"

    return {
        "detected_indicators": detected_indicators,
        "risk_level": risk_level
    }

def extract_metadata(text: str) -> Dict[str, Any]:
    """
    Extract potential metadata from journal entry.

    Args:
        text: The journal entry text

    Returns:
        Dictionary with potential metadata
    """
    # Define patterns for common life situations
    life_situations = {
        "parenting": ["my child", "my kid", "my son", "my daughter", "children", "parenting", "mom", "dad", "school"],
        "relationship": ["my partner", "my husband", "my wife", "my boyfriend", "my girlfriend", "dating", "marriage", "divorce"],
        "work": ["job", "career", "workplace", "boss", "coworker", "promotion", "fired", "work-life balance", "burnout"],
        "health": ["illness", "pain", "chronic", "doctor", "diagnosis", "treatment", "medication", "symptom", "recovery"],
        "grief": ["loss", "died", "passed away", "funeral", "missing someone", "death", "grief", "mourning"]
    }

    # Convert to lowercase for matching
    text_lower = text.lower()

    # Detect life situations
    detected_situations = {}
    for situation, keywords in life_situations.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected_situations[situation] = detected_situations.get(situation, 0) + 1

    # Extract the top situations
    top_situations = [k for k, v in sorted(detected_situations.items(), key=lambda item: item[1], reverse=True)]

    return {
        "life_situations": top_situations[:3] if top_situations else [],
        "word_count": len(text.split())
    }

def get_user_history_context(user_id: int) -> str:
    """
    Generate detailed context about the user's history from previous entries.
    Includes recent journal summaries, emotional trends, and identified patterns.

    Args:
        user_id: The user's ID

    Returns:
        String with user history context
    """
    try:
        entries = get_journal_entries_for_user(user_id)

        if not entries or len(entries) < 2:
            return ""

        # Analyze emotional trends
        anxiety_levels = []
        emotional_tones = []
        recurring_situations = {}
        recent_entries_data = []

        # Process the last 5 entries (excluding the most recent one)
        # We skip the most recent entry because it's likely the current one
        recent_entries = entries[1:6] if len(entries) > 1 else []

        for entry in recent_entries:
            # Get detailed data for each entry
            entry_data = {
                "date": entry.get("created_at", ""),
                "title": entry.get("title", "Untitled Entry"),
                "summary": summarize_journal_content(entry.get("content", "")),
                "anxiety": entry.get("anxiety_level", 5),
                "patterns": []
            }

            # Get patterns if available
            patterns = entry.get('cbt_patterns', [])
            if patterns:
                for pattern in patterns:
                    pattern_name = pattern.get('pattern')
                    if pattern_name and pattern_name not in ["Error analyzing entry", "API Quota Exceeded", "API Configuration Issue"]:
                        entry_data["patterns"].append(pattern_name)

            # Add to list of recent entries
            recent_entries_data.append(entry_data)

            # Get anxiety levels
            if "anxiety_level" in entry:
                anxiety_levels.append(entry["anxiety_level"])

            # Get emotional tones
            if "content" in entry:
                tone = detect_emotional_tone(entry["content"])
                emotional_tones.append(tone["primary_emotion"])

                # Extract situations
                metadata = extract_metadata(entry["content"])
                for situation in metadata.get("life_situations", []):
                    recurring_situations[situation] = recurring_situations.get(situation, 0) + 1

        # Create context string with historical trends
        context = []

        # Add anxiety trend
        if anxiety_levels:
            avg_anxiety = sum(anxiety_levels) / len(anxiety_levels)
            if avg_anxiety >= 7:
                context.append("User has consistently reported high anxiety levels")
            elif avg_anxiety <= 3:
                context.append("User has maintained relatively low anxiety levels")
            elif max(anxiety_levels) - min(anxiety_levels) >= 4:
                context.append("User has experienced significant fluctuations in anxiety levels")

        # Add emotional tone trends
        if emotional_tones:
            # Get most common emotion
            emotion_counts = {}
            for emotion in emotional_tones:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

            most_common = max(emotion_counts, key=emotion_counts.get)
            if emotion_counts[most_common] >= 2:
                context.append(f"User has frequently expressed {most_common}")

        # Add recurring life situations
        if recurring_situations:
            top_situation = max(recurring_situations, key=recurring_situations.get)
            if recurring_situations[top_situation] >= 2:
                context.append(f"User has been dealing with {top_situation}-related challenges")

        trends_context = ". ".join(context) if context else "No clear trends in recent journals."

        # Now build a detailed history section with recent journal summaries
        history_section = "RECENT JOURNAL HISTORY:\n"
        history_section += f"Trends: {trends_context}\n\n"

        # Add summaries of recent entries
        if recent_entries_data:
            history_section += "Recent entries (from newest to oldest):\n"
            for idx, entry in enumerate(recent_entries_data):
                patterns_text = ", ".join(entry["patterns"]) if entry["patterns"] else "No patterns identified"
                history_section += f"{idx+1}. {entry['title']} (Anxiety: {entry['anxiety']}/10, Patterns: {patterns_text})\n"
                history_section += f"   Summary: {entry['summary']}\n\n"

        return history_section

    except Exception as e:
        logger.error(f"Error generating user history context: {str(e)}")
        return ""

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
    Uses SQLAlchemy to query the database directly instead of JSON files.

    Args:
        user_id: The ID of the user
        min_entries: Minimum number of entries required

    Returns:
        A list of dictionaries with pattern and count
    """
    # Import needed modules
    from app import db
    from models import JournalEntry, CBTRecommendation
    from sqlalchemy import func, distinct
    
    try:
        # First check if the user has enough entries
        entry_count = JournalEntry.query.filter(JournalEntry.user_id == user_id).count()
        
        if entry_count < min_entries:
            logger.debug(f"User {user_id} has only {entry_count} entries, less than minimum {min_entries}")
            return []
        
        # Get patterns with counts using SQL aggregation
        # This gets the count of each pattern and sorts by frequency
        patterns_query = db.session.query(
            CBTRecommendation.thought_pattern, 
            func.count(CBTRecommendation.thought_pattern).label('count')
        ).join(
            JournalEntry, 
            CBTRecommendation.journal_entry_id == JournalEntry.id
        ).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.is_analyzed == True,
            ~CBTRecommendation.thought_pattern.in_(["Error analyzing entry", "API Quota Exceeded", "API Configuration Issue"])
        ).group_by(
            CBTRecommendation.thought_pattern
        ).order_by(
            func.count(CBTRecommendation.thought_pattern).desc()
        )
        
        # Execute the query
        patterns = patterns_query.all()
        
        # Format the results
        result = [{'pattern': pattern, 'count': count} for pattern, count in patterns]
        
        # Return top 3 patterns
        return result[:3]
        
    except Exception as e:
        logger.error(f"Error getting recurring patterns for user {user_id}: {str(e)}")
        
        # Fall back to the JSON-based method if database query fails
        logger.warning("Falling back to JSON-based pattern analysis")
        
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

def classify_journal_sentiment(text: str, anxiety_level: Optional[int] = None) -> str:
    """
    Classify journal sentiment as Joyful, Positive, Neutral, Concern, or Distress
    based on content and anxiety level.
    """
    # Check anxiety level first if provided
    if anxiety_level and anxiety_level >= 7:
        return "Distress"
    elif anxiety_level and anxiety_level >= 5:
        return "Concern"
    elif anxiety_level and anxiety_level <= 2:
        return "Joyful"

    # Analyze text content
    joyful_indicators = [
        "wonderful", "amazing", "blessed", "fantastic", "thrilled",
        "delighted", "overjoyed", "ecstatic", "blissful", "incredible"
    ]
    
    positive_indicators = [
        "happy", "grateful", "thankful", "excited", "proud",
        "peaceful", "calm", "good", "love", "enjoy",
        "appreciate", "hopeful", "pleased", "content"
    ]

    concern_indicators = [
        "upset", "sad", "confused", "unsure", "bothered",
        "tired", "annoyed", "difficult", "hard", "struggle"
    ]

    distress_indicators = [
        "anxious", "worried", "scared", "depressed", "hopeless",
        "overwhelmed", "stressed", "panic", "afraid", "terrified",
        "lonely", "miserable", "hate", "angry", "frustrated"
    ]

    text_lower = text.lower()

    # Count indicators
    distress_count = sum(1 for word in distress_indicators if word in text_lower)
    concern_count = sum(1 for word in concern_indicators if word in text_lower)
    positive_count = sum(1 for word in positive_indicators if word in text_lower)

    # Classify based on strongest signal
    if distress_count > 0 and distress_count >= positive_count:
        return "Distress"
    elif concern_count > 0 and concern_count >= positive_count:
        return "Concern"
    elif positive_count > 0:
        return "Positive"
    else:
        return "Neutral"

def analyze_journal_with_gpt(journal_text: Optional[str] = None, anxiety_level: Optional[int] = None, user_id: int = 0, mode: str = "initial") -> Dict[str, Any]:
    """
    Generate an improved AI analysis of a journal entry that's concise and focused,
    with NLP preprocessing and structured metadata for more personalized responses.
    
    Returns a dictionary with the following structure:
    {
        "gpt_response": String with Mira's full response,
        "cbt_patterns": List of thought patterns identified,
        "structured_data": Dictionary with structured data for UI display including the insight_text, 
                          reflection_prompt, thought_patterns, strategies, etc.
    }

    Args:
        journal_text: The journal entry text
        anxiety_level: Anxiety level (1-10)
        user_id: User ID for pattern analysis

    Returns:
        Dictionary with response and identified patterns
    """
    # Handle None or empty values with more robust validation
    if not journal_text or journal_text.strip() == "":
        logger.error("Empty or invalid journal text provided")
        return {
            "gpt_response": "I wasn't able to read your journal entry. Please try again.",
            "cbt_patterns": [],
            "structured_data": None
        }
    safe_text = journal_text.strip()
    safe_anxiety = anxiety_level if anxiety_level is not None else 5  # Default to mid-level anxiety

    logger.debug(f"Analyzing journal text (first 100 chars): {safe_text[:100]}...")
    try:
        # Get API key and model settings with detailed logging
        api_key = get_openai_api_key()
        model = get_openai_model()

        # Log the configuration details (sanitized)
        if api_key:
            # Check if the API key is a valid format (starts with sk-)
            if api_key.startswith('sk-'):
                logger.debug(f"API key found with valid format (length: {len(api_key)}, starts with: {api_key[:5]}...)")
            else:
                logger.warning(f"API key found but has unexpected format: {api_key[:10]}... (length: {len(api_key)})")
                # Try to fix the key if it looks like an email
                if '@' in api_key and '.' in api_key:
                    logger.warning("API key appears to be an email address instead of an API key")
                    # This will trigger the proper error handling below
                    api_key = None
        else:
            logger.debug("No API key found in environment or admin settings")

        logger.debug(f"Using model: {model}")

        # Check if API key is available
        if not api_key:
            logger.error("OpenAI API key is not set")
            raise ValueError("INVALID_API_KEY: OpenAI API key is missing. Please check your environment variables or admin settings.")

        # Preprocess the journal entry with NLP analysis
        # 1. Tag emotional tone
        emotional_tone = detect_emotional_tone(safe_text)
        primary_emotion = emotional_tone.get("primary_emotion", "neutral")
        logger.debug(f"Detected primary emotion: {primary_emotion}")

        # 2. Detect crisis indicators
        crisis_info = detect_crisis_indicators(safe_text)
        risk_level = crisis_info.get("risk_level", "none")
        logger.debug(f"Detected crisis risk level: {risk_level}")

        # 3. Extract metadata (life situations, etc.)
        metadata = extract_metadata(safe_text)
        life_situations = metadata.get("life_situations", [])
        life_situations_text = ", ".join(life_situations) if life_situations else "general life"
        logger.debug(f"Detected life situations: {life_situations_text}")

        # 4. Get user history context
        user_history = get_user_history_context(user_id) if user_id else ""
        logger.debug(f"User history context: {user_history}")

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

        # Build the enhanced metadata section
        metadata_section = f"""
        ## JOURNAL METADATA:
        - Anxiety Level: {safe_anxiety}/10
        - Primary Emotion: {primary_emotion}
        - Risk Level: {risk_level}
        - Life Situations: {life_situations_text}
        - Word Count: {metadata.get('word_count', 0)}
        """

        # Add user history if available
        if user_history:
            metadata_section += f"""
        ## USER HISTORY CONTEXT:
        {user_history}
        """

        # Add recurring patterns if available
        if recurring_patterns_text:
            metadata_section += f"""
        ## RECURRING THOUGHT PATTERNS:
        {recurring_patterns_text}
        """

        # Add crisis alert if risk level is medium or high
        crisis_instructions = ""
        if risk_level in ["medium", "high"]:
            crisis_instructions = f"""
        ## CRISIS ALERT - {risk_level.upper()} RISK:
        This entry contains potential {', '.join(crisis_info.get('detected_indicators', {}).keys())} indicators. 
        Provide supportive, non-judgmental validation while gently encouraging safety planning and professional support.
        """

        # Create the enhanced structured prompt with greater emotional intelligence and historical awareness
        # Classify journal sentiment
        sentiment = classify_journal_sentiment(safe_text, safe_anxiety)
        logger.debug(f"Journal sentiment classified as: {sentiment}")

        # For followup mode, use a different prompt structure focused on the user's reflection
        if mode == "followup":
            # Split the journal text to separate original entry from user reflection
            # Format is expected to be: "{original_entry}\n\nUser Reflection: {reflection_text}"
            parts = safe_text.split("\n\nUser Reflection: ", 1)
            original_entry = parts[0] if len(parts) > 0 else ""
            reflection_text = parts[1] if len(parts) > 1 else ""
            
            logger.info(f"Processing followup reflection: {reflection_text[:50]}...")
            logger.info(f"Mode detected: followup mode")
            
            prompt = f"""
            You are Mira, a warm, emotionally intelligent journaling coach using CBT principles.

            You've already responded once to a user's journal entry with a reflection prompt. The user has now replied with their reflection.

            Original Journal Entry: 
            "{original_entry}"
            
            User's Reflection: 
            "{reflection_text}"

            Your task is to continue the conversation with a deeper, emotionally aware follow-up that ALWAYS ends with a thoughtful, reflective question. Do not repeat the original insight or prompt. Do not be generic.

            Build specifically on what the user just revealed:
            - If they expressed sadness, acknowledge it and gently explore what's behind it with a question.
            - If they revealed anger, validate it and ask a question that invites deeper exploration.
            - If they showed resignation, ask what boundary or shift might protect them.
            - If they mentioned perfectionism, explore how it relates to their self-worth with a thoughtful question.
            - If they revealed fears of abandonment, connect this to their relationship patterns and ask a deepening question.
            - If they shared a vulnerability, honor it with validation and then ask a meaningful question.

            Return your response in JSON format with this structure:
            {{
              "followup_text": "Your thoughtful, empathetic response that builds on their reflection and ALWAYS ends with a specific, reflective question that invites deeper exploration"
            }}
            
            Use a warm, human tone and keep the response (2-4 sentences) specific to what they shared. Your response must:
            1. Show you understood their reflection
            2. Build on it meaningfully
            3. ALWAYS end with a reflective question that invites deeper exploration
            """
            
        # Choose prompt based on sentiment for initial analysis
        elif sentiment in ["Positive", "Neutral"]:
            prompt = f"""
            You are Mira, a warm, supportive journaling coach inside Calm Journey. A user has just submitted a {sentiment.lower()} journal entry.

            Journal entry: "{safe_text}"

            This is a moment for celebration and affirmation. Return a simple JSON response with exactly:
            - 'insight_text': One warm, specific comment that reflects their positive experience and its value
            - 'reflection_prompt': A gentle question that helps carry this positive energy forward
            - 'followup_text': A brief closing thought that supports savoring this moment

            Example for "Today is a fantastic day. Everything is going as planned!":
            {{
                "insight_text": "It's so good to see everything going as planned — moments like this reflect your efforts and create space for ease and joy.",
                "reflection_prompt": "What's one part of today you want to carry into tomorrow?",
                "followup_text": "Let yourself fully receive the goodness of this moment. You deserve it."
            }}

            Keep your response encouraging and warm, focusing on their specific experience.
            
            Journal entry: "{safe_text}"
                "insight_text": "It's so good to hear that today feels wonderful — noticing and naming joy is a powerful act.",
                "reflection_prompt": "What made today feel wonderful for you?", 
                "followup_text": "May this positive energy carry you gently into whatever comes next."
            }}

            Keep your response warm and celebratory, focusing only on these elements.
            """
        else:
            prompt = f"""
            You are Mira, a warm, compassionate CBT journaling coach inside an app called Calm Journey. 
        Your task is to respond to the following journal entry with deep emotional intelligence, therapeutic insight, and highly personalized CBT strategies.
        You should reference patterns and themes from previous entries when appropriate to show continuity and insight into the user's journey.

        ## JOURNAL ENTRY:
        "{safe_text}"

        {metadata_section}
        {crisis_instructions}

        ## USER HISTORY CONTEXT:
        {user_history}

        ## YOUR TASK:
        1. Validate specific emotions by naming them precisely (e.g., "neglected," "anxious," "unimportant") rather than using general statements
        2. Identify cognitive distortions with depth, connecting them to underlying emotional needs (need for safety, validation, connection)
        3. Explore relationship context by including thoughtful questions about patterns and expectations
        4. Offer practical, actionable steps including specific scripts or templates the user can directly apply
        5. Encourage meaningful self-reflection that identifies core emotional needs
        6. Balance compassionate support with gentle challenges to unhelpful thought patterns
        7. When appropriate, connect current issues to patterns or themes observed in previous journals (reference specific entries if relevant)
        8. Acknowledge progress or changes in thinking compared to previous entries when applicable

        ## ENHANCED THERAPEUTIC TECHNIQUES:
        1. Provide a scripted "I-statement" template they can use in a conversation (e.g., "I feel ___ when ___ because ___. What I need is ___.")
        2. Include a focused reality-check exercise that challenges negative assumptions (list evidence for/against)
        3. Offer a specific emotion-regulation technique appropriate to their situation
        4. Create a mini reflection guide (e.g., "When I feel [emotion], I will [healthy action] instead of [unhealthy reaction]")
        5. Connect current feelings to deeper emotional needs to increase self-awareness

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
        DO NOT use markdown formatting like ```json or ``` markers.
        RETURN ONLY THE JSON OBJECT, nothing else.

        {{
            "insight_text": "Your empathetic initial response that specifically names emotions like 'neglected', 'anxious', 'unimportant' and introduces a connection to emotional needs and relationship patterns",
            "reflection_prompt": "Take a moment. What's one expectation you've been holding about this relationship that feels heavy — and might point to an important emotional need?",
            "followup_text": "Your supportive follow-up that provides a specific script, template, or practical exercise the user can implement immediately",
            "distortions": [
                {{
                    "pattern": "Name of CBT thought pattern 1",
                    "description": "In-depth explanation connecting this pattern to specific emotional needs (e.g., safety, validation, connection)",
                    "emotional_need": "The core emotional need driving this thought pattern"
                }},
                {{
                    "pattern": "Name of CBT thought pattern 2",
                    "description": "In-depth explanation connecting this pattern to specific emotional needs",
                    "emotional_need": "The core emotional need driving this thought pattern"
                }}
            ],
            "strategies": [
                {{
                    "title": "Communication Script Template",
                    "description": "Detailed explanation of when to use this script in the relationship context",
                    "action_step": "I feel [specific emotion] when [specific behavior] because [impact]. What I need is [clear request].",
                    "emotional_need_addressed": "The specific emotional need this strategy helps fulfill"
                }},
                {{
                    "title": "Reality-Check Exercise",
                    "description": "Detailed explanation of how assumptions are affecting the situation",
                    "action_step": "List evidence for and against your fear that [specific fear related to the relationship]",
                    "emotional_need_addressed": "The specific emotional need this strategy helps fulfill"
                }},
                {{
                    "title": "Emotion Regulation Technique",
                    "description": "Explanation of how to manage the intense emotions in this situation",
                    "action_step": "When you feel [specific emotion], try this specific grounding technique: [detailed steps]",
                    "emotional_need_addressed": "The specific emotional need this strategy helps fulfill"
                }}
            ],
            "relationship_exploration": [
                {{
                    "question": "Has this communication pattern happened before in this relationship?",
                    "purpose": "Exploring recurring patterns to identify relationship dynamics"
                }},
                {{
                    "question": "What expectations were set before your partner left?",
                    "purpose": "Examining unspoken assumptions that may contribute to distress"
                }}
            ],
            "actionable_templates": [
                {{
                    "situation": "When reaching out to express your needs",
                    "template": "A ready-to-use message template they can adapt for their specific situation",
                    "follow_up_guidance": "Specific advice on what to do after using this template"
                }},
                {{
                    "situation": "When managing anxiety while waiting for a response",
                    "template": "When I feel [specific emotion], I will [healthy coping action] instead of [unhealthy reaction]",
                    "follow_up_guidance": "How to respond to different possible outcomes"
                }}
            ],
            "patterns": [
                {{
                    "pattern": "Name of CBT thought pattern 1",
                    "description": "In-depth explanation of how this pattern affects relationships",
                    "recommendation": "Specific CBT technique tailored for relationship contexts",
                    "core_need": "The emotional need this pattern is trying to meet"
                }},
                {{
                    "pattern": "Name of CBT thought pattern 2",
                    "description": "In-depth explanation of how this pattern affects relationships", 
                    "recommendation": "Specific CBT technique tailored for relationship contexts",
                    "core_need": "The emotional need this pattern is trying to meet"
                }}
            ]
        }}

        Your response (in the "response" field) should follow this therapeutic structure:

        1. **Personal Connection & Emotional Validation**
           - Begin with a personalized greeting that acknowledges the specific individual (use an appropriate name if provided in the journal).
           - Show deep empathy for their specific situation and emotions. Directly reference details from their journal entry.
           - Use language that shows you truly understand their unique circumstances.

        2. **Nuanced Reflection & Contextual Understanding**
           - Provide a thoughtful analysis that shows you've carefully considered their unique situation.
           - Acknowledge the complexity of their experience, avoiding simplistic interpretations.
           - Reference specific details from their journal to demonstrate your understanding.

        3. **Identify Relevant Cognitive Patterns**
           - Identify 2-3 thought patterns that specifically relate to their situation.
           - Explain these patterns using their own examples from the journal.
           - Frame these observations in a compassionate, non-judgmental way.

        4. **Tailored CBT Strategies**
           - Offer 2-4 practical, specific techniques directly relevant to their situation.
           - Customize each suggestion to their specific context, not generic advice.
           - Provide clear, actionable steps they can take, using concrete examples from their life.
           - Format these as bullet points with clear titles and brief explanations.

        5. **Personalized Reflection Prompt**
           - Create a reflection question that directly addresses their specific situation.
           - Frame this as a compassionate invitation to deeper understanding.
           - Make it specific to their circumstances, not generic.

        6. **Warm, Personal Close**
           - End with genuine encouragement that acknowledges their unique journey.
           - Remind them they're not alone in their specific struggles.
           - Sign off warmly as "Coach Mira" with a brief personal touch.

        Tone: Write as if you are a trusted friend who deeply understands their specific situation. Be warm, personal, empathetic, and thoughtful. Avoid clinical language or generic advice. Your response should feel like it was written specifically for them, not a template.

        Here's an example of the personalized, empathetic style I want (this is just an example - your actual response should be tailored to the journal content):

        "Hi Josiah, I can feel how much you're carrying right now—and how painful, exhausting, and frightening it must be to love your daughter so deeply while also feeling so powerless and overwhelmed. You're doing so much: working, parenting, managing co-parenting conflict, and trying to help your daughter through a very serious and risky phase. You're not failing—you're in crisis, and your concern shows just how deeply you care.

        Thought Patterns That May Be Surfacing:
        * Personalization: You may be feeling like her choices reflect your worth or effectiveness as a mother ("What am I doing wrong?"). This is a very human thought, but it's not fully true—you are not the cause of all her behavior.
        * Catastrophizing: Understandably, you're imagining worst-case outcomes (pregnancy, STDs, future failure). This can amplify your anxiety and make problem-solving harder.
        * Emotional Reasoning: Feeling hopeless or exhausted may lead to thoughts like "nothing is working," even though you're actively trying many things.

        CBT-Based Strategies:
        1. Separate the Problem from the Person Your daughter is in distress and making dangerous choices, but she is not beyond help. Try to hold both truths: you love her and you must protect your peace.
        2. Boundary Reframing Define what is yours to carry (structure, safety, emotional limits) and what must be hers (school effort, honesty, behavior). Repeating this may help reduce your burnout.
        3. Self-Compassion Prompt Write this sentence: "Even though I feel ________, I am showing up by __________." Example: "Even though I feel defeated, I am showing up by finding help." 
        4. Grounding Action Today Choose one thing today to reduce the emotional chaos. Maybe that's contacting the school, journaling without censoring, or planning a break for yourself.

        Reflection Prompt: "What part of this crisis is mine to carry—and what can I start letting go of, even if just a little?"

        You're not alone. You're not a bad parent. You're exhausted because you care deeply—and care is never wasted.

        Warmly,
        Coach Mira"

        Notice how the example response directly addresses the person's specific situation with personalized insights and recommendations. Your response should be similarly tailored to the exact content of their journal entry.

        CRITICAL: Return ONLY valid JSON as described above. 
        NEVER include any text outside the JSON structure.
        NEVER use markdown code blocks or backticks.
        ONLY return a valid JSON object with the "response" and "patterns" fields.
        EVERYTHING YOU RETURN MUST BE PARSABLE AS JSON.
        """

        # Attempt to make the API call with error handling
        try:
            # Get a fresh client with the current API key
            client = get_openai_client()

            # Log the API parameters for debugging
            logger.debug(f"Making OpenAI API call with model: {model}, API key (sanitized): {'*****' + api_key[-4:] if api_key else 'None'}")

            # Determine if this is followup mode for proper API request configuration
            is_followup_mode = mode == "followup"
            logger.info(f"API request mode: {'followup' if is_followup_mode else 'initial'}")
            
            # Make the API call with appropriate parameters based on mode
            if is_followup_mode:
                # For followup mode, use an emotionally intelligent system message that mentions JSON
                logger.info("Using response_format=json_object for followup mode")
                # Ensure there's no conflict with variable names
                api_response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": """You are Mira, a warm, emotionally intelligent CBT-based coach in Dear Teddy. Provide a thoughtful followup response in JSON format.

IMPORTANT INSTRUCTIONS:
1. Acknowledge the user's reflection with specific emotional validation
2. Deepen the inquiry with a more specific follow-up question that builds on their response
3. Make your follow-up question emotionally intelligent - name specific emotions they might be feeling
4. Format your question to invite exploration of unexamined aspects of their feelings
5. Return response in valid JSON format with these fields:
   - response: your warm, supportive acknowledgment and follow-up question
   - patterns: array of thought patterns or insights you've identified (can be empty)

FOLLOWUP QUESTION EXAMPLES:
- "When you realize you're afraid of disappointing others, does that create a pressure to always be 'on' for them?"
- "That feeling of invisibility despite your efforts sounds painful. When did you first notice this pattern happening?"
- "You've named feeling both hurt and angry. Which of those emotions feels harder to sit with right now?"
- "When you say you take on more than you can handle, how does your body feel when you're in that overwhelmed state?"

Be warm, insightful, and genuinely curious in your response."""},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=1500
                )
            else:
                # For initial mode, use the standard system message
                api_response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": """
You are Mira, an emotionally intelligent CBT-based journaling coach inside Dear Teddy (formerly Calm Journey). Your goal is to help the user reflect on their emotional experiences in a compassionate, supportive, and directive way.

You will be given a journal entry and additional context about the user's history and emotional patterns.

Return your output as a JSON object with two main sections:

---

1. **narrative_response** (for Mira's Insights - Listen tab)
A warm, natural-language reflection that reads like a kind journal coach. Include:
- A brief insight summarizing the journal's emotional tone
- A gentle reflection prompt that feels personal, emotionally attuned, and non-repetitive
- A short closing affirmation

Avoid jargon. Do not include section titles. Write like a caring coach speaking directly to the user.

---

2. **structured_response** (for CBT Tools - Interact tab)
This is a breakdown of actionable insight using CBT principles. Only include sections if relevant:

- **insight_text**: Grounded summary of emotional or cognitive themes
- **reflection_prompt**: One specific, emotionally intelligent question that directly connects to their feelings (e.g., "When you think about how one-sided this feels, what emotion comes up first—hurt, anger, something else?")
- **thought_patterns**: List of clearly detected distortions (e.g., Filtering, Catastrophizing)
- **strategies**: List of helpful CBT-based techniques (briefly described)
- **templates**: Optional ready-to-use scripts (for self-expression or anxiety management)
- **relationship_questions**: Optional reflection questions for relational themes
- **followup_text**: Affirming encouragement to close

---

IMPORTANT INSTRUCTIONS:
- Make reflection prompts highly specific to the user's emotional experience, not generic. Ask about specific emotions they might be feeling.
- Make reflection prompts emotionally intelligent by naming potential feelings the user might be experiencing.
- Format reflection prompts as direct, empathetic questions that invite deeper emotional exploration.
- For Joyful or Positive entries, do NOT include thought_patterns or strategies unless clearly warranted. Focus on savoring and celebration.
- For Distress or Concern, use CBT gently but clearly.
- Do NOT repeat phrasing across sessions (e.g., "What expectation are you holding…").
- Everything must be clearly grounded in the user's actual journal entry.
- When relevant, reference patterns, progress, or recurring themes from previous journal entries to create a sense of continuity and deeper understanding.

REFLECTION PROMPT EXAMPLES:
- "When you feel invisible despite your care for others, does it remind you of patterns from your past relationships?"
- "You mentioned feeling 'stupid for caring so much'—what would you say to a friend who felt the same way?"
- "If we named the emotion behind feeling unseen when you reach out to others, what would it be?"
- "When you think about how one-sided these relationships feel, what emotion comes up first—hurt, anger, something else?"

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
                    },
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
                content = api_response.choices[0].message.content
                logger.debug(f"Raw OpenAI response content: {content}")  # Log the full content for debugging
                # Also log the exact format to see any issues
                logger.debug(f"Response type: {type(content)}, length: {len(content)}")

                # Parse the JSON with more robust error handling
                try:
                    # Safety trim in case the response is too large
                    if len(content) > 20000:
                        logger.warning(f"Response content is very large ({len(content)} chars), trimming for parsing")
                        content = content[:20000]

                    # Parse the initial JSON
                    result = json.loads(content)

                    # Clean the result by removing empty fields
                    cleaned_result = {}
                    for key, value in result.items():
                        # Skip empty strings, empty lists, or None values
                        if value and (isinstance(value, str) and value.strip() or 
                                    isinstance(value, (list, dict)) and value):
                            cleaned_result[key] = value

                    # Only include thought_patterns if distortions are present
                    if 'distortions' not in cleaned_result or not cleaned_result['distortions']:
                        cleaned_result.pop('thought_patterns', None)

                    # Only include strategies if there's emotional struggle
                    if sentiment not in ["Concern", "Distress"]:
                        cleaned_result.pop('strategies', None)

                    result = cleaned_result

                    # Sometimes the API returns content with non-JSON text before or after the JSON
                    # Try to extract just the JSON part using regex
                    import re
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)

                    if json_match:
                        # Extract just the JSON part
                        json_content = json_match.group(1)
                        try:
                            result = json.loads(json_content)
                            logger.debug("Successfully parsed JSON response using regex extraction")
                        except json.JSONDecodeError:
                            # If regex extraction fails, try a direct approach with the original content
                            logger.warning("Regex extraction failed, trying direct parsing of full content")
                            result = json.loads(content)
                            logger.debug("Successfully parsed JSON response from full content")
                    else:
                        # If regex fails, try the full content
                        logger.warning("No JSON-like structure found with regex, trying direct parsing")
                        result = json.loads(content)
                        logger.debug("Successfully parsed JSON response from full content")

                    # Log the final result structure
                    logger.debug(f"Parsed result keys: {list(result.keys())}")
                except Exception as json_parse_error:
                    logger.error(f"Failed to parse JSON response: {str(json_parse_error)}")

                    # Look for patterns that suggest it's a valid response but not in JSON format
                    if "warmly" in content.lower() or "coach mira" in content.lower() or "thank you for sharing" in content.lower():
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
                        logger.debug(f"Created manual response object with content: {content[:100]}...")
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

                # Handle the new structured response format
                # Check if we have the new narrative format with structured_response
                has_narrative_format = 'narrative_response' in result and 'structured_response' in result
                
                # Check if we have the enhanced reflective pause format fields
                has_enhanced_format = all(k in result for k in ['insight_text', 'reflection_prompt', 'followup_text']) and any(k in result for k in ['relationship_exploration', 'actionable_templates'])
                
                # Special handling for followup mode using the response field
                if mode == "followup" and 'response' in result:
                    # For followup mode, the main content is in the 'response' field
                    # Copy this to other fields for consistent processing
                    coach_response = result['response']
                    result['gpt_response'] = coach_response
                    result['followup_text'] = coach_response
                    result['followup_message'] = coach_response
                    logger.info(f"Extracted followup response from 'response' field: {coach_response[:100]}...")

                # Check if we have the reflective pause format fields (older version)
                has_reflective_pause_format = all(k in result for k in ['insight_text', 'reflection_prompt', 'followup_text'])

                # Check if we have all the expected fields for the previous format
                has_structured_format = all(k in result for k in ['intro', 'reflection', 'distortions', 'strategies', 'reflection_prompt', 'outro'])

                if has_narrative_format:
                    logger.debug("Found new narrative format with structured_response")
                    
                    # Get the narrative response for the main display
                    narrative_response = result.get('narrative_response', '')
                    
                    # Get the structured response for interactive elements
                    structured_response = result.get('structured_response', {})
                    
                    # Extract components from structured response
                    insight_text = structured_response.get('insight_text', '')
                    reflection_prompt = structured_response.get('reflection_prompt', '')
                    followup_text = structured_response.get('followup_text', '')
                    thought_patterns = structured_response.get('thought_patterns', [])
                    strategies = structured_response.get('strategies', [])
                    templates = structured_response.get('templates', [])
                    relationship_questions = structured_response.get('relationship_questions', [])
                    
                    # Format thought patterns
                    thought_patterns_text = ""
                    if thought_patterns:
                        thought_patterns_text = "\n\n## Thought Patterns\n"
                        for pattern in thought_patterns:
                            if isinstance(pattern, dict):
                                pattern_name = pattern.get('pattern', '')
                                description = pattern.get('description', '')
                                thought_patterns_text += f"\n**{pattern_name}**\n{description}\n"
                            elif isinstance(pattern, str):
                                thought_patterns_text += f"\n**{pattern}**\n"
                    
                    # Format strategies
                    strategies_text = ""
                    if strategies:
                        strategies_text = "\n\n## Suggested Strategies\n"
                        for i, strategy in enumerate(strategies, 1):
                            if isinstance(strategy, dict):
                                title = strategy.get('title', f"Strategy {i}")
                                description = strategy.get('description', '')
                                action = strategy.get('action', '')
                                strategies_text += f"\n**{i}. {title}**\n{description} {action}\n"
                            elif isinstance(strategy, str):
                                strategies_text += f"\n**{i}. Strategy {i}**\n{strategy}\n"
                    
                    # Format templates
                    templates_text = ""
                    if templates:
                        templates_text = "\n\n## Ready-to-Use Templates\n"
                        for i, template in enumerate(templates, 1):
                            if isinstance(template, dict):
                                situation = template.get('situation', f"Situation {i}")
                                text = template.get('text', '')
                                guidance = template.get('guidance', '')
                                templates_text += f"\n**For {situation}:**\n\"{text}\"\n"
                                if guidance:
                                    templates_text += f"Then: {guidance}\n"
                            elif isinstance(template, str):
                                templates_text += f"\n**Template {i}:**\n\"{template}\"\n"
                    
                    # Format relationship questions
                    relationship_text = ""
                    if relationship_questions:
                        relationship_text = "\n\n## Relationship Context Questions\n"
                        for i, question in enumerate(relationship_questions, 1):
                            if isinstance(question, dict):
                                q_text = question.get('question', '')
                                purpose = question.get('purpose', '')
                                relationship_text += f"• **{q_text}**\n"
                                if purpose:
                                    relationship_text += f"  ({purpose})\n\n"
                            elif isinstance(question, str):
                                relationship_text += f"• **{question}**\n\n"
                    
                    # Use the narrative response as the main coach response
                    coach_response = narrative_response
                    
                    # Remove thought patterns section from coach response if present
                    if "We're starting to notice" in coach_response:
                        coach_response = coach_response.split("We're starting to notice")[0].strip()
                    
                    # Make sure we have a sign-off
                    if "Coach Mira" not in coach_response and "Mira" not in coach_response:
                        coach_response += "\n\nWarmly,\nCoach Mira"
                    
                    # Store structured data for UI components
                    result['structured_data'] = {
                        'insight_text': insight_text,
                        'reflection_prompt': reflection_prompt,
                        'followup_text': followup_text,
                        'thought_patterns': thought_patterns,
                        'strategies': strategies,
                        'templates': templates,
                        'relationship_questions': relationship_questions
                    }
                    
                elif has_enhanced_format:
                    logger.debug("Found enhanced format with relationship exploration and actionable templates")

                    # Get the three parts of the reflective pause format
                    insight_text = result.get('insight_text', '')
                    reflection_prompt = result.get('reflection_prompt', '')
                    followup_text = result.get('followup_text', '')

                    # Process distortions section with emotional needs
                    distortions_list = result.get('distortions', [])
                    distortions_text = "\n\n## Thought Patterns\n"
                    for d in distortions_list:
                        pattern = d.get('pattern', '')
                        description = d.get('description', '')
                        emotional_need = d.get('emotional_need', '')

                        # Add emotional need if provided
                        if emotional_need:
                            distortions_text += f"\n**{pattern}**\n{description} This may relate to your need for {emotional_need}.\n"
                        else:
                            distortions_text += f"\n**{pattern}**\n{description}\n"

                    # Process strategies section with emotional needs addressed
                    strategies_list = result.get('strategies', [])
                    strategies_text = "\n\n## Suggested Strategies\n"
                    for i, s in enumerate(strategies_list, 1):
                        title = s.get('title', f"Strategy {i}")
                        description = s.get('description', '')
                        action = s.get('action_step', '')
                        emotional_need = s.get('emotional_need_addressed', '')

                        # Format with emotional need if provided
                        if emotional_need:
                            strategies_text += f"\n**{i}. {title}**\n{description} {action} This helps address your need for {emotional_need}.\n"
                        else:
                            strategies_text += f"\n**{i}. {title}**\n{description} {action}\n"

                    # Process relationship exploration if available
                    relationship_exploration = result.get('relationship_exploration', [])
                    relationship_text = ""
                    if relationship_exploration:
                        relationship_text = "\n\n## Relationship Context Questions\n"
                        for i, q in enumerate(relationship_exploration, 1):
                            question = q.get('question', '')
                            purpose = q.get('purpose', '')
                            relationship_text += f"• **{question}**\n  ({purpose})\n\n"

                    # Process actionable templates if available
                    templates = result.get('actionable_templates', [])
                    templates_text = ""
                    if templates:
                        templates_text = "\n\n## Ready-to-Use Templates\n"
                        for i, t in enumerate(templates, 1):
                            situation = t.get('situation', '')
                            template = t.get('template', '')
                            guidance = t.get('follow_up_guidance', '')

                            templates_text += f"\n**For {situation}:**\n\"{template}\"\n"
                            if guidance:
                                templates_text += f"Then: {guidance}\n"

                    # Combine sections for the enhanced response format, but EXCLUDE thought patterns
                    coach_response = f"{insight_text}\n\n{reflection_prompt}\n\n{followup_text}{strategies_text}{relationship_text}{templates_text}"

                    # Add a sign-off if not already present
                    if "Coach Mira" not in coach_response:
                        coach_response += "\n\nWarmly,\nCoach Mira"

                    # Store the structured data with all new fields
                    result['structured_data'] = {
                        'insight_text': insight_text,
                        'reflection_prompt': reflection_prompt,
                        'followup_text': followup_text,
                        'distortions': distortions_list,
                        'strategies': strategies_list,
                        'relationship_exploration': relationship_exploration,
                        'actionable_templates': templates
                    }

                elif has_reflective_pause_format:
                    logger.debug("Found basic reflective pause format with all expected fields")

                    # Get the three parts of the reflective pause format
                    insight_text = result.get('insight_text', '')
                    reflection_prompt = result.get('reflection_prompt', '')
                    followup_text = result.get('followup_text', '')

                    # Process distortions section
                    distortions_list = result.get('distortions', [])
                    distortions_text = "\n\n## Thought Patterns\n"
                    for d in distortions_list:
                        pattern = d.get('pattern', '')
                        description = d.get('description', '')
                        distortions_text += f"\n**{pattern}**\n{description}\n"

                    # Process strategies section
                    strategies_list = result.get('strategies', [])
                    strategies_text = "\n\n## Suggested Strategies\n"
                    for i, s in enumerate(strategies_list, 1):
                        title = s.get('title', f"Strategy {i}")
                        description = s.get('description', '')
                        action = s.get('action_step', '')
                        strategies_text += f"\n**{i}. {title}**\n{description} {action}\n"

                    # Combine sections for the legacy response format, but EXCLUDE thought patterns
                    coach_response = f"{insight_text}\n\n{reflection_prompt}\n\n{followup_text}{strategies_text}"

                    # Add a sign-off if not already present
                    if "Coach Mira" not in coach_response:
                        coach_response += "\n\nWarmly,\nCoach Mira"

                    # Store the structured data
                    result['structured_data'] = {
                        'insight_text': insight_text,
                        'reflection_prompt': reflection_prompt,
                        'followup_text': followup_text,
                        'distortions': distortions_list,
                        'strategies': strategies_list
                    }
                elif has_structured_format:
                    logger.debug("Found legacy structured format with all expected fields")

                    # Combine the structured parts into a cohesive response
                    intro = result.get('intro', '')
                    reflection = result.get('reflection', '')

                    # Process distortions section
                    distortions_list = result.get('distortions', [])
                    distortions_text = "\n\n## Thought Patterns\n"
                    for d in distortions_list:
                        pattern = d.get('pattern', '')
                        description = d.get('description', '')
                        distortions_text += f"\n**{pattern}**\n{description}\n"

                    # Process strategies section
                    strategies_list = result.get('strategies', [])
                    strategies_text = "\n\n## Suggested Strategies\n"
                    for i, s in enumerate(strategies_list, 1):
                        title = s.get('title', f"Strategy {i}")
                        description = s.get('description', '')
                        action = s.get('action_step', '')
                        strategies_text += f"\n**{i}. {title}**\n{description} {action}\n"

                    # Add reflection prompt
                    reflection_prompt = result.get('reflection_prompt', '')
                    if reflection_prompt:
                        reflection_prompt = f"\n\n## Reflection Prompt\n\"{reflection_prompt}\"\n"

                    # Add outro
                    outro = result.get('outro', '')

                    # Combine sections without thought patterns
                    coach_response = f"{intro}\n\n{reflection}{strategies_text}{reflection_prompt}\n\n{outro}"

                    # Convert to the new reflective pause format for consistency
                    result['structured_data'] = {
                        'insight_text': f"{intro}\n\n{reflection}",
                        'reflection_prompt': reflection_prompt.replace('\n\n## Reflection Prompt\n"', '').replace('"\n', ''),
                        'followup_text': outro,
                        'distortions': distortions_list,
                        'strategies': strategies_list
                    }
                else:
                    # Fall back to the old format for backward compatibility
                    logger.debug("Response doesn't have structured format, using legacy format")

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

                # If we still don't have a valid response, use the original content if it looks like text
                if (coach_response is None or coach_response == "") and content and len(content) > 20:
                    logger.warning("No valid response key found in JSON, using raw content as fallback")
                    coach_response = content

                # Format unstructured response to improve readability
                if not result.get('structured_data') and not has_enhanced_format and not has_reflective_pause_format and not has_structured_format:
                    logger.debug("Formatting unstructured response to improve readability")

                    # Split into paragraphs
                    paragraphs = coach_response.split('\n\n')
                    formatted_paragraphs = []

                    # Format each paragraph with proper HTML
                    for i, paragraph in enumerate(paragraphs):
                        if i == 0:
                            # First paragraph is usually the introduction/validation
                            formatted_paragraphs.append(f"<div class='validation-section mb-4'>{paragraph}</div>")
                        elif "pattern" in paragraph.lower() or "distortion" in paragraph.lower():
                            # Thought patterns section
                            formatted_paragraphs.append(f"<div class='thought-patterns-section mb-4'><h5 class='mb-3'>Thought Patterns</h5>{paragraph}</div>")
                        elif "strateg" in paragraph.lower() or "technique" in paragraph.lower() or "exercise" in paragraph.lower():
                            # Strategies section
                            formatted_paragraphs.append(f"<div class='strategies-section mb-4'><h5 class='mb-3'>Suggested Strategies</h5>{paragraph}</div>")
                        elif "reflect" in paragraph.lower() or "consider" in paragraph.lower() or "ask yourself" in paragraph.lower():
                            # Reflection section
                            formatted_paragraphs.append(f"<div class='reflection-section mb-4'><h5 class='mb-3'>Reflection Prompts</h5>{paragraph}</div>")
                        elif i == len(paragraphs) - 1 and "warmly" in paragraph.lower():
                            # Closing section
                            formatted_paragraphs.append(f"<div class='closing-section mt-4'>{paragraph}</div>")
                        else:
                            # Other paragraphs
                            formatted_paragraphs.append(f"<div class='paragraph mb-3'>{paragraph}</div>")

                    # Combine the formatted paragraphs
                    coach_response = "".join(formatted_paragraphs)

                # Get recurring patterns and add them ONLY at the end of the response
                recurring_patterns = get_recurring_patterns(user_id)
                
                # Add recurring patterns if applicable, but only at the very end
                if entry_count >= 3 and recurring_patterns:
                    # Make sure we don't already have the patterns section
                    if "We're starting to notice a few thought patterns" not in coach_response:
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

                # For new format, structured_data is the structured_response object
                # For old format, it's the previously constructed structured_data
                structured_data = result.get('structured_data', {})
                
                # If we have the new narrative format
                if has_narrative_format:
                    structured_data = result.get('structured_response', {})
                    
                    # Get the thought patterns from the structured response
                    thought_patterns = structured_data.get('thought_patterns', [])
                    if thought_patterns:
                        # Format thought patterns consistently
                        cbt_patterns = []
                        for pattern in thought_patterns:
                            if isinstance(pattern, dict):
                                cbt_patterns.append({
                                    "pattern": pattern.get('pattern', ''),
                                    "description": pattern.get('description', '')
                                })
                            elif isinstance(pattern, str):
                                cbt_patterns.append({
                                    "pattern": pattern,
                                    "description": ""
                                })
                
                # Return formatted results with structured data for UI improvements
                return {
                    "gpt_response": coach_response,
                    "cbt_patterns": cbt_patterns,
                    "structured_data": structured_data
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
                    }],
                    "structured_data": None
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
                }],
                "structured_data": None
            }
        elif "INVALID_API_KEY" in error_msg:
            logger.warning("Invalid API key for OpenAI API")
            return {
                "gpt_response": "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "API Configuration Issue",
                    "description": "The AI analysis service is currently unavailable due to a configuration issue.",
                    "recommendation": "Your journal entry has been saved successfully. Please contact the administrator to resolve this issue."
                }],
                "structured_data": None
            }
        elif "MODEL_ERROR" in error_msg:
            logger.warning("Model error for OpenAI API")
            return {
                "gpt_response": "Thank you for sharing your thoughts in this journal entry. Currently, our AI analysis feature is experiencing technical difficulties with the language model. Your entry has been saved, and we're working to resolve this issue.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "Model Configuration Issue",
                    "description": "The AI language model is currently unavailable.",
                    "recommendation": "Your journal entry has been saved successfully. Please try again later while we resolve this issue."
                }],
                "structured_data": None
            }
        elif "API_TIMEOUT" in error_msg:
            logger.warning("Timeout error for OpenAI API")
            return {
                "gpt_response": "Thank you for sharing your journal entry today. It seems our AI coach is taking a bit longer than usual to respond. Your entry has been saved, and you're welcome to try again in a few moments.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "Connection Timeout",
                    "description": "The connection to our AI service timed out.",
                    "recommendation": "Your journal entry has been saved successfully. Please try again in a few minutes when network conditions may improve."
                }],
                "structured_data": None
            }
        else:
            logger.warning(f"Unknown error for OpenAI API: {error_msg}")
            return {
                "gpt_response": "Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey. Your entry has been saved successfully.\n\nWarmly,\nCoach Mira",
                "cbt_patterns": [{
                    "pattern": "Error analyzing entry",
                    "description": "We couldn't analyze your journal entry at this time.",
                    "recommendation": "Please try again later or contact support if the problem persists."
                }],
                "structured_data": None
            }
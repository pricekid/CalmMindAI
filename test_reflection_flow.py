"""
Test script for the multi-turn reflection flow in the Dear Teddy app.
This script simulates the conversation between a user and Teddy through the journal reflection process.
"""

import json
import requests
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL for local testing
BASE_URL = "http://localhost:5000"

# Sample test data
TEST_JOURNAL_ENTRY = {
    "title": "Feeling anxious about work",
    "content": "I've been feeling really anxious about my work situation lately. There's so much pressure to perform well, and I'm worried I might not meet expectations. Every time I think about the upcoming deadline, I feel my heart racing and my thoughts spiraling. I keep thinking that if I don't do a perfect job, everyone will think I'm incompetent and I might lose my position. I know rationally that one project won't define my entire career, but emotionally it feels like everything is riding on this.",
    "anxiety_level": 7
}

TEST_REFLECTION = "When I think about it more, I realize that I've always put a lot of pressure on myself to be perfect. I think it comes from my childhood when I felt I had to be the best at everything to get attention and approval. I notice that I often catastrophize situations, assuming the worst possible outcome will happen."

TEST_FOLLOWUP_REFLECTION = "That's a really good point. I've never connected my need for perfectionism with my fear of abandonment before. I think I'm afraid that if I'm not valuable enough through my work, people will leave me or decide I'm not worth their time. Maybe I need to work on separating my self-worth from my productivity."

def login(username="test@example.com", password="password"):
    """Log in to get a session cookie"""
    logger.info("Attempting to log in...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            data={"email": username, "password": password}
        )
        
        if response.status_code == 200:
            logger.info("Login successful")
            return response.cookies
        else:
            logger.error(f"Login failed with status code {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return None

def create_journal_entry(cookies, journal_data):
    """Create a new journal entry"""
    logger.info("Creating new journal entry...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/journal/new",
            data=journal_data,
            cookies=cookies
        )
        
        if response.status_code == 200:
            logger.info("Journal entry created successfully")
            # Extract the entry ID from the redirect URL
            if 'Location' in response.headers:
                entry_id = response.headers['Location'].split('/')[-1]
                return entry_id
            else:
                # Try to parse the entry ID from the response content
                logger.info("Trying to extract entry ID from response")
                return None
        else:
            logger.error(f"Failed to create journal entry: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error creating journal entry: {str(e)}")
        return None

def submit_initial_reflection(cookies, entry_id, reflection_text):
    """Submit the initial reflection to a journal entry"""
    logger.info(f"Submitting initial reflection for entry {entry_id}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/journal/save-initial-reflection",
            json={"entry_id": entry_id, "reflection_text": reflection_text},
            cookies=cookies
        )
        
        if response.status_code == 200:
            logger.info("Initial reflection submitted successfully")
            data = response.json()
            logger.info(f"Response: {data}")
            return data.get("followup_insight")
        else:
            logger.error(f"Failed to submit initial reflection: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error submitting initial reflection: {str(e)}")
        return None

def submit_conversation_reflection(cookies, entry_id, reflection_text):
    """Submit a reflection in the conversation UI"""
    logger.info(f"Submitting conversation reflection for entry {entry_id}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/journal/{entry_id}/save-conversation-reflection",
            json={"reflection": reflection_text},
            cookies=cookies
        )
        
        if response.status_code == 200:
            logger.info("Conversation reflection submitted successfully")
            data = response.json()
            logger.info(f"Response: {data}")
            return data.get("followup_message")
        else:
            logger.error(f"Failed to submit conversation reflection: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error submitting conversation reflection: {str(e)}")
        return None

def submit_second_reflection(cookies, entry_id, reflection_text):
    """Submit the second reflection to a journal entry"""
    logger.info(f"Submitting second reflection for entry {entry_id}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/journal/save-second-reflection",
            json={"entry_id": entry_id, "reflection_text": reflection_text},
            cookies=cookies
        )
        
        if response.status_code == 200:
            logger.info("Second reflection submitted successfully")
            data = response.json()
            logger.info(f"Response: {data}")
            return data.get("closing_message")
        else:
            logger.error(f"Failed to submit second reflection: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error submitting second reflection: {str(e)}")
        return None

def main():
    """Main test function that runs through the conversation flow"""
    logger.info("Starting reflection flow test...")
    
    # Step 1: Login
    cookies = login()
    if not cookies:
        logger.error("Test failed: Could not log in")
        return
    
    # Step 2: Create a journal entry (or use an existing one)
    entry_id = create_journal_entry(cookies, TEST_JOURNAL_ENTRY)
    if not entry_id:
        logger.error("Test failed: Could not create journal entry")
        return
    
    logger.info(f"Working with journal entry ID: {entry_id}")
    
    # Step 3: Submit initial reflection and get Teddy's response
    followup_insight = submit_initial_reflection(cookies, entry_id, TEST_REFLECTION)
    if not followup_insight:
        logger.error("Test failed: No followup insight received")
    else:
        logger.info(f"Teddy's initial response: {followup_insight[:100]}...")
    
    # Step 4: Submit followup reflection in conversation UI
    followup_message = submit_conversation_reflection(cookies, entry_id, TEST_FOLLOWUP_REFLECTION)
    if not followup_message:
        logger.error("Test failed: No followup message received")
    else:
        logger.info(f"Teddy's followup response: {followup_message[:100]}...")
    
    # Step 5: Submit another reflection to continue the conversation
    second_followup = submit_conversation_reflection(cookies, entry_id, "I think that's exactly right. I'm going to try to focus more on my intrinsic value rather than what I produce.")
    if not second_followup:
        logger.error("Test failed: No second followup received")
    else:
        logger.info(f"Teddy's second followup: {second_followup[:100]}...")
    
    # Step 6: Submit a final reflection to close the conversation
    closing_message = submit_second_reflection(cookies, entry_id, "This conversation has been really helpful. I feel like I understand my anxiety patterns better now.")
    if not closing_message:
        logger.error("Test failed: No closing message received")
    else:
        logger.info(f"Teddy's closing message: {closing_message[:100]}...")
    
    logger.info("Reflection flow test completed")

if __name__ == "__main__":
    main()
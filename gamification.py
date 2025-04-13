"""
Gamification system for Calm Journey.
This module provides badges, achievements, and streak tracking to enhance user engagement.
"""
import json
import os
import logging
from datetime import datetime, timedelta
from flask import flash

# Configure logging
logger = logging.getLogger(__name__)

# Ensure data directory exists
def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/badges'):
        os.makedirs('data/badges')

# Define badge types and their properties
BADGE_DEFINITIONS = {
    # Streak badges
    'streak_3': {
        'name': '3-Day Streak',
        'description': 'You journaled for 3 consecutive days!',
        'icon': 'fa-fire',
        'color': '#FF9500',
        'requirement': 3,
        'type': 'streak',
        'hint': 'Journal for 3 days in a row'
    },
    'streak_7': {
        'name': '7-Day Streak',
        'description': 'You maintained a full week of journaling!',
        'icon': 'fa-fire-alt',
        'color': '#FF5E3A',
        'requirement': 7,
        'type': 'streak',
        'hint': 'Journal for 7 days in a row'
    },
    'streak_14': {
        'name': '2-Week Streak',
        'description': 'Two consistent weeks of reflection!',
        'icon': 'fa-burn',
        'color': '#FF2D55',
        'requirement': 14,
        'type': 'streak',
        'hint': 'Journal for 14 days in a row'
    },
    'streak_30': {
        'name': 'Monthly Dedicated',
        'description': 'A full month of consistent journaling!',
        'icon': 'fa-crown',
        'color': '#AF52DE',
        'requirement': 30,
        'type': 'streak',
        'hint': 'Journal for 30 days in a row'
    },
    
    # Journal entry count badges
    'entries_5': {
        'name': 'Getting Started',
        'description': 'You completed 5 journal entries!',
        'icon': 'fa-book-open',
        'color': '#34C759',
        'requirement': 5,
        'type': 'entries',
        'hint': 'Create 5 journal entries'
    },
    'entries_20': {
        'name': 'Consistent Journaler',
        'description': 'You completed 20 journal entries!',
        'icon': 'fa-books',
        'color': '#30B0C7',
        'requirement': 20,
        'type': 'entries',
        'hint': 'Create 20 journal entries'
    },
    'entries_50': {
        'name': 'Journaling Expert',
        'description': 'You completed 50 journal entries!',
        'icon': 'fa-journal-whills',
        'color': '#5856D6',
        'requirement': 50,
        'type': 'entries',
        'hint': 'Create 50 journal entries'
    },
    
    # Special action badges
    'first_cbt_insight': {
        'name': 'Pattern Spotter',
        'description': 'You identified your first thought pattern!',
        'icon': 'fa-lightbulb',
        'color': '#FFCC00',
        'requirement': 1,
        'type': 'insight',
        'hint': 'Analyze a journal entry with AI insights'
    },
    'mood_tracker_5': {
        'name': 'Mood Tracking Pro',
        'description': 'You tracked your mood 5 times!',
        'icon': 'fa-chart-line',
        'color': '#007AFF',
        'requirement': 5,
        'type': 'mood',
        'hint': 'Track your mood 5 times'
    },
    'breathing_session': {
        'name': 'Breath Mindfully',
        'description': 'You completed your first breathing exercise!',
        'icon': 'fa-wind',
        'color': '#64D2FF',
        'requirement': 1,
        'type': 'breathing',
        'hint': 'Complete a guided breathing exercise'
    }
}

# Motivational streak facts
STREAK_FACTS = [
    "Journaling for just 5 minutes daily creates new neural pathways that improve emotional regulation.",
    "Regular journaling helps move thoughts from your emotional brain (amygdala) to your rational brain (prefrontal cortex).",
    "Studies show that journaling can reduce stress by decreasing the activity in your amygdala, the brain's emotional center.",
    "Consistent journaling can increase your brain's theta wave activity, which is associated with deep relaxation and learning.",
    "Writing regularly actually strengthens immune cells called T-lymphocytes, helping you stay physically healthier.",
    "The act of writing activates the reticular activating system (RAS), helping your brain to focus on what matters most.",
    "When you journal consistently, your brain forms new neural pathways that make emotional processing more efficient.",
    "The physical act of writing by hand activates areas of the brain that help you process emotions more effectively."
]

def get_user_badges(user_id):
    """
    Get all badge data for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Badge data and streak information
    """
    ensure_data_directory()
    
    # Initialize badge data
    badge_data = {
        'badge_details': {},
        'earned_badges': [],
        'current_streak': 0,
        'longest_streak': 0,
        'streak_fact': STREAK_FACTS[0],  # Default streak fact
        'next_streak_badge': None
    }
    
    # Create badge details from definitions
    for badge_id, details in BADGE_DEFINITIONS.items():
        badge_data['badge_details'][badge_id] = {
            'name': details['name'],
            'description': details['description'],
            'icon': details['icon'],
            'color': details['color'],
            'requirement': details['requirement'],
            'type': details['type'],
            'hint': details.get('hint', 'Keep using Calm Journey'),
            'earned': False,
            'earned_date': None
        }
    
    # Load user's badge data if it exists
    badge_file = f'data/badges/user_{user_id}_badges.json'
    
    if os.path.exists(badge_file):
        try:
            with open(badge_file, 'r') as f:
                user_badge_data = json.load(f)
                
            # Update earned status from saved data
            if 'earned_badges' in user_badge_data:
                badge_data['earned_badges'] = user_badge_data['earned_badges']
                
                for badge_id in user_badge_data['earned_badges']:
                    if badge_id in badge_data['badge_details']:
                        badge_data['badge_details'][badge_id]['earned'] = True
                        badge_data['badge_details'][badge_id]['earned_date'] = user_badge_data.get('earned_dates', {}).get(badge_id, 'Unknown date')
            
            # Get streak information
            badge_data['current_streak'] = user_badge_data.get('current_streak', 0)
            badge_data['longest_streak'] = user_badge_data.get('longest_streak', 0)
            
            # Select a streak fact based on the streak length
            streak_index = min(len(STREAK_FACTS) - 1, badge_data['current_streak'] // 3)
            badge_data['streak_fact'] = STREAK_FACTS[streak_index]
            
            # Find the next streak badge to earn
            for badge_id, details in badge_data['badge_details'].items():
                if (details['type'] == 'streak' and 
                    not details['earned'] and 
                    details['requirement'] > badge_data['current_streak']):
                    # Sort badges by requirement to find the next achievable one
                    if (badge_data['next_streak_badge'] is None or 
                        details['requirement'] < badge_data['next_streak_badge']['requirement']):
                        badge_data['next_streak_badge'] = details
                        
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading badge data for user {user_id}: {str(e)}")
            # Continue with default empty badge data
    
    return badge_data

def process_journal_entry(user_id):
    """
    Process a new journal entry and award badges as appropriate.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Updated badge data and any newly earned badges
    """
    ensure_data_directory()
    
    # Load journal entries for the user
    journal_entries = get_journal_entries(user_id)
    entry_count = len(journal_entries)
    
    # Load or initialize user badge data
    badge_file = f'data/badges/user_{user_id}_badges.json'
    
    if os.path.exists(badge_file):
        try:
            with open(badge_file, 'r') as f:
                user_badge_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            user_badge_data = {
                'earned_badges': [],
                'earned_dates': {},
                'current_streak': 0,
                'longest_streak': 0,
                'last_entry_date': None
            }
    else:
        user_badge_data = {
            'earned_badges': [],
            'earned_dates': {},
            'current_streak': 0,
            'longest_streak': 0,
            'last_entry_date': None
        }
    
    # Update streak
    today = datetime.now().date()
    last_entry_date_str = user_badge_data.get('last_entry_date')
    
    if last_entry_date_str:
        try:
            last_entry_date = datetime.strptime(last_entry_date_str, '%Y-%m-%d').date()
            days_diff = (today - last_entry_date).days
            
            if days_diff == 1:
                # Consecutive day, increment streak
                user_badge_data['current_streak'] += 1
            elif days_diff == 0:
                # Same day entry, no streak change
                pass
            else:
                # Streak broken
                user_badge_data['current_streak'] = 1
        except ValueError:
            # Invalid date format, reset streak
            user_badge_data['current_streak'] = 1
    else:
        # First entry, start streak at 1
        user_badge_data['current_streak'] = 1
    
    # Update longest streak if needed
    if user_badge_data['current_streak'] > user_badge_data.get('longest_streak', 0):
        user_badge_data['longest_streak'] = user_badge_data['current_streak']
    
    # Update last entry date
    user_badge_data['last_entry_date'] = today.strftime('%Y-%m-%d')
    
    # Check for new badges to award
    current_streak = user_badge_data['current_streak']
    newly_earned_badges = []
    
    # Check streak badges
    for badge_id, details in BADGE_DEFINITIONS.items():
        if details['type'] == 'streak' and details['requirement'] <= current_streak:
            if badge_id not in user_badge_data['earned_badges']:
                user_badge_data['earned_badges'].append(badge_id)
                user_badge_data['earned_dates'][badge_id] = today.strftime('%B %d, %Y')
                newly_earned_badges.append(badge_id)
    
    # Check entry count badges
    for badge_id, details in BADGE_DEFINITIONS.items():
        if details['type'] == 'entries' and details['requirement'] <= entry_count:
            if badge_id not in user_badge_data['earned_badges']:
                user_badge_data['earned_badges'].append(badge_id)
                user_badge_data['earned_dates'][badge_id] = today.strftime('%B %d, %Y')
                newly_earned_badges.append(badge_id)
    
    # Check if this is the first analyzed entry (for insight badge)
    has_analyzed = False
    for entry in journal_entries:
        if entry.get('is_analyzed'):
            has_analyzed = True
            break
    
    if has_analyzed and 'first_cbt_insight' not in user_badge_data['earned_badges']:
        user_badge_data['earned_badges'].append('first_cbt_insight')
        user_badge_data['earned_dates']['first_cbt_insight'] = today.strftime('%B %d, %Y')
        newly_earned_badges.append('first_cbt_insight')
    
    # Save updated badge data
    with open(badge_file, 'w') as f:
        json.dump(user_badge_data, f, indent=2)
    
    # Get complete badge data to return
    badge_data = get_user_badges(user_id)
    badge_data['new_badges'] = newly_earned_badges
    
    return badge_data

def get_journal_entries(user_id):
    """
    Get journal entries for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        list: Journal entries for the user
    """
    journal_file = f'data/user_{user_id}_journals.json'
    
    if not os.path.exists(journal_file):
        return []
    
    try:
        with open(journal_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def check_streak_status(user_id):
    """
    Check if the user's streak is at risk of breaking.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Streak status information
    """
    badge_file = f'data/badges/user_{user_id}_badges.json'
    
    if not os.path.exists(badge_file):
        return {'status': 'none', 'message': 'No streak yet'}
    
    try:
        with open(badge_file, 'r') as f:
            user_badge_data = json.load(f)
        
        last_entry_date_str = user_badge_data.get('last_entry_date')
        
        if not last_entry_date_str:
            return {'status': 'none', 'message': 'No streak yet'}
        
        last_entry_date = datetime.strptime(last_entry_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        days_diff = (today - last_entry_date).days
        
        if days_diff == 0:
            return {'status': 'active', 'message': 'Streak active and secure for today'}
        elif days_diff == 1:
            return {'status': 'warning', 'message': 'Journal today to keep your streak!'}
        else:
            return {'status': 'broken', 'message': f'Streak broken after {days_diff} days'}
        
    except (json.JSONDecodeError, FileNotFoundError, ValueError):
        return {'status': 'none', 'message': 'No streak information available'}

def flash_badge_notifications(badge_result):
    """
    Flash notifications for newly earned badges.
    
    Args:
        badge_result: Badge data from process_journal_entry()
    """
    if not badge_result.get('new_badges'):
        return
    
    new_badges = badge_result['new_badges']
    badge_details = badge_result['badge_details']
    
    for badge_id in new_badges:
        if badge_id in badge_details:
            badge = badge_details[badge_id]
            message = f"🏆 Achievement unlocked: {badge['name']} - {badge['description']}"
            
            # Add motivational message for streak badges
            if badge_id.startswith('streak_'):
                days = badge['requirement']
                if days == 3:
                    message += " That kind of consistency rewires anxiety."
                elif days == 7:
                    message += " A full week of reflection builds powerful self-awareness."
                elif days == 14:
                    message += " Two weeks of practice is creating lasting neural pathways."
                elif days == 30:
                    message += " You've built a life-changing habit!"
            
            flash(message, 'success')

def process_breathing_session(user_id):
    """
    Process a completed breathing session and award the breathing badge if appropriate.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Updated badge data and any newly earned badges
    """
    ensure_data_directory()
    
    # Load or initialize user badge data
    badge_file = f'data/badges/user_{user_id}_badges.json'
    
    if os.path.exists(badge_file):
        try:
            with open(badge_file, 'r') as f:
                user_badge_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            user_badge_data = {
                'earned_badges': [],
                'earned_dates': {},
                'current_streak': 0,
                'longest_streak': 0,
                'last_entry_date': None
            }
    else:
        user_badge_data = {
            'earned_badges': [],
            'earned_dates': {},
            'current_streak': 0,
            'longest_streak': 0,
            'last_entry_date': None
        }
    
    # Check if breathing badge already earned
    newly_earned_badges = []
    today = datetime.now().date()
    
    if 'breathing_session' not in user_badge_data['earned_badges']:
        user_badge_data['earned_badges'].append('breathing_session')
        user_badge_data['earned_dates']['breathing_session'] = today.strftime('%B %d, %Y')
        newly_earned_badges.append('breathing_session')
        
        # Save updated badge data
        with open(badge_file, 'w') as f:
            json.dump(user_badge_data, f, indent=2)
    
    # Get complete badge data to return
    badge_data = get_user_badges(user_id)
    badge_data['new_badges'] = newly_earned_badges
    
    return badge_data

def process_mood_log(user_id):
    """
    Process a mood log entry and award the mood tracking badge if appropriate.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Updated badge data and any newly earned badges
    """
    ensure_data_directory()
    
    # Load mood logs for the user - this is a simplification, in reality you'd query the database
    mood_logs = get_mood_logs(user_id)
    mood_count = len(mood_logs)
    
    # Load or initialize user badge data
    badge_file = f'data/badges/user_{user_id}_badges.json'
    
    if os.path.exists(badge_file):
        try:
            with open(badge_file, 'r') as f:
                user_badge_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            user_badge_data = {
                'earned_badges': [],
                'earned_dates': {},
                'current_streak': 0,
                'longest_streak': 0,
                'last_entry_date': None
            }
    else:
        user_badge_data = {
            'earned_badges': [],
            'earned_dates': {},
            'current_streak': 0,
            'longest_streak': 0,
            'last_entry_date': None
        }
    
    # Check for mood tracking badge
    newly_earned_badges = []
    today = datetime.now().date()
    
    if mood_count >= 5 and 'mood_tracker_5' not in user_badge_data['earned_badges']:
        user_badge_data['earned_badges'].append('mood_tracker_5')
        user_badge_data['earned_dates']['mood_tracker_5'] = today.strftime('%B %d, %Y')
        newly_earned_badges.append('mood_tracker_5')
        
        # Save updated badge data
        with open(badge_file, 'w') as f:
            json.dump(user_badge_data, f, indent=2)
    
    # Get complete badge data to return
    badge_data = get_user_badges(user_id)
    badge_data['new_badges'] = newly_earned_badges
    
    return badge_data

def get_mood_logs(user_id):
    """
    Placeholder function to get mood logs.
    In a real implementation, this would query the database.
    
    Args:
        user_id: The user's ID
        
    Returns:
        list: Mood logs for the user
    """
    # This is a simplified version - in reality you'd query the database
    return []
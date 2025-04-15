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

# XP (Experience Points) Rewards for activities
XP_REWARDS = {
    'journal_entry': 10,      # Points for creating a journal entry
    'mood_log': 5,            # Points for logging mood
    'streak_day': 5,          # Additional points per day of streak
    'streak_milestone': 20,   # Extra points for streak milestones (3, 7, 14, 30 days)
    'badge_earned': 25,       # Points for earning a badge
    'breathing': 15,          # Points for completing a breathing exercise
    'analysis': 20,           # Points for analyzing an entry
    'daily_bonus': 5,         # Daily login bonus
}

# Level definitions (Duolingo style)
LEVEL_DEFINITIONS = [
    {'level': 1, 'name': 'Beginner', 'xp_required': 0, 'color': '#A0D6B4'},       # Light green
    {'level': 2, 'name': 'Explorer', 'xp_required': 50, 'color': '#5DB075'},      # Green
    {'level': 3, 'name': 'Enthusiast', 'xp_required': 120, 'color': '#47B881'},   # Darker green
    {'level': 4, 'name': 'Dedicated', 'xp_required': 250, 'color': '#26A65B'},    # Rich green
    {'level': 5, 'name': 'Focused', 'xp_required': 400, 'color': '#1E90FF'},      # Blue
    {'level': 6, 'name': 'Committed', 'xp_required': 600, 'color': '#1A75FF'},    # Richer blue
    {'level': 7, 'name': 'Diligent', 'xp_required': 850, 'color': '#0066CC'},     # Deep blue
    {'level': 8, 'name': 'Resilient', 'xp_required': 1150, 'color': '#9370DB'},   # Purple
    {'level': 9, 'name': 'Persistent', 'xp_required': 1500, 'color': '#8A2BE2'},  # Violet
    {'level': 10, 'name': 'Master', 'xp_required': 2000, 'color': '#FF6347'},     # Tomato red
    {'level': 11, 'name': 'Guru', 'xp_required': 2600, 'color': '#FF4500'},       # Orange red
    {'level': 12, 'name': 'Sage', 'xp_required': 3300, 'color': '#FF8C00'},       # Dark orange
    {'level': 13, 'name': 'Expert', 'xp_required': 4100, 'color': '#FFD700'},     # Gold
    {'level': 14, 'name': 'Champion', 'xp_required': 5000, 'color': '#FFC125'},   # Goldenrod
    {'level': 15, 'name': 'Legend', 'xp_required': 6000, 'color': '#FF1493'},     # Pink
]

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
        'hint': 'Journal for 3 days in a row',
        'xp_reward': 30
    },
    'streak_7': {
        'name': '7-Day Streak',
        'description': 'You maintained a full week of journaling!',
        'icon': 'fa-fire-alt',
        'color': '#FF5E3A',
        'requirement': 7,
        'type': 'streak',
        'hint': 'Journal for 7 days in a row',
        'xp_reward': 50
    },
    'streak_14': {
        'name': '2-Week Streak',
        'description': 'Two consistent weeks of reflection!',
        'icon': 'fa-burn',
        'color': '#FF2D55',
        'requirement': 14,
        'type': 'streak',
        'hint': 'Journal for 14 days in a row',
        'xp_reward': 100
    },
    'streak_30': {
        'name': 'Monthly Dedicated',
        'description': 'A full month of consistent journaling!',
        'icon': 'fa-crown',
        'color': '#AF52DE',
        'requirement': 30,
        'type': 'streak',
        'hint': 'Journal for 30 days in a row',
        'xp_reward': 200
    },
    
    # Journal entry count badges
    'entries_5': {
        'name': 'Getting Started',
        'description': 'You completed 5 journal entries!',
        'icon': 'fa-book-open',
        'color': '#34C759',
        'requirement': 5,
        'type': 'entries',
        'hint': 'Create 5 journal entries',
        'xp_reward': 40
    },
    'entries_20': {
        'name': 'Consistent Journaler',
        'description': 'You completed 20 journal entries!',
        'icon': 'fa-books',
        'color': '#30B0C7',
        'requirement': 20,
        'type': 'entries',
        'hint': 'Create 20 journal entries',
        'xp_reward': 80
    },
    'entries_50': {
        'name': 'Journaling Expert',
        'description': 'You completed 50 journal entries!',
        'icon': 'fa-journal-whills',
        'color': '#5856D6',
        'requirement': 50,
        'type': 'entries',
        'hint': 'Create 50 journal entries',
        'xp_reward': 150
    },
    
    # Special action badges
    'first_cbt_insight': {
        'name': 'Pattern Spotter',
        'description': 'You identified your first thought pattern!',
        'icon': 'fa-lightbulb',
        'color': '#FFCC00',
        'requirement': 1,
        'type': 'insight',
        'hint': 'Analyze a journal entry with AI insights',
        'xp_reward': 25
    },
    'mood_tracker_5': {
        'name': 'Mood Tracking Pro',
        'description': 'You tracked your mood 5 times!',
        'icon': 'fa-chart-line',
        'color': '#007AFF',
        'requirement': 5,
        'type': 'mood',
        'hint': 'Track your mood 5 times',
        'xp_reward': 35
    },
    'breathing_session': {
        'name': 'Breath Mindfully',
        'description': 'You completed your first breathing exercise!',
        'icon': 'fa-wind',
        'color': '#64D2FF',
        'requirement': 1,
        'type': 'breathing',
        'hint': 'Complete a guided breathing exercise',
        'xp_reward': 20
    },
    
    # New Duolingo-style badges
    'perfect_week': {
        'name': 'Perfect Week',
        'description': 'You journaled every day for a full week!',
        'icon': 'fa-calendar-check',
        'color': '#FFD700',  # Gold
        'requirement': 7,
        'type': 'perfect_week',
        'hint': 'Journal every day for 7 consecutive days',
        'xp_reward': 100
    },
    'anxiety_reduction': {
        'name': 'Anxiety Reducer',
        'description': 'You reduced your anxiety levels over time!',
        'icon': 'fa-heart',
        'color': '#FF6B6B',  # Coral
        'requirement': 1,
        'type': 'progress',
        'hint': 'Show improvement in anxiety levels over time',
        'xp_reward': 75
    },
    'daily_login_3': {
        'name': 'Regular Check-in',
        'description': 'You logged in 3 days in a row!',
        'icon': 'fa-calendar-day',
        'color': '#5CBBF6',  # Light blue
        'requirement': 3,
        'type': 'login',
        'hint': 'Log in 3 days in a row',
        'xp_reward': 15
    },
    'daily_login_7': {
        'name': 'Consistent Check-in',
        'description': 'You logged in 7 days in a row!',
        'icon': 'fa-calendar-week',
        'color': '#3B82F6',  # Medium blue
        'requirement': 7,
        'type': 'login',
        'hint': 'Log in 7 days in a row',
        'xp_reward': 35
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

def get_user_xp(user_id):
    """
    Get a user's XP (Experience Points) level data.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: XP data including total XP, current level, and progress
    """
    # Load or initialize user badge data which contains XP
    badge_file = f'data/badges/user_{user_id}_badges.json'
    
    xp_data = {
        'total_xp': 0,
        'level': 1,
        'level_name': LEVEL_DEFINITIONS[0]['name'],
        'level_color': LEVEL_DEFINITIONS[0]['color'],
        'next_level': 2,
        'next_level_name': LEVEL_DEFINITIONS[1]['name'] if len(LEVEL_DEFINITIONS) > 1 else None,
        'xp_for_next_level': LEVEL_DEFINITIONS[1]['xp_required'] if len(LEVEL_DEFINITIONS) > 1 else None,
        'xp_needed': LEVEL_DEFINITIONS[1]['xp_required'] if len(LEVEL_DEFINITIONS) > 1 else 0,
        'progress_percent': 0
    }
    
    if os.path.exists(badge_file):
        try:
            with open(badge_file, 'r') as f:
                user_badge_data = json.load(f)
                
            # Get total XP (default to 0 if not found)
            total_xp = user_badge_data.get('total_xp', 0)
            xp_data['total_xp'] = total_xp
            
            # Find current level based on XP
            current_level = 1
            for level_def in LEVEL_DEFINITIONS:
                if total_xp >= level_def['xp_required']:
                    current_level = level_def['level']
                    xp_data['level'] = current_level
                    xp_data['level_name'] = level_def['name']
                    xp_data['level_color'] = level_def['color']
                else:
                    break
            
            # Find next level information
            if current_level < len(LEVEL_DEFINITIONS):
                next_level_def = LEVEL_DEFINITIONS[current_level]  # Level is 1-based, array is 0-based
                xp_data['next_level'] = next_level_def['level']
                xp_data['next_level_name'] = next_level_def['name']
                xp_data['xp_for_next_level'] = next_level_def['xp_required']
                
                # Calculate XP needed for next level
                xp_data['xp_needed'] = next_level_def['xp_required'] - total_xp
                
                # Calculate progress percentage to next level
                current_level_xp = LEVEL_DEFINITIONS[current_level-1]['xp_required']
                xp_in_current_level = total_xp - current_level_xp
                xp_needed_for_level = next_level_def['xp_required'] - current_level_xp
                xp_data['progress_percent'] = min(100, int((xp_in_current_level / xp_needed_for_level) * 100))
            else:
                # Max level reached
                xp_data['next_level'] = None
                xp_data['next_level_name'] = "Max Level"
                xp_data['xp_for_next_level'] = None
                xp_data['xp_needed'] = 0
                xp_data['progress_percent'] = 100
                
        except (json.JSONDecodeError, FileNotFoundError, KeyError, ZeroDivisionError) as e:
            logger.error(f"Error loading XP data for user {user_id}: {str(e)}")
    
    return xp_data

def award_xp(user_id, xp_amount, reason=None):
    """
    Award XP to a user and update their level if necessary.
    
    Args:
        user_id: The user's ID
        xp_amount: Amount of XP to award
        reason: Optional reason for the XP award (for logging)
        
    Returns:
        dict: Updated XP data including level up information if applicable
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
                'last_entry_date': None,
                'total_xp': 0,
                'xp_history': []
            }
    else:
        user_badge_data = {
            'earned_badges': [],
            'earned_dates': {},
            'current_streak': 0,
            'longest_streak': 0,
            'last_entry_date': None,
            'total_xp': 0,
            'xp_history': []
        }
    
    # Get previous level
    old_xp = user_badge_data.get('total_xp', 0)
    old_level = 1
    for level_def in LEVEL_DEFINITIONS:
        if old_xp >= level_def['xp_required']:
            old_level = level_def['level']
        else:
            break
    
    # Add XP
    user_badge_data['total_xp'] = old_xp + xp_amount
    
    # Record XP history
    if 'xp_history' not in user_badge_data:
        user_badge_data['xp_history'] = []
    
    # Add XP history entry
    xp_entry = {
        'amount': xp_amount,
        'reason': reason or 'Activity completed',
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    user_badge_data['xp_history'].append(xp_entry)
    
    # Trim history if it gets too long (keep last 50 entries)
    if len(user_badge_data['xp_history']) > 50:
        user_badge_data['xp_history'] = user_badge_data['xp_history'][-50:]
    
    # Check for level up
    new_xp = user_badge_data['total_xp']
    new_level = 1
    for level_def in LEVEL_DEFINITIONS:
        if new_xp >= level_def['xp_required']:
            new_level = level_def['level']
        else:
            break
    
    # Save updated data
    with open(badge_file, 'w') as f:
        json.dump(user_badge_data, f, indent=2)
    
    # Get complete XP data
    xp_data = get_user_xp(user_id)
    
    # Add level up information if applicable
    xp_data['leveled_up'] = new_level > old_level
    xp_data['levels_gained'] = new_level - old_level
    xp_data['xp_gained'] = xp_amount
    
    return xp_data

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
        'next_streak_badge': None,
        'xp_data': get_user_xp(user_id)  # Add XP data
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
"""
Gamification module for Calm Journey.
Handles badges, streaks, and achievement notifications.
"""
import logging
import json
import os
from datetime import datetime, timedelta
from flask import flash, render_template
from app import db
from models import User, JournalEntry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Badge definitions with mental wellness messaging
BADGES = {
    "streak_3": {
        "name": "Consistency Builder",
        "description": "Journaled 3 days in a row. This kind of consistency rewires anxiety patterns.",
        "icon": "fa-seedling",
        "color": "#7fad7b"  # soft green
    },
    "streak_7": {
        "name": "Habit Former",
        "description": "A full week of journaling. You're building neural pathways for emotional regulation.",
        "icon": "fa-pagelines",
        "color": "#5f9ea0"  # teal
    },
    "streak_14": {
        "name": "Mindfulness Master",
        "description": "Two weeks of consistent reflection. Your brain is strengthening its self-awareness centers.",
        "icon": "fa-tree",
        "color": "#6a8caf"  # soft blue
    },
    "streak_30": {
        "name": "Emotional Insight Champion",
        "description": "A full month of journaling! Research shows this level of practice significantly reduces stress levels.",
        "icon": "fa-mountain",
        "color": "#9370db"  # medium purple
    },
    "entries_5": {
        "name": "Self-Reflection Starter",
        "description": "Completed 5 journal entries. Each entry helps process emotions more effectively.",
        "icon": "fa-book-open",
        "color": "#d4a76a"  # warm peach/tan
    },
    "entries_20": {
        "name": "Thought Pattern Observer",
        "description": "20 entries complete. You're developing the ability to observe thoughts without judgment.",
        "icon": "fa-brain",
        "color": "#c27ba0"  # mauve
    },
    "entries_50": {
        "name": "Emotional Intelligence Cultivator",
        "description": "50 entries! You've created a valuable record of your emotional journey and insights.",
        "icon": "fa-gem",
        "color": "#8e6c88"  # dusty purple
    },
    "first_cbt_insight": {
        "name": "Insight Seeker",
        "description": "Received your first AI-powered insight. Recognizing patterns is the first step to changing them.",
        "icon": "fa-lightbulb",
        "color": "#ffd700"  # gold
    },
    "mood_tracker_5": {
        "name": "Emotion Tracker",
        "description": "Tracked your mood 5 times. Naming emotions reduces their intensity by up to 50%.",
        "icon": "fa-chart-line",
        "color": "#5d8aa8"  # air force blue
    },
    "breathing_session": {
        "name": "Breath Awareness",
        "description": "Completed a breathing exercise. Controlled breathing activates your parasympathetic nervous system.",
        "icon": "fa-wind",
        "color": "#89cff0"  # baby blue
    }
}

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')

def ensure_user_badge_tracking():
    """Ensure the badges.json file exists"""
    ensure_data_directory()
    if not os.path.exists('data/badges.json'):
        with open('data/badges.json', 'w') as f:
            json.dump({}, f)

def get_user_badge_data(user_id):
    """
    Get badge data for a specific user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: The user's badge data
    """
    ensure_user_badge_tracking()
    
    try:
        with open('data/badges.json', 'r') as f:
            all_badges = json.load(f)
            
        # Convert user_id to string for JSON dictionary keys
        user_id_str = str(user_id)
        
        # Initialize if not present
        if user_id_str not in all_badges:
            all_badges[user_id_str] = {
                "earned_badges": [],
                "current_streak": 0,
                "longest_streak": 0,
                "last_entry_date": None,
                "entry_count": 0,
                "mood_log_count": 0,
                "breathing_sessions": 0,
                "cbt_insights_received": 0,
                "shown_badges": []  # Tracks badges already shown to the user
            }
            
            # Save the initialized data
            with open('data/badges.json', 'w') as f:
                json.dump(all_badges, f, indent=2)
        
        return all_badges[user_id_str]
    except Exception as e:
        logger.error(f"Error getting badge data: {str(e)}")
        return {
            "earned_badges": [],
            "current_streak": 0,
            "longest_streak": 0,
            "last_entry_date": None,
            "entry_count": 0,
            "mood_log_count": 0,
            "breathing_sessions": 0,
            "cbt_insights_received": 0,
            "shown_badges": []
        }

def save_user_badge_data(user_id, badge_data):
    """
    Save badge data for a specific user.
    
    Args:
        user_id: The user's ID
        badge_data: The user's badge data to save
    """
    ensure_user_badge_tracking()
    
    try:
        with open('data/badges.json', 'r') as f:
            all_badges = json.load(f)
        
        # Convert user_id to string for JSON dictionary keys
        user_id_str = str(user_id)
        
        # Update the user's badge data
        all_badges[user_id_str] = badge_data
        
        # Save all badge data
        with open('data/badges.json', 'w') as f:
            json.dump(all_badges, f, indent=2)
            
        return True
    except Exception as e:
        logger.error(f"Error saving badge data: {str(e)}")
        return False

def process_journal_entry(user_id):
    """
    Process a new journal entry, update streaks and check for new badges.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Information about any new badges earned
    """
    badge_data = get_user_badge_data(user_id)
    today = datetime.now().date()
    new_badges = []
    
    # Update entry count
    badge_data["entry_count"] += 1
    entry_count = badge_data["entry_count"]
    
    # Check if this is a new day compared to the last entry
    last_entry_date = None
    if badge_data["last_entry_date"]:
        try:
            # Parse the stored date string
            last_entry_date = datetime.strptime(badge_data["last_entry_date"], "%Y-%m-%d").date()
        except:
            last_entry_date = None
    
    # Update streak information
    if last_entry_date is None:
        # First journal entry
        badge_data["current_streak"] = 1
        badge_data["longest_streak"] = 1
    elif last_entry_date == today:
        # Already journaled today, no streak update needed
        pass
    elif last_entry_date == today - timedelta(days=1):
        # Yesterday, increment streak
        badge_data["current_streak"] += 1
        if badge_data["current_streak"] > badge_data["longest_streak"]:
            badge_data["longest_streak"] = badge_data["current_streak"]
    else:
        # Broken streak (more than 1 day gap)
        badge_data["current_streak"] = 1
    
    # Save today as the last entry date
    badge_data["last_entry_date"] = today.strftime("%Y-%m-%d")
    
    # Check for streak badges
    streak_milestones = [3, 7, 14, 30]
    current_streak = badge_data["current_streak"]
    
    for milestone in streak_milestones:
        badge_id = f"streak_{milestone}"
        if current_streak >= milestone and badge_id not in badge_data["earned_badges"]:
            badge_data["earned_badges"].append(badge_id)
            if badge_id not in badge_data["shown_badges"]:
                new_badges.append(badge_id)
                badge_data["shown_badges"].append(badge_id)
    
    # Check for entry count badges
    entry_milestones = [5, 20, 50]
    
    for milestone in entry_milestones:
        badge_id = f"entries_{milestone}"
        if entry_count >= milestone and badge_id not in badge_data["earned_badges"]:
            badge_data["earned_badges"].append(badge_id)
            if badge_id not in badge_data["shown_badges"]:
                new_badges.append(badge_id)
                badge_data["shown_badges"].append(badge_id)
    
    # Save updated badge data
    save_user_badge_data(user_id, badge_data)
    
    # Return information about new badges
    result = {
        "new_badges": new_badges,
        "badge_details": {badge_id: BADGES[badge_id] for badge_id in new_badges} if new_badges else {}
    }
    
    return result

def process_cbt_insight(user_id):
    """
    Process a new CBT insight, check for related badges.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Information about any new badges earned
    """
    badge_data = get_user_badge_data(user_id)
    new_badges = []
    
    # Update insights count
    badge_data["cbt_insights_received"] += 1
    
    # Check for first insight badge
    badge_id = "first_cbt_insight"
    if badge_data["cbt_insights_received"] == 1 and badge_id not in badge_data["earned_badges"]:
        badge_data["earned_badges"].append(badge_id)
        if badge_id not in badge_data["shown_badges"]:
            new_badges.append(badge_id)
            badge_data["shown_badges"].append(badge_id)
    
    # Save updated badge data
    save_user_badge_data(user_id, badge_data)
    
    # Return information about new badges
    result = {
        "new_badges": new_badges,
        "badge_details": {badge_id: BADGES[badge_id] for badge_id in new_badges} if new_badges else {}
    }
    
    return result

def process_mood_log(user_id):
    """
    Process a new mood log, check for related badges.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Information about any new badges earned
    """
    badge_data = get_user_badge_data(user_id)
    new_badges = []
    
    # Update mood log count
    badge_data["mood_log_count"] += 1
    
    # Check for mood tracking badge
    if badge_data["mood_log_count"] >= 5:
        badge_id = "mood_tracker_5"
        if badge_id not in badge_data["earned_badges"]:
            badge_data["earned_badges"].append(badge_id)
            if badge_id not in badge_data["shown_badges"]:
                new_badges.append(badge_id)
                badge_data["shown_badges"].append(badge_id)
    
    # Save updated badge data
    save_user_badge_data(user_id, badge_data)
    
    # Return information about new badges
    result = {
        "new_badges": new_badges,
        "badge_details": {badge_id: BADGES[badge_id] for badge_id in new_badges} if new_badges else {}
    }
    
    return result

def process_breathing_session(user_id):
    """
    Process a breathing session, check for related badges.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Information about any new badges earned
    """
    badge_data = get_user_badge_data(user_id)
    new_badges = []
    
    # Update breathing session count
    badge_data["breathing_sessions"] += 1
    
    # Check for breathing session badge
    if badge_data["breathing_sessions"] == 1:
        badge_id = "breathing_session"
        if badge_id not in badge_data["earned_badges"]:
            badge_data["earned_badges"].append(badge_id)
            if badge_id not in badge_data["shown_badges"]:
                new_badges.append(badge_id)
                badge_data["shown_badges"].append(badge_id)
    
    # Save updated badge data
    save_user_badge_data(user_id, badge_data)
    
    # Return information about new badges
    result = {
        "new_badges": new_badges,
        "badge_details": {badge_id: BADGES[badge_id] for badge_id in new_badges} if new_badges else {}
    }
    
    return result

def get_user_badges(user_id):
    """
    Get all badges for a user with full details.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: The user's badges with details
    """
    badge_data = get_user_badge_data(user_id)
    
    # Get details for all earned badges
    earned_badges = []
    for badge_id in badge_data["earned_badges"]:
        if badge_id in BADGES:
            badge = BADGES[badge_id].copy()
            badge["id"] = badge_id
            earned_badges.append(badge)
    
    # Get all available badges (including unearned)
    available_badges = []
    for badge_id, badge in BADGES.items():
        badge_copy = badge.copy()
        badge_copy["id"] = badge_id
        badge_copy["earned"] = badge_id in badge_data["earned_badges"]
        available_badges.append(badge_copy)
    
    # Organize badges by category
    categorized_badges = {
        "streak": [b for b in available_badges if b["id"].startswith("streak_")],
        "entries": [b for b in available_badges if b["id"].startswith("entries_")],
        "insights": [b for b in available_badges if b["id"] == "first_cbt_insight"],
        "mood": [b for b in available_badges if b["id"].startswith("mood_")],
        "breathing": [b for b in available_badges if b["id"] == "breathing_session"]
    }
    
    return {
        "earned_badges": earned_badges,
        "all_badges": available_badges,
        "categorized_badges": categorized_badges,
        "current_streak": badge_data["current_streak"],
        "longest_streak": badge_data["longest_streak"],
        "entry_count": badge_data["entry_count"],
        "stats": badge_data
    }

def flash_badge_notifications(new_badge_info):
    """
    Flash notifications for newly earned badges.
    
    Args:
        new_badge_info: Information about new badges from process functions
    """
    if new_badge_info.get("new_badges"):
        for badge_id in new_badge_info["new_badges"]:
            badge = BADGES.get(badge_id)
            if badge:
                flash(f"🏆 Achievement Unlocked: {badge['name']} - {badge['description']}", "success")

def check_streak_status(user_id):
    """
    Check if the user's streak is at risk of breaking.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Information about the streak status
    """
    badge_data = get_user_badge_data(user_id)
    today = datetime.now().date()
    
    # If no last entry date or it's today, streak is not at risk
    if not badge_data["last_entry_date"]:
        return {"at_risk": False}
    
    try:
        last_entry_date = datetime.strptime(badge_data["last_entry_date"], "%Y-%m-%d").date()
    except:
        return {"at_risk": False}
    
    # If last entry was yesterday, streak is at risk of breaking today
    if last_entry_date == today - timedelta(days=1):
        return {
            "at_risk": True,
            "current_streak": badge_data["current_streak"],
            "days_maintained": badge_data["current_streak"]
        }
    
    # If last entry was today, streak is safe
    if last_entry_date == today:
        return {"at_risk": False}
    
    # If more than a day has passed, streak is already broken
    return {"at_risk": False, "streak_broken": True}

def sync_database_entries(user_id):
    """
    Sync badge data with actual database entries.
    Useful for initialization or fixing inconsistencies.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: Updated badge data
    """
    try:
        # Get all journal entries for this user
        entries = JournalEntry.query.filter_by(user_id=user_id).order_by(JournalEntry.created_at).all()
        
        # Get all mood logs for this user
        from models import MoodLog
        mood_logs = MoodLog.query.filter_by(user_id=user_id).all()
        
        # Get recommendations for CBT insights count
        from models import CBTRecommendation
        insights = CBTRecommendation.query.filter_by(user_id=user_id).all()
        
        # Initialize badge data
        badge_data = get_user_badge_data(user_id)
        
        # Reset counts
        badge_data["entry_count"] = len(entries)
        badge_data["mood_log_count"] = len(mood_logs)
        badge_data["cbt_insights_received"] = len(insights)
        
        # Calculate streak
        if entries:
            # Sort entries by date
            dates = [entry.created_at.date() for entry in entries]
            dates.sort()
            
            # Find the latest entry date
            latest_date = dates[-1]
            badge_data["last_entry_date"] = latest_date.strftime("%Y-%m-%d")
            
            # Calculate current streak
            current_streak = 1
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            if latest_date < yesterday:
                # Streak is broken if latest entry is before yesterday
                current_streak = 0
            else:
                # Count consecutive days backwards from latest entry
                current_date = latest_date
                consecutive_days = set([current_date])
                
                # Look back through previous days
                for i in range(1, 100):  # Arbitrary limit to avoid infinite loop
                    previous_date = current_date - timedelta(days=i)
                    if previous_date in dates:
                        consecutive_days.add(previous_date)
                        if len(consecutive_days) > badge_data["longest_streak"]:
                            badge_data["longest_streak"] = len(consecutive_days)
                    else:
                        break
                
                current_streak = len(consecutive_days)
            
            badge_data["current_streak"] = current_streak
            
            # Check for streak badges
            streak_milestones = [3, 7, 14, 30]
            for milestone in streak_milestones:
                badge_id = f"streak_{milestone}"
                if badge_data["longest_streak"] >= milestone and badge_id not in badge_data["earned_badges"]:
                    badge_data["earned_badges"].append(badge_id)
        
        # Check for entry count badges
        entry_milestones = [5, 20, 50]
        for milestone in entry_milestones:
            badge_id = f"entries_{milestone}"
            if badge_data["entry_count"] >= milestone and badge_id not in badge_data["earned_badges"]:
                badge_data["earned_badges"].append(badge_id)
        
        # Check for other badges
        if badge_data["cbt_insights_received"] > 0:
            badge_id = "first_cbt_insight"
            if badge_id not in badge_data["earned_badges"]:
                badge_data["earned_badges"].append(badge_id)
        
        if badge_data["mood_log_count"] >= 5:
            badge_id = "mood_tracker_5"
            if badge_id not in badge_data["earned_badges"]:
                badge_data["earned_badges"].append(badge_id)
        
        # Save updated badge data
        save_user_badge_data(user_id, badge_data)
        
        return badge_data
    except Exception as e:
        logger.error(f"Error syncing database entries: {str(e)}")
        return get_user_badge_data(user_id)
"""
Routes for the onboarding process for new users.
"""
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from flask_login import current_user
from app import login_required
import random

# Create Blueprint
onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/step-1', methods=['GET', 'POST'])
@login_required
def step_1():
    """
    First step of onboarding: Ask how the user is feeling today
    """
    if request.method == 'POST':
        mood = request.form.get('mood')
        if not mood:
            flash('Please select a mood', 'error')
            return render_template('onboarding_step_1.html')
            
        # Store the mood in session
        session['onboarding_mood'] = mood
        
        # Redirect to step 2
        return redirect(url_for('onboarding.step_2'))
    
    return render_template('onboarding_step_1.html')

@onboarding_bp.route('/step-2', methods=['GET', 'POST'])
@login_required
def step_2():
    """
    Second step of onboarding: Ask for first journal entry
    """
    # List of 5 hardcoded CBT-style feedback messages
    cbt_style_messages = [
        "It's okay to feel overwhelmed. The first step is noticing the thought.",
        "You're not alone in feeling this way. Let's explore what that thought is telling you.",
        "Anxious thoughts can feel very real, but they're not always true.",
        "This moment will pass. Let's focus on what's in your control.",
        "Your thoughts might be distorted—would you like to reframe one together tomorrow?"
    ]
    
    # Make sure user completed step 1
    if 'onboarding_mood' not in session:
        return redirect(url_for('onboarding.step_1'))
    
    if request.method == 'POST':
        journal_content = request.form.get('journal_content')
        if not journal_content or len(journal_content.strip()) < 10:
            flash('Please write at least a few sentences in your journal', 'error')
            return render_template('onboarding_step_2.html')
        
        # Store the journal content in session
        session['onboarding_journal'] = journal_content
        
        # Generate a simple CBT feedback message
        mood = session.get('onboarding_mood')
        cbt_feedback = generate_cbt_feedback(mood)
        session['onboarding_cbt_feedback'] = cbt_feedback
        
        # Randomly select one of the CBT-style messages and store it in session
        last_feedback = random.choice(cbt_style_messages)
        session['last_feedback'] = last_feedback
        
        # Create the first journal entry
        create_first_journal_entry(journal_content, mood, cbt_feedback)
        
        # Redirect to step 3
        return redirect(url_for('onboarding.step_3'))
    
    return render_template('onboarding_step_2.html')

@onboarding_bp.route('/step-3', methods=['GET'])
@login_required
def step_3():
    """
    Third step of onboarding: Show CBT feedback and complete onboarding
    """
    # Make sure user completed step 2
    if 'onboarding_journal' not in session or 'onboarding_cbt_feedback' not in session:
        return redirect(url_for('onboarding.step_1'))
    
    # Get the feedback from session
    cbt_feedback = session.get('onboarding_cbt_feedback')
    
    # Get the last_feedback from session or use fallback
    last_feedback = session.get('last_feedback', "You're off to a great start. Create a journal entry for a new reflection.")
    
    # Mark user as no longer new
    mark_user_as_not_new()
    
    return render_template('onboarding_step_3.html', feedback=cbt_feedback, last_feedback=last_feedback)

def generate_cbt_feedback(mood):
    """
    Generate CBT feedback based on the user's mood.
    
    Args:
        mood: User's mood (very_anxious, anxious, neutral, calm, great)
        
    Returns:
        String containing CBT feedback
    """
    feedback_messages = {
        'very_anxious': "Remember, your thoughts are not facts—you can challenge them. When feeling very anxious, try to identify the specific thoughts causing your anxiety and ask yourself what evidence supports or contradicts them.",
        'anxious': "Anxiety often comes from overestimating threats and underestimating our ability to cope. Consider what might really happen and remind yourself of past challenges you've overcome.",
        'neutral': "Being neutral is actually a great starting point. From here, you can notice your thought patterns without strong emotions clouding your judgment. This awareness is a powerful tool in CBT.",
        'calm': "Your calm state shows that you have the ability to maintain balance. Remember this feeling so you can return to it when things get stressful.",
        'great': "Wonderful! Take note of what's contributing to this positive feeling. Understanding what elevates your mood can help during more challenging times."
    }
    
    default_feedback = "Remember that your thoughts influence your emotions, and both can be examined and shifted. This journal is a great way to track patterns and develop greater self-awareness."
    
    return feedback_messages.get(mood, default_feedback)

def create_first_journal_entry(content, mood, feedback):
    """
    Create the user's first journal entry.
    
    Args:
        content: Journal content
        mood: User's mood
        feedback: CBT feedback
    """
    import os
    import json
    import datetime
    from pathlib import Path
    
    # Make sure data directory exists
    Path("data").mkdir(exist_ok=True)
    Path("data/journals").mkdir(exist_ok=True)
    
    # Get user ID
    user_id = current_user.id
    
    # Create journal entry
    journal_entry = {
        "id": 1,  # First entry
        "user_id": user_id,
        "content": content,
        "mood": mood,
        "feedback": feedback,
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat()
    }
    
    # Get user's journal file
    journal_file = f"data/journals/user_{user_id}_journals.json"
    
    # Load existing journals or create new list
    journals = []
    if os.path.exists(journal_file):
        try:
            with open(journal_file, "r") as f:
                journals = json.load(f)
                # Get the next ID
                if journals:
                    journal_entry["id"] = max(j.get("id", 0) for j in journals) + 1
        except:
            # If error reading file, start with empty list
            journals = []
    
    # Add the new entry
    journals.append(journal_entry)
    
    # Save updated journals
    with open(journal_file, "w") as f:
        json.dump(journals, f, indent=2)
    
    # Also update gamification stats (if available)
    try:
        from gamification import award_xp, XP_REWARDS
        award_xp(user_id, XP_REWARDS['journal_entry_created'], "Created first journal entry during onboarding")
    except (ImportError, KeyError) as e:
        # If gamification module not available or key not found, skip
        print(f"Error awarding gamification XP: {str(e)}")
        pass

def mark_user_as_not_new():
    """
    Mark the current user as not new.
    """
    import os
    import json
    from pathlib import Path
    
    # Get user ID
    user_id = current_user.id
    
    # Make sure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Load users
    users_file = "data/users.json"
    if os.path.exists(users_file):
        try:
            with open(users_file, "r") as f:
                users = json.load(f)
                
            # Find the user and update is_new_user flag
            for user in users:
                if user.get("id") == user_id:
                    user["is_new_user"] = False
                    break
            
            # Save updated users
            with open(users_file, "w") as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            print(f"Error updating user: {str(e)}")
    
    # Clear onboarding data from session except last_feedback
    session.pop('onboarding_mood', None)
    session.pop('onboarding_journal', None)
    session.pop('onboarding_cbt_feedback', None)
    # We keep 'last_feedback' in the session so it can be displayed on step 3
    
    # Award XP for completing the onboarding process
    try:
        from gamification import award_xp, XP_REWARDS
        award_xp(user_id, XP_REWARDS['onboarding_complete'], "Completed onboarding process")
    except (ImportError, KeyError) as e:
        # If gamification module not available or key not found, skip
        print(f"Error awarding gamification XP: {str(e)}")
        pass

def is_new_user(user_id):
    """
    Check if a user is new (has no journal entries).
    
    Args:
        user_id: User ID
        
    Returns:
        bool: True if user is new, False otherwise
    """
    import os
    
    # Check if user has a journals file
    journal_file = f"data/journals/user_{user_id}_journals.json"
    if os.path.exists(journal_file):
        return False
        
    # Check is_new_user flag in users.json
    users_file = "data/users.json"
    if os.path.exists(users_file):
        try:
            import json
            with open(users_file, "r") as f:
                users = json.load(f)
                
            # Find the user
            for user in users:
                if user.get("id") == user_id:
                    return user.get("is_new_user", True)
        except:
            # If error reading file, assume user is new
            pass
    
    # Default to True if we couldn't determine
    return True
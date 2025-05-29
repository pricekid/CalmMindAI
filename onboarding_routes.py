"""
Routes for the onboarding process for new users.
"""
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from flask_login import current_user
from app import login_required, db
from flask_wtf import FlaskForm
from models import User, JournalEntry
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Blueprint
onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/step-1', methods=['GET', 'POST'])
@login_required
def step_1():
    """
    First step of onboarding: Ask how the user is feeling today
    """
    # Create a simple form for CSRF protection
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        mood = request.form.get('mood')
        if not mood:
            flash('Please select a mood', 'error')
            return render_template('onboarding_step_1.html', form=form)
            
        # Store the mood in session
        session['onboarding_mood'] = mood
        
        # Redirect to step 2
        return redirect(url_for('onboarding.step_2'))
    
    return render_template('onboarding_step_1.html', form=form)

@onboarding_bp.route('/step-2', methods=['GET', 'POST'])
@login_required
def step_2():
    """
    Second step of onboarding: Ask for first journal entry
    """
    # Create a simple form for CSRF protection
    form = FlaskForm()
    
    # Make sure user completed step 1
    if 'onboarding_mood' not in session:
        return redirect(url_for('onboarding.step_1'))
    
    if request.method == 'POST' and form.validate_on_submit():
        journal_content = request.form.get('journal_content')
        if not journal_content or len(journal_content.strip()) < 10:
            flash('Please write at least a few sentences in your journal', 'error')
            return render_template('onboarding_step_2.html', form=form)
        
        # Store the journal content in session
        session['onboarding_journal'] = journal_content
        
        # Get the user's mood
        mood = session.get('onboarding_mood')
        
        # Import the OpenAI service functions
        try:
            from openai_service import generate_onboarding_feedback, generate_insightful_message
            
            # Generate personalized CBT feedback using OpenAI
            cbt_feedback = generate_onboarding_feedback(journal_content, mood)
            session['onboarding_cbt_feedback'] = cbt_feedback
            
            # Generate an insightful message using OpenAI
            last_feedback = generate_insightful_message(mood)
            session['last_feedback'] = last_feedback
            
        except ImportError as e:
            # If OpenAI service is unavailable, fall back to the static messages
            print(f"Error importing OpenAI service: {str(e)}")
            
            # Use the static feedback generation function
            cbt_feedback = generate_cbt_feedback(mood)
            session['onboarding_cbt_feedback'] = cbt_feedback
            
            # Fallback to one of the hardcoded CBT-style messages
            cbt_style_messages = [
                "It's okay to feel overwhelmed. The first step is noticing the thought.",
                "You're not alone in feeling this way. Let's explore what that thought is telling you.",
                "Anxious thoughts can feel very real, but they're not always true.",
                "This moment will pass. Let's focus on what's in your control.",
                "Your thoughts might be distorted—would you like to reframe one together tomorrow?"
            ]
            last_feedback = random.choice(cbt_style_messages)
            session['last_feedback'] = last_feedback
        
        # Create the first journal entry
        create_first_journal_entry(journal_content, mood, cbt_feedback)
        
        # Redirect to demographics step
        return redirect(url_for('onboarding.demographics'))
    
    return render_template('onboarding_step_2.html', form=form)

@onboarding_bp.route('/demographics', methods=['GET', 'POST'])
@login_required
def demographics():
    """
    Demographics step: Optional demographic information collection
    """
    # Create a simple form for CSRF protection
    form = FlaskForm()
    
    # Make sure user completed step 2
    if 'onboarding_journal' not in session:
        return redirect(url_for('onboarding.step_1'))
    
    if request.method == 'POST' and form.validate_on_submit():
        # Get form data - all fields are optional
        age_range = request.form.get('age_range', '')
        relationship_status = request.form.get('relationship_status', '')
        has_children = request.form.get('has_children', '')
        life_focus = request.form.getlist('life_focus')  # Multi-select
        life_focus_other = request.form.get('life_focus_other', '')
        
        # Add "Other" text if provided
        if life_focus_other.strip():
            life_focus.append(f"Other: {life_focus_other.strip()}")
        
        # Update user's demographic information
        try:
            from app import db
            from models import User
            
            user = User.query.get(current_user.id)
            if user:
                # Only update fields that were provided
                if age_range:
                    user.age_range = age_range
                if relationship_status:
                    user.relationship_status = relationship_status
                if has_children:
                    user.has_children = (has_children == 'yes')
                if life_focus:
                    # Store as JSON string
                    import json
                    user.life_focus = json.dumps(life_focus)
                
                db.session.commit()
                logging.info(f"Updated demographics for user {current_user.id}")
        except Exception as e:
            logging.error(f"Error updating demographics: {str(e)}")
            db.session.rollback()
        
        # Mark demographics as completed
        session['demographics_completed'] = True
        
        # Redirect to final step
        return redirect(url_for('onboarding.step_3'))
    
    return render_template('onboarding_demographics.html', form=form)

@onboarding_bp.route('/skip-demographics')
@login_required
def skip_demographics():
    """
    Skip demographics step and proceed to final onboarding step
    """
    # Mark demographics as completed (skipped)
    session['demographics_completed'] = True
    return redirect(url_for('onboarding.step_3'))

@onboarding_bp.route('/step-3', methods=['GET'])
@login_required
def step_3():
    """
    Third step of onboarding: Show CBT feedback and complete onboarding
    """
    # Create a simple form for CSRF protection (not needed for GET but for consistency)
    form = FlaskForm()
    
    # Make sure user completed step 2
    if 'onboarding_journal' not in session:
        return redirect(url_for('onboarding.step_1'))
    
    # Check if user should go through demographics step first
    # Only skip demographics if they explicitly came from demographics or skipped it
    if 'demographics_completed' not in session:
        return redirect(url_for('onboarding.demographics'))
    
    # Get the feedback from session or use fallback
    cbt_feedback = session.get('onboarding_cbt_feedback', "Thank you for sharing your thoughts. Regular journaling can help you gain insights into your emotions and thought patterns. I'll be here to support your mental wellness journey.")
    
    # Get the last_feedback from session or use fallback
    last_feedback = session.get('last_feedback', "You're off to a great start. Create a journal entry for a new reflection.")
    
    # Log the feedback values for debugging
    print(f"CBT Feedback: {cbt_feedback}")
    print(f"Last Feedback: {last_feedback}")
    
    # Mark user as no longer new
    mark_user_as_not_new()
    
    try:
        return render_template('onboarding_step_3.html', feedback=cbt_feedback, last_feedback=last_feedback, form=form)
    except Exception as e:
        # Log the error and provide fallback
        print(f"Error rendering onboarding_step_3.html: {str(e)}")
        
        # If there's an error, provide default feedback values and try again
        default_feedback = "Thank you for sharing your thoughts. Regular journaling can help you gain insights into your emotions and thought patterns. I'll be here to support your mental wellness journey."
        default_last_feedback = "You're off to a great start. Create a journal entry for a new reflection."
        
        return render_template('onboarding_step_3.html', feedback=default_feedback, last_feedback=default_last_feedback, form=form)

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
    Create the user's first journal entry in the database.
    
    Args:
        content: Journal content
        mood: User's mood
        feedback: CBT feedback
    """
    import datetime
    import logging
    from app import db
    from models import JournalEntry
    
    # Get user ID
    user_id = current_user.id
    
    # Ensure feedback is not None
    if feedback is None:
        feedback = "Remember that your thoughts influence your emotions, and both can be examined and shifted. This journal is a great way to track patterns and develop greater self-awareness."
    
    try:
        # Create new journal entry in the database
        journal_entry = JournalEntry(
            title="My First Journal Entry",
            content=content,
            user_id=user_id,
            anxiety_level=mood_to_anxiety_level(mood),
            initial_insight=feedback,
            is_analyzed=True
        )
        
        # Add to database and commit
        db.session.add(journal_entry)
        db.session.commit()
        
        logging.info(f"Created first journal entry for user {user_id}")
        
        # Also update gamification stats (if available)
        try:
            from gamification import award_xp, XP_REWARDS
            award_xp(user_id, XP_REWARDS['journal_entry_created'], "Created first journal entry during onboarding")
        except (ImportError, KeyError) as e:
            # If gamification module not available or key not found, skip
            logging.error(f"Error awarding gamification XP: {str(e)}")
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating first journal entry: {str(e)}")
        
def mood_to_anxiety_level(mood):
    """
    Convert mood string to anxiety level (1-10).
    
    Args:
        mood: Mood string from onboarding (very_anxious, anxious, neutral, calm, great)
        
    Returns:
        int: Anxiety level (1-10, where 1 is calm and 10 is very anxious)
    """
    mood_map = {
        'very_anxious': 9,
        'anxious': 7, 
        'neutral': 5,
        'calm': 3,
        'great': 1
    }
    
    return mood_map.get(mood, 5)  # Default to 5 (neutral) if mood not found

def mark_user_as_not_new():
    """
    Mark the current user as not new by setting welcome_message_shown to True.
    """
    import logging
    from app import db
    from models import User
    
    # Get user ID
    user_id = current_user.id
    
    try:
        # Find the user in the database and update welcome_message_shown flag
        user = User.query.get(user_id)
        if user:
            user.welcome_message_shown = True
            db.session.commit()
            logging.info(f"Marked user {user_id} as not new (welcome_message_shown = True)")
        else:
            logging.error(f"User {user_id} not found in database")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating user welcome_message_shown flag: {str(e)}")
    
    # Clear onboarding data from session except last_feedback
    session.pop('onboarding_mood', None)
    session.pop('onboarding_journal', None)
    session.pop('onboarding_cbt_feedback', None)
    session.pop('demographics_completed', None)  # Clear demographics flag too
    # We keep 'last_feedback' in the session so it can be displayed on step 3
    
    # Award XP for completing the onboarding process
    try:
        from gamification import award_xp, XP_REWARDS
        award_xp(user_id, XP_REWARDS['onboarding_complete'], "Completed onboarding process")
    except (ImportError, KeyError) as e:
        # If gamification module not available or key not found, skip
        logging.error(f"Error awarding gamification XP: {str(e)}")

def is_new_user(user_id):
    """
    Check if a user is new (has no journal entries).
    
    Args:
        user_id: User ID
        
    Returns:
        bool: True if user is new, False otherwise
    """
    try:
        from models import JournalEntry, User
        from app import db
        import logging
        
        # Check if user has any journal entries in the database
        journal_count = JournalEntry.query.filter_by(user_id=user_id).count()
        if journal_count > 0:
            logging.info(f"User {user_id} has {journal_count} journal entries")
            return False
            
        # Check if welcome_message_shown flag is set on user
        user = User.query.get(user_id)
        if user and user.welcome_message_shown:
            logging.info(f"User {user_id} has seen the welcome message")
            return False
            
        logging.info(f"User {user_id} is new (no journal entries and hasn't seen welcome message)")
        return True
        
    except Exception as e:
        logging.error(f"Error checking if user is new: {str(e)}")
        # Default to True if we couldn't determine
        return True
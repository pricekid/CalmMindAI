"""
This is a fixed version of the new_journal_entry function that properly
analyzes journal entries upon creation. After testing, copy this function
into journal_routes.py to replace the existing new_journal_entry function.
"""
import logging
from flask import flash, redirect, render_template
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy.orm import load_only
from app import db
from models import JournalEntry, CBTRecommendation
from forms import JournalEntryForm
from journal_service import analyze_journal_with_gpt, save_journal_entry
from recommendation_handler import safe_process_pattern
import gamification
from utils.activity_tracker import track_journal_entry

logger = logging.getLogger(__name__)

def new_journal_entry():
    form = JournalEntryForm()
    if form.validate_on_submit():
        # Check for recently created similar entries to prevent duplicates - use load_only for specific columns
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_entries = JournalEntry.query\
            .options(load_only(
                JournalEntry.id,
                JournalEntry.title,
                JournalEntry.created_at,
                JournalEntry.user_id
            ))\
            .filter(
                JournalEntry.user_id == current_user.id,
                JournalEntry.title == form.title.data,
                JournalEntry.created_at >= five_minutes_ago
            ).all()

        # If a similar entry was recently created, redirect to that entry
        if recent_entries:
            logger.info(f"Prevented duplicate entry: {form.title.data}")
            flash('A similar journal entry was just created. Redirecting to the existing entry.', 'info')
            # Use direct path instead of url_for
            return redirect(f'/journal/{recent_entries[0].id}')

        # First, save the journal entry so it's not lost if analysis fails
        logger.debug("Saving journal entry to database")
        try:
            entry = JournalEntry(
                title=form.title.data,
                content=form.content.data,
                anxiety_level=form.anxiety_level.data,
                author=current_user
            )

            db.session.add(entry)
            db.session.commit()
            logger.debug(f"Successfully saved journal entry with ID: {entry.id}")
        except Exception as db_error:
            logger.error(f"Database error when saving journal entry: {str(db_error)}")
            db.session.rollback()
            flash('Error saving your journal entry. Please try again.', 'danger')
            # Create a dummy entry object with default values
            mock_entry = {
                'title': form.title.data,
                'content': form.content.data,
                'anxiety_level': form.anxiety_level.data,
                'created_at': datetime.utcnow()
            }
            return render_template('journal_entry.html', title='New Journal Entry', 
                                  form=form, legend='New Journal Entry',
                                  entry=mock_entry,
                                  structured_data={'insight_text': '', 'reflection_prompt': ''},
                                  view_only=False)

        # Analyze the entry using the improved GPT analysis
        try:
            logger.debug(f"Starting GPT analysis for journal entry {entry.id}")
            analysis_result = analyze_journal_with_gpt(
                journal_text=form.content.data, 
                anxiety_level=form.anxiety_level.data,
                user_id=current_user.id
            )

            # Safety check to make sure analysis_result is a dictionary
            if not isinstance(analysis_result, dict):
                logger.error(f"Invalid analysis result type: {type(analysis_result)}")
                analysis_result = {
                    "gpt_response": "Thank you for sharing your journal entry. I've read through your thoughts.\n\nWarmly,\nCoach Mira",
                    "cbt_patterns": [{
                        "pattern": "Processing Issue",
                        "description": "We encountered a technical issue analyzing your entry.",
                        "recommendation": "Your journal has been saved successfully. The insights will be available soon."
                    }],
                    "structured_data": None
                }

            logger.debug(f"Got analysis result type: {type(analysis_result)}")
            logger.debug(f"Analysis result keys: {list(analysis_result.keys()) if isinstance(analysis_result, dict) else 'Not a dictionary'}")

            gpt_response = analysis_result.get("gpt_response")
            cbt_patterns = analysis_result.get("cbt_patterns", [])
            structured_data = analysis_result.get("structured_data", None)

            # Safety check for gpt_response
            if not gpt_response:
                logger.warning("Missing GPT response in analysis result, providing fallback")
                gpt_response = "Thank you for sharing your journal entry. I've read through your thoughts.\n\nWarmly,\nCoach Mira"

            logger.debug(f"GPT response type: {type(gpt_response)}")
            logger.debug(f"GPT response length: {len(gpt_response) if gpt_response else 0}")
            logger.debug(f"GPT response preview: {gpt_response[:100] if gpt_response else 'None'}...")

            # Log structured data status if available
            if structured_data:
                logger.debug(f"Structured data available with keys: {list(structured_data.keys())}")
            else:
                logger.debug("No structured data available in response")

            # Save the patterns to the database
            is_api_error = False
            is_config_error = False

            for pattern in cbt_patterns:
                try:
                    # Process pattern safely with our handler
                    pattern_name, recommendation_text = safe_process_pattern(pattern)
                    
                    # Check for different error patterns
                    if pattern_name == "API Quota Exceeded":
                        is_api_error = True
                    elif pattern_name == "API Configuration Issue":
                        is_config_error = True

                    # Save recommendation to database
                    recommendation = CBTRecommendation(
                        thought_pattern=pattern_name,
                        recommendation=recommendation_text,
                        journal_entry_id=entry.id
                    )
                    db.session.add(recommendation)
                except Exception as pattern_err:
                    logger.error(f"Error processing pattern in new entry: {str(pattern_err)}")
                    # Continue with the next pattern instead of failing completely

            entry.is_analyzed = True

            # Set the conversational fields using structured data if available
            if structured_data and isinstance(structured_data, dict):
                logger.debug("Setting conversational fields from structured data")
                if 'insight_text' in structured_data:
                    entry.initial_insight = structured_data.get('insight_text')
                    logger.debug(f"Set initial_insight: {entry.initial_insight[:50]}...")
                if 'reflection_prompt' in structured_data:
                    # Include the reflection prompt at the end of the initial insight
                    if entry.initial_insight:
                        entry.initial_insight += f"\n\n{structured_data.get('reflection_prompt')}"
                    else:
                        entry.initial_insight = structured_data.get('reflection_prompt')
                    logger.debug(f"Added reflection prompt to initial_insight")
            else:
                # Fallback - set the initial_insight to the gpt_response with formatting
                logger.debug("No structured data available, using gpt_response for initial_insight with improved formatting")

                # Format the insight for better readability
                if gpt_response:
                    insight_parts = gpt_response.split('\n\n', 1)
                    if len(insight_parts) > 1:
                        # Use the first paragraph as the insight and the rest for reflection
                        entry.initial_insight = insight_parts[0] + "\n\n" + insight_parts[1]
                    else:
                        # If there's no clear separation, just use the whole response
                        entry.initial_insight = gpt_response

            # Append a reflection prompt if not already present
            if entry.initial_insight and "?" not in entry.initial_insight:
                entry.initial_insight += "\n\nWhat thoughts come to mind as you reflect on this insight?"

            # Commit the changes to the database
            db.session.commit()
            logger.debug(f"Analysis results saved to database for entry {entry.id}")

            # Save the journal entry to the JSON file
            save_journal_entry(
                entry_id=entry.id,
                user_id=current_user.id,
                title=entry.title,
                content=entry.content,
                anxiety_level=entry.anxiety_level,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
                is_analyzed=entry.is_analyzed,
                gpt_response=gpt_response,
                cbt_patterns=cbt_patterns,
                structured_data=structured_data
            )

            # Show appropriate message based on error type
            if is_api_error:
                flash('Your journal entry has been saved! AI analysis is currently unavailable due to API usage limits.', 'info')
            elif is_config_error:
                flash('Your journal entry has been saved! AI analysis is currently unavailable due to a configuration issue.', 'info')
            else:
                flash('Your journal entry has been created with AI analysis!', 'success')

            # Track the journal entry for community stats (privacy-friendly)
            try:
                track_journal_entry(user_id=current_user.id, activity_type="journal_created", entry_id=entry.id)
                logger.debug("Tracked journal entry for community statistics")
            except Exception as track_error:
                logger.error(f"Error tracking journal entry: {str(track_error)}")

            # Process gamification elements
            badge_result = gamification.process_journal_entry(current_user.id)

            # Award XP for creating a journal entry
            xp_data = gamification.award_xp(
                user_id=current_user.id,
                xp_amount=gamification.XP_REWARDS['journal_entry'],
                reason="Created a new journal entry"
            )

            # Award additional XP if entry was analyzed
            if entry.is_analyzed:
                gamification.award_xp(
                    user_id=current_user.id,
                    xp_amount=gamification.XP_REWARDS['analysis'],
                    reason="Received insights on journal entry"
                )

            # Flash notifications for earned badges
            gamification.flash_badge_notifications(badge_result)

            # Flash XP notifications
            if xp_data and xp_data.get('xp_gained'):
                flash(f"🌟 You earned {xp_data['xp_gained']} XP for journaling!", 'success')

                # Show level up message if user leveled up
                if xp_data.get('leveled_up'):
                    level = xp_data['level']
                    level_name = xp_data['level_name']
                    flash(f"🎉 Level Up! You're now Level {level}: {level_name}", 'success')

            # If user earned new badges, prepare to render the badge notification
            if badge_result.get("new_badges"):
                first_badge_id = badge_result["new_badges"][0]
                badge = badge_result["badge_details"][first_badge_id]

                # Generate a wellness fact based on the badge type
                wellness_facts = {
                    'streak_3': "Consistent journaling creates new neural pathways in your brain that improve emotional regulation.",
                    'streak_7': "After a week of consistent journaling, your brain starts forming new habits that can reduce stress hormones.",
                    'streak_14': "Two weeks of consistent reflection has been shown to reduce rumination and increase mindfulness.",
                    'streak_30': "Studies show that a month of daily journaling can lead to measurable improvements in emotional processing."
                }

                wellness_fact = wellness_facts.get(badge.badge_type, 
                                                "Regular journaling helps your brain process emotions and reduce stress.")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error analyzing journal entry: {error_msg}")

            # Update the entry to indicate analysis failed
            try:
                entry.is_analyzed = False
                db.session.commit()

                # Still save to JSON but with error info
                save_journal_entry(
                    entry_id=entry.id,
                    user_id=current_user.id,
                    title=entry.title,
                    content=entry.content,
                    anxiety_level=entry.anxiety_level,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                    is_analyzed=False,
                    gpt_response="Error occurred during analysis.",
                    cbt_patterns=[{
                        "pattern": "Error analyzing entry",
                        "description": "We couldn't analyze your journal entry at this time.",
                        "recommendation": "Please try again later or contact support if the problem persists."
                    }],
                    structured_data=None
                )

                # Show specific error messages based on error type
                if "API_QUOTA_EXCEEDED" in error_msg:
                    flash('Your journal entry has been saved! AI analysis is currently unavailable due to API usage limits.', 'info')
                elif "INVALID_API_KEY" in error_msg:
                    flash('Your journal entry has been saved! AI analysis is currently unavailable due to a configuration issue.', 'info')
                else:
                    flash('Your journal entry has been saved, but analysis could not be completed. You can try analyzing it later.', 'warning')
            except Exception as inner_e:
                # Catch any errors in error handling to ensure we still redirect
                logger.error(f"Error during error handling: {str(inner_e)}")
                flash('Your journal entry has been saved. There was an issue with the analysis process.', 'warning')

        # Wrap the redirect in a try/except to guarantee we don't have a blank page
        try:
            # Use direct path instead of url_for and ensure proper redirection
            response = redirect(f'/journal/{entry.id}')
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
        except Exception as redirect_error:
            logger.error(f"Critical error during redirect: {str(redirect_error)}")
            # Use a hardcoded URL as absolute fallback to avoid blank page
            flash('Your journal entry has been saved. Redirecting to journal list.', 'info')
            # Use direct path instead of url_for
            return redirect('/journal')

    # Create a dummy entry object with default values
    mock_entry = {
        'title': '',
        'content': '',
        'anxiety_level': 5,
        'created_at': datetime.utcnow()
    }
    
    return render_template('journal_entry.html', title='New Journal Entry', 
                          form=form, legend='New Journal Entry',
                          entry=mock_entry,
                          structured_data={'insight_text': '', 'reflection_prompt': ''},
                          view_only=False)
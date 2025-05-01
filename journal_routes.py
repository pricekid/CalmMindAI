from flask import render_template, url_for, flash, redirect, request, jsonify, abort, Blueprint
from flask_login import current_user
from app import login_required, db
from models import JournalEntry, CBTRecommendation
from forms import JournalEntryForm
from journal_service import (
    analyze_journal_with_gpt, save_journal_entry, 
    get_journal_entries_for_user, count_user_entries,
    get_recurring_patterns
)
from datetime import datetime, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import load_only, defer, undefer
import logging
import gamification
from utils.activity_tracker import track_journal_entry
import markdown
import re
from csrf_utils import get_csrf_token, validate_csrf_token

# Set up logging with more details
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create blueprint
journal_bp = Blueprint('journal_blueprint', __name__, url_prefix='/journal')

def convert_markdown_to_html(text):
    """
    Convert markdown formatting to HTML for better display.
    Also handles legacy formatting for older entries.

    Args:
        text: Text containing markdown formatting

    Returns:
        Text with markdown converted to HTML
    """
    if not text:
        return ""

    # First, standardize newlines to avoid inconsistencies
    text = text.replace('\r\n', '\n')

    # Detect if the text has markdown formatting
    has_markdown = "##" in text or "**" in text or "•" in text or "- " in text or "#" in text or "*" in text

    # 1. Pre-process: Clean up any markdown symbols that might cause issues
    # Remove any standalone # at the beginning of lines that aren't proper headings
    text = re.sub(r'^#(?!\s)', '', text, flags=re.MULTILINE)

    # Process sections in order to avoid formatting conflicts

    # 2. Convert markdown headers (##) to styled headers
    text = re.sub(r'##\s+(.*?)$', r'<h4 class="mt-4 mb-3">\1</h4>', text, flags=re.MULTILINE)
    # Also convert single # headers
    text = re.sub(r'^#\s+(.*?)$', r'<h4 class="mt-4 mb-3">\1</h4>', text, flags=re.MULTILINE)

    # 3. Convert bold text (**text**) to <strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # 4. Convert italic text (*text*) to <em>
    text = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'<em>\1</em>', text)

    # 5. Convert bullet points (both • and - bullets)
    text = re.sub(r'^\s*[•\-]\s+(.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)

    # 6. Wrap lists in <ul> tags, making sure all <li> elements are wrapped
    text = re.sub(r'((<li>.*?</li>\n?)+)', r'<ul class="mb-3">\n\g<0></ul>', text, flags=re.DOTALL)

    # If the text doesn't have markdown but has common section headers, format them
    if not has_markdown:
        # Format legacy section headers for entries that don't use markdown
        text = text.replace("Here are a few thought patterns", "<h4 class='mt-4 mb-3'>Thought Patterns</h4>")
        text = text.replace("Here are a few gentle CBT strategies", "<h4 class='mt-4 mb-3'>CBT Strategies</h4>")
        text = text.replace("And a little reflection for today:", "<h4 class='mt-4 mb-3'>Reflection Prompt</h4>")
    else:
        # For text that has markdown formatting, check for patterns that indicate section headers that should be formatted
        text = re.sub(r'Thought Patterns[:]*\s*$', r'<h4 class="mt-4 mb-3">Thought Patterns</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'CBT Strategies[:]*\s*$', r'<h4 class="mt-4 mb-3">CBT Strategies</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'Suggested Strategies[:]*\s*$', r'<h4 class="mt-4 mb-3">Suggested Strategies</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'Reflection Prompt[:]*\s*$', r'<h4 class="mt-4 mb-3">Reflection Prompt</h4>', text, flags=re.MULTILINE)

    # 7. Handle paragraph breaks but avoid extra breaks after headers and before lists
    # Replace double newlines with paragraph breaks, but not if preceded by header or followed by list
    text = re.sub(r'(?<!</h4>)\n\n(?!<ul)', '<br><br>', text)

    # 8. Remove any remaining excessive newlines around HTML elements
    text = re.sub(r'\n+(<h4|<ul|<li|</ul>)', r'\1', text)
    text = re.sub(r'(</h4>|</ul>|</li>)\n+', r'\1', text)

    # 9. Thorough clean up of any remaining raw markdown symbols that weren't properly converted

    # Remove all remaining # characters
    text = re.sub(r'#', '', text)

    # Remove all remaining * characters
    text = re.sub(r'\*', '', text)

    # Remove any raw dashes at the beginning of lines that might be malformed bullet points
    text = re.sub(r'^\s*-\s', '', text, flags=re.MULTILINE)

    # Clean up any double spaces that might have been created during cleaning
    text = re.sub(r'\s{2,}', ' ', text)

    return text

# API endpoint to check if a followup insight is ready
@journal_bp.route('/check-followup/<int:entry_id>', methods=['GET'])
@login_required
def check_followup_insight(entry_id):
    """Check if a followup insight is ready for a journal entry"""
    try:
        # Fetch the journal entry
        entry = JournalEntry.query.get(entry_id)

        # Check if the entry exists and belongs to the current user
        if not entry:
            logger.error(f"Journal entry not found: ID {entry_id}")
            return jsonify({"error": "Journal entry not found", "ready": False}), 404

        if entry.user_id != current_user.id:
            logger.warning(f"Unauthorized access to entry {entry_id} by user {current_user.id}")
            return jsonify({"error": "Unauthorized access", "ready": False}), 403

        # Check if the followup insight exists and is not empty
        followup_ready = entry.followup_insight and len(entry.followup_insight.strip()) > 0

        return jsonify({
            "ready": followup_ready,
            "entry_id": entry_id
        })

    except Exception as e:
        logger.error(f"Error checking followup insight: {str(e)}")
        return jsonify({"error": "Server error", "ready": False}), 500

# API endpoint to save user reflections
@journal_bp.route('/save-initial-reflection', methods=['POST'])
@login_required
def save_initial_reflection():
    """Save user's first reflection response with enhanced error handling"""
    try:
        # Debug logging
        logger.debug("Starting save_initial_reflection handler")

        # Get JSON request data with error handling
        try:
            data = request.get_json()
            if data is None:
                logger.error("No JSON data in request")
                return jsonify({"error": "Invalid request format - no JSON data"}), 400
        except Exception as json_err:
            logger.error(f"Error parsing JSON request: {str(json_err)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        # Validate required fields with detailed error messages
        entry_id = data.get('entry_id')
        reflection_text = data.get('reflection_text')

        if entry_id is None:
            logger.error("Missing entry_id in request")
            return jsonify({"error": "Missing entry_id field"}), 400

        if reflection_text is None:
            logger.error("Missing reflection_text in request")
            return jsonify({"error": "Missing reflection_text field"}), 400

        # Validate and convert entry_id
        try:
            entry_id = int(entry_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid entry_id format: {entry_id}")
            return jsonify({"error": "Invalid entry ID format"}), 400

        # Check for empty reflection
        if not reflection_text.strip():
            logger.warning("Empty reflection text submitted")
            return jsonify({"error": "Reflection text cannot be empty"}), 400

        # Fetch journal entry with error handling
        try:
            entry = JournalEntry.query.get(entry_id)
            if entry is None:
                logger.error(f"Journal entry not found: ID {entry_id}")
                return jsonify({"error": "Journal entry not found"}), 404
        except Exception as db_err:
            logger.error(f"Database error fetching entry {entry_id}: {str(db_err)}")
            return jsonify({"error": "Database error"}), 500

        # Check authorization
        if entry.user_id != current_user.id:
            logger.warning(f"Unauthorized access to entry {entry_id} by user {current_user.id}")
            return jsonify({"error": "Unauthorized access"}), 403

        # Save the reflection
        try:
            entry.user_reflection = reflection_text
            entry.updated_at = datetime.utcnow()

            # Log successful update
            logger.debug(f"Successfully updated entry {entry_id} with user reflection")
        except Exception as update_err:
            logger.error(f"Error updating entry with reflection: {str(update_err)}")
            return jsonify({"error": "Error saving reflection"}), 500

        # Generate Mira's followup insight
        try:
            logger.debug(f"Generating followup insight for entry {entry_id}")
            analysis_result = analyze_journal_with_gpt(
                journal_text=f"{entry.content}\n\nUser Reflection: {reflection_text}",
                anxiety_level=entry.anxiety_level,
                user_id=current_user.id
            )

            # Check if we got a valid response
            if not analysis_result or "gpt_response" not in analysis_result:
                logger.error("Invalid or empty analysis result from GPT")
                entry.followup_insight = "I appreciate your reflection. I'm having trouble generating a response right now, but your thoughts are valuable and have been saved."
            else:
                entry.followup_insight = analysis_result.get("gpt_response")

            # Commit changes
            db.session.commit()
            logger.debug(f"Successfully committed changes for entry {entry_id}")

        except Exception as gpt_err:
            # Handle GPT analysis errors gracefully
            logger.error(f"Error generating followup insight: {str(gpt_err)}")
            # Save the reflection even if GPT analysis fails
            entry.followup_insight = "Thank you for sharing your reflection. I'm processing your thoughts, but having some trouble generating a response right now. Your reflection has been saved."
            db.session.commit()

        # Return success response
        return jsonify({
            "success": True,
            "followup_insight": entry.followup_insight
        })

    except Exception as e:
        # Catch-all error handler for unhandled exceptions
        logger.error(f"Unhandled error in save_initial_reflection: {str(e)}")
        return jsonify({"error": "Server error occurred while saving your reflection"}), 500

# API endpoint to check if a closing message is ready
@journal_bp.route('/check-closing/<int:entry_id>', methods=['GET'])
@login_required
def check_closing_message(entry_id):
    """Check if a closing message is ready for a journal entry"""
    try:
        # Fetch the journal entry
        entry = JournalEntry.query.get(entry_id)

        # Check if the entry exists and belongs to the current user
        if not entry:
            logger.error(f"Journal entry not found: ID {entry_id}")
            return jsonify({"error": "Journal entry not found", "ready": False}), 404

        if entry.user_id != current_user.id:
            logger.warning(f"Unauthorized access to entry {entry_id} by user {current_user.id}")
            return jsonify({"error": "Unauthorized access", "ready": False}), 403

        # Check if the closing message exists and is not empty
        closing_ready = entry.closing_message and len(entry.closing_message.strip()) > 0

        return jsonify({
            "ready": closing_ready,
            "entry_id": entry_id
        })

    except Exception as e:
        logger.error(f"Error checking closing message: {str(e)}")
        return jsonify({"error": "Server error", "ready": False}), 500

@journal_bp.route('/save-second-reflection', methods=['POST'])
@login_required
def save_second_reflection():
    """Save user's second reflection response with enhanced error handling"""
    try:
        # Debug logging
        logger.debug("Starting save_second_reflection handler")

        # Get JSON request data with error handling
        try:
            data = request.get_json()
            if data is None:
                logger.error("No JSON data in request")
                return jsonify({"error": "Invalid request format - no JSON data"}), 400
        except Exception as json_err:
            logger.error(f"Error parsing JSON request: {str(json_err)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        # Validate required fields with detailed error messages
        entry_id = data.get('entry_id')
        reflection_text = data.get('reflection_text')

        if entry_id is None:
            logger.error("Missing entry_id in request")
            return jsonify({"error": "Missing entry_id field"}), 400

        if reflection_text is None:
            logger.error("Missing reflection_text in request")
            return jsonify({"error": "Missing reflection_text field"}), 400

        # Validate and convert entry_id
        try:
            entry_id = int(entry_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid entry_id format: {entry_id}")
            return jsonify({"error": "Invalid entry ID format"}), 400

        # Check for empty reflection
        if not reflection_text.strip():
            logger.warning("Empty reflection text submitted")
            return jsonify({"error": "Reflection text cannot be empty"}), 400

        # Fetch journal entry with error handling
        try:
            entry = JournalEntry.query.get(entry_id)
            if entry is None:
                logger.error(f"Journal entry not found: ID {entry_id}")
                return jsonify({"error": "Journal entry not found"}), 404
        except Exception as db_err:
            logger.error(f"Database error fetching entry {entry_id}: {str(db_err)}")
            return jsonify({"error": "Database error"}), 500

        # Check authorization
        if entry.user_id != current_user.id:
            logger.warning(f"Unauthorized access to entry {entry_id} by user {current_user.id}")
            return jsonify({"error": "Unauthorized access"}), 403

        # Save the reflection
        try:
            entry.second_reflection = reflection_text
            entry.updated_at = datetime.utcnow()
            entry.conversation_complete = True

            # Log successful update
            logger.debug(f"Successfully updated entry {entry_id} with second reflection")
        except Exception as update_err:
            logger.error(f"Error updating entry with second reflection: {str(update_err)}")
            return jsonify({"error": "Error saving reflection"}), 500

        # Generate Mira's closing message
        try:
            logger.debug(f"Generating closing message for entry {entry_id}")
            analysis_result = analyze_journal_with_gpt(
                journal_text=f"{entry.content}\n\nFirst Reflection: {entry.user_reflection}\nSecond Reflection: {reflection_text}",
                anxiety_level=entry.anxiety_level,
                user_id=current_user.id
            )

            # Check if we got a valid response
            if not analysis_result or "gpt_response" not in analysis_result:
                logger.error("Invalid or empty analysis result from GPT")
                entry.closing_message = "Thank you for sharing your reflections. I appreciate your thoughtful responses. Your insights show a willingness to explore your feelings, which is an important part of emotional growth.\n\nWarmly,\nCoach Mira"
            else:
                entry.closing_message = analysis_result.get("gpt_response")

            # Commit changes
            db.session.commit()
            logger.debug(f"Successfully committed changes for entry {entry_id}")

        except Exception as gpt_err:
            # Handle GPT analysis errors gracefully
            logger.error(f"Error generating closing message: {str(gpt_err)}")
            # Save the reflection even if GPT analysis fails
            entry.closing_message = "Thank you for sharing your reflections throughout this conversation. Even though I'm having some technical difficulties generating a personalized response, your willingness to reflect and explore your thoughts shows great self-awareness. Your reflections have been saved.\n\nWarmly,\nCoach Mira"
            db.session.commit()

        # Return success response
        return jsonify({
            "success": True,
            "closing_message": entry.closing_message
        })

    except Exception as e:
        # Catch-all error handler for unhandled exceptions
        logger.error(f"Unhandled error in save_second_reflection: {str(e)}")
        return jsonify({"error": "Server error occurred while saving your reflection"}), 500

@journal_bp.route('/save-reflection', methods=['POST'])
@login_required
def save_reflection():
    """
    Save a user's reflection to their journal entry.

    Expects JSON with:
    {
        "entry_id": int,
        "reflection_text": str
    }
    """
    try:
        # Get data from request - use try/except for more robust error handling
        try:
            data = request.get_json()
            logger.debug(f"Received reflection data: {data}")
        except Exception as json_error:
            logger.error(f"JSON parsing error: {str(json_error)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Use safer type conversions with explicit error handling
        try:
            entry_id = int(data.get('entry_id'))
        except (TypeError, ValueError):
            logger.error(f"Invalid entry_id format: {data.get('entry_id')}")
            return jsonify({"error": "Invalid entry ID format"}), 400

        reflection_text = data.get('reflection_text')

        if not entry_id or not reflection_text:
            return jsonify({"error": "Missing required fields"}), 400

        # Use undefer() to explicitly load the deferred user_reflection column
        entry = JournalEntry.query.options(undefer(JournalEntry.user_reflection)).get(entry_id)

        if not entry:
            logger.error(f"Entry not found: {entry_id}")
            return jsonify({"error": "Entry not found"}), 404

        # Ensure the entry belongs to the current user
        if entry.user_id != current_user.id:
            logger.warning(f"Unauthorized access attempt for entry {entry_id} by user {current_user.id}")
            return jsonify({"error": "Unauthorized access"}), 403

        # Save the reflection to the database
        entry.user_reflection = reflection_text
        entry.updated_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"Saved reflection for entry {entry_id}")

        # Also save to the JSON file if using that for structured data
        try:
            from journal_service import get_journal_entries_for_user, save_journal_entry
            entries = get_journal_entries_for_user(current_user.id)

            for json_entry in entries:
                if json_entry.get('id') == entry_id:
                    # Update the existing entry with the reflection
                    save_journal_entry(
                        entry_id=entry.id,
                        user_id=current_user.id,
                        title=entry.title,
                        content=entry.content, 
                        anxiety_level=entry.anxiety_level,
                        created_at=entry.created_at,
                        updated_at=entry.updated_at,
                        is_analyzed=entry.is_analyzed,
                        gpt_response=json_entry.get('gpt_response'),
                        cbt_patterns=json_entry.get('cbt_patterns'),
                        structured_data=json_entry.get('structured_data'),
                        user_reflection=reflection_text
                    )
                    logger.debug(f"Updated JSON data for entry {entry_id}")
                    break
        except Exception as json_error:
            # Log but don't fail if JSON update fails
            logger.error(f"Error updating JSON data: {str(json_error)}")

        # Track the reflection activity
        try:
            track_journal_entry(user_id=current_user.id, activity_type="reflection_added", entry_id=entry_id)
            logger.debug(f"Tracked reflection activity for entry {entry_id}")
        except Exception as tracking_error:
            # Log but don't fail if tracking fails
            logger.error(f"Error tracking reflection activity: {str(tracking_error)}")

        return jsonify({
            "success": True,
            "message": "Reflection saved successfully"
        })

    except Exception as e:
        logger.error(f"Error saving reflection: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Journal entry list
@journal_bp.route('/')
@login_required
def journal_list():
    page = request.args.get('page', 1, type=int)
    
    # Log the current user for debugging
    logger.info(f"User {current_user.id} accessing journal list page {page}")

    # Use load_only to specify only the columns we need, avoiding the deferred user_reflection column
    entries_query = JournalEntry.query\
        .options(load_only(
            JournalEntry.id,
            JournalEntry.title,
            JournalEntry.content,
            JournalEntry.created_at,
            JournalEntry.updated_at,
            JournalEntry.is_analyzed,
            JournalEntry.anxiety_level,
            JournalEntry.user_id
        ))\
        .filter(JournalEntry.user_id == current_user.id)\
        .order_by(desc(JournalEntry.created_at))
    
    # Log the query for debugging
    logger.debug(f"Journal entries query: {str(entries_query)}")
    
    # Count total entries for this user
    total_entries = entries_query.count()
    logger.info(f"Found {total_entries} total entries for user {current_user.id}")

    entries = entries_query.paginate(page=page, per_page=10)

    # Get all entries for visualization (limiting to last 30 for performance)
    # Use load_only to specify only the columns we need, avoiding the deferred user_reflection column
    all_entries = JournalEntry.query\
        .options(load_only(
            JournalEntry.id,
            JournalEntry.title,
            JournalEntry.content,
            JournalEntry.created_at,
            JournalEntry.updated_at,
            JournalEntry.is_analyzed,
            JournalEntry.anxiety_level,
            JournalEntry.user_id
        ))\
        .filter(JournalEntry.user_id == current_user.id)\
        .order_by(desc(JournalEntry.created_at))\
        .limit(30).all()
    
    logger.info(f"Retrieved {len(all_entries)} entries for visualization")

    # Format the entry data for visualization
    journal_data = [{
        'id': entry.id,
        'title': entry.title,
        'anxiety_level': entry.anxiety_level,
        'created_at': entry.created_at.isoformat() if entry.created_at else datetime.utcnow().isoformat(),
        'content': entry.content[:100] if entry.content else "",  # Only send snippet for privacy/performance
        'is_analyzed': entry.is_analyzed
    } for entry in all_entries]

    # Calculate trend and statistics
    anxiety_avg = None
    anxiety_trend = None

    if all_entries:
        anxiety_levels = [entry.anxiety_level for entry in all_entries if entry.anxiety_level is not None]
        if anxiety_levels:
            anxiety_avg = sum(anxiety_levels) / len(anxiety_levels)

            # Calculate trend if we have enough entries
            if len(anxiety_levels) >= 5:
                recent_entries = all_entries[:5]
                older_entries = all_entries[-5:] if len(all_entries) > 10 else all_entries[:5]

                recent_anxiety = [e.anxiety_level for e in recent_entries if e.anxiety_level is not None]
                older_anxiety = [e.anxiety_level for e in older_entries if e.anxiety_level is not None]

                if recent_anxiety and older_anxiety:
                    recent_avg = sum(recent_anxiety) / len(recent_anxiety)
                    older_avg = sum(older_anxiety) / len(older_anxiety)
                    anxiety_trend = recent_avg - older_avg

    # Get recurring patterns if user has enough entries
    recurring_patterns = []
    entry_count = count_user_entries(current_user.id)
    if entry_count >= 3:
        recurring_patterns = get_recurring_patterns(current_user.id)

    # Pass statistics to the template
    stats = {
        'total_entries': len(all_entries),
        'anxiety_avg': round(anxiety_avg, 1) if anxiety_avg is not None else None,
        'anxiety_trend': anxiety_trend,
        'recurring_patterns': recurring_patterns
    }

    return render_template('journal.html', 
                          title='Journal', 
                          entries=entries, 
                          journal_data=journal_data,
                          stats=stats)

# Create new journal entry
@journal_bp.route('/new', methods=['GET', 'POST'])
@login_required
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
            return render_template('journal_entry.html', title='New Journal Entry', 
                                  form=form, legend='New Journal Entry')

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
                # Check for different error patterns
                if pattern["pattern"] == "API Quota Exceeded":
                    is_api_error = True
                elif pattern["pattern"] == "API Configuration Issue":
                    is_config_error = True

                # Save recommendation to database
                recommendation = CBTRecommendation(
                    thought_pattern=pattern["pattern"],
                    recommendation=f"{pattern['description']} - {pattern['recommendation']}",
                    journal_entry_id=entry.id
                )
                db.session.add(recommendation)

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
                    # Split into paragraphs
                    paragraphs = gpt_response.split('\n\n')
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
                    entry.initial_insight = "".join(formatted_paragraphs)
                else:
                    entry.initial_insight = gpt_response

            db.session.commit()

            # Save the complete journal entry to JSON file
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
                    'streak_30': "Studies show that a month of journaling can reduce intrusive thoughts by up to 20%.",
                    'entries_5': "Writing about emotions reduces their intensity by activating the prefrontal cortex, which helps regulate the amygdala.",
                    'entries_20': "Regular journaling has been linked to a 28% reduction in anxiety symptoms over time.",
                    'entries_50': "Long-term journaling strengthens neural connections between the logical and emotional centers of your brain.",
                    'first_cbt_insight': "Recognizing thought patterns activates your brain's executive function, which helps you respond rather than react.",
                    'mood_tracker_5': "Consistent mood tracking improves emotional awareness by activating the anterior cingulate cortex in your brain.",
                    'breathing_session': "Controlled breathing activates your vagus nerve, which can reduce anxiety within 90 seconds."
                }

                # Get the wellness fact for this badge type or use a default
                wellness_fact = wellness_facts.get(first_badge_id, "Journaling regularly can improve your mental wellness by strengthening neural pathways related to self-awareness.")

                # Store the badge data and wellness fact in the session for rendering
                from flask import session
                session['earned_badge'] = badge
                session['wellness_fact'] = wellness_fact

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error analyzing journal entry: {error_msg}")

            try:
                # Update the entry to indicate analysis failed
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

    return render_template('journal_entry.html', title='New Journal Entry', 
                          form=form, legend='New Journal Entry',
                          structured_data={'insight_text': '', 'reflection_prompt': ''})

# View journal entry
@journal_bp.route('/<int:entry_id>')
@login_required
def view_journal_entry(entry_id):
    logger.info(f"User {current_user.id} viewing journal entry {entry_id}")
    
    # Use undefer() to explicitly load the deferred columns
    entry = JournalEntry.query.options(
        undefer(JournalEntry.user_reflection),
        undefer(JournalEntry.second_reflection)
    ).get_or_404(entry_id)

    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        logger.warning(f"Unauthorized access attempt: User {current_user.id} tried to access entry {entry_id} belonging to user {entry.user_id}")
        abort(403)

    # Create form only if we need to edit (which we don't in view mode)
    form = None

    # Check if we have an earned badge to display
    from flask import session
    earned_badge = session.pop('earned_badge', None)
    wellness_fact = session.pop('wellness_fact', None)

    # Clean markdown symbols from various insights if they exist
    fields_to_clean = {
        'initial_insight': entry.initial_insight,
        'followup_insight': entry.followup_insight,
        'closing_message': entry.closing_message
    }

    changes_made = False
    for field_name, field_value in fields_to_clean.items():
        if field_value:
            logger.debug(f"Cleaning markdown symbols from {field_name} for entry {entry_id}")
            # Remove markdown symbols completely
            cleaned_value = re.sub(r'(^|\s)#+\s', ' ', field_value)  # Remove heading hashtags
            cleaned_value = re.sub(r'\*\*', '', cleaned_value)  # Remove bold markers
            cleaned_value = re.sub(r'\*', '', cleaned_value)  # Remove italic markers
            cleaned_value = re.sub(r'^\s*[•\-]\s+', '', cleaned_value, flags=re.MULTILINE)  # Remove bullet points
            cleaned_value = re.sub(r'\s{2,}', ' ', cleaned_value)  # Clean multiple spaces

            # Only update if cleaning made changes
            if cleaned_value != field_value:
                setattr(entry, field_name, cleaned_value)
                changes_made = True
                logger.debug(f"Markdown symbols cleaned from {field_name}")

    if changes_made:
        db.session.commit()
        logger.debug(f"Saved cleaned markdown fields to database")

    # Initialize variables
    coach_response = ""
    user_entries = get_journal_entries_for_user(current_user.id)

    # Check conversation state - if initial insight is missing but we have an analyzed entry,
    # populate it from the GPT response
    if entry.is_analyzed and not entry.initial_insight:
        logger.debug(f"Entry {entry_id} is analyzed but missing initial_insight, fetching from JSON")

        # Try to get from saved journal entries first
        for json_entry in user_entries:
            if json_entry.get('id') == entry_id:
                coach_response = json_entry.get('gpt_response', "")
                structured_data = json_entry.get('structured_data', None)

                # If we have structured data, use it to populate the conversation fields
                if structured_data and isinstance(structured_data, dict):
                    logger.debug("Found structured data in JSON, using to populate conversation fields")
                    if 'insight_text' in structured_data:
                        entry.initial_insight = structured_data.get('insight_text')
                    if 'reflection_prompt' in structured_data:
                        # Include the reflection prompt at the end of the initial insight
                        if entry.initial_insight:
                            entry.initial_insight += f"\n\n{structured_data.get('reflection_prompt')}"
                        else:
                            entry.initial_insight = structured_data.get('reflection_prompt')
                    db.session.commit()
                    logger.debug(f"Updated entry {entry_id} with conversation fields from JSON")
                else:
                    # Fallback - set the initial_insight to the coach_response with formatting
                    logger.debug(f"No structured data available, formatting coach_response for initial_insight")

                    # Format the insight for better readability
                    if coach_response:
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
                        entry.initial_insight = "".join(formatted_paragraphs)
                    else:
                        entry.initial_insight = coach_response

                    db.session.commit()
                    logger.debug(f"Updated entry {entry_id} with formatted coach_response as initial_insight")

                break
    else:
        # Get coach_response from JSON if available
        for json_entry in user_entries:
            if json_entry.get('id') == entry_id:
                coach_response = json_entry.get('gpt_response', "")
                break

    # If not found, generate a new one
    if not coach_response:
        try:
            analysis_result = analyze_journal_with_gpt(
                journal_text=entry.content, 
                anxiety_level=entry.anxiety_level,
                user_id=current_user.id
            )
            coach_response = analysis_result.get("gpt_response")
            cbt_patterns = analysis_result.get("cbt_patterns", [])

            # Save the updated entry with the response
            save_journal_entry(
                entry_id=entry.id,
                user_id=current_user.id,
                title=entry.title,
                content=entry.content,
                anxiety_level=entry.anxiety_level,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
                is_analyzed=entry.is_analyzed,
                gpt_response=coach_response,
                cbt_patterns=cbt_patterns,
                structured_data=analysis_result.get("structured_data", None)
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating automatic coach response: {error_msg}")

            # Provide different messages based on error type
            if "API_QUOTA_EXCEEDED" in error_msg:
                coach_response = "Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Remember that the act of journaling itself is a powerful tool for self-reflection and growth.\n\nWarmly,\nCoach Mira"
            elif "INVALID_API_KEY" in error_msg:
                coach_response = "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself.\n\nWarmly,\nCoach Mira"
            else:
                coach_response = "Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey.\n\nWarmly,\nCoach Mira"

    # Get recurring patterns if user has enough entries
    recurring_patterns = []
    entry_count = count_user_entries(current_user.id)
    if entry_count >= 3:
        recurring_patterns = get_recurring_patterns(current_user.id)

    # Add a flag to show the emergency call button when anxiety level is high (8 or higher)
    show_call_button = entry.anxiety_level >= 8

    # Create a form object to pass to the template
    form = JournalEntryForm()

    # Debug logging to help identify issues
    logger.debug(f"Journal entry {entry_id} details:")
    logger.debug(f"is_analyzed: {entry.is_analyzed}")
    logger.debug(f"coach_response length: {len(coach_response) if coach_response else 0}")
    logger.debug(f"coach_response: {coach_response[:100]}...")

    # Format the coach response with markdown conversion
    if coach_response:
        # Convert any markdown formatting to proper HTML
        formatted_response = convert_markdown_to_html(coach_response)

        # Double-check for any leftover markdown symbols
        formatted_response = formatted_response.replace('#', '')
        formatted_response = formatted_response.replace('*', '')
        formatted_response = formatted_response.replace('- ', '')
        formatted_response = re.sub(r'^\s*-\s*', '', formatted_response, flags=re.MULTILINE)

        # Clean up any double spaces that might have been created during cleaning
        formatted_response = re.sub(r'\s{2,}', ' ', formatted_response)

        # Add paragraph tags around the whole response if they're not already there
        if not formatted_response.startswith("<p>") and not formatted_response.startswith("<h4") and not formatted_response.startswith("<div"):
            formatted_response = f"<p>{formatted_response}</p>"

        styled_coach_response = f'<div style="color: #000000;">{formatted_response}</div>'
    else:
        styled_coach_response = f'<div style="color: #000000;">{coach_response}</div>'

    # Get structured data if available
    structured_data = None
    for json_entry in user_entries:
        if json_entry.get('id') == entry_id:
            structured_data = json_entry.get('structured_data')
            logger.debug(f"Found structured_data in JSON for entry {entry_id}: {structured_data is not None}")
            if structured_data:
                logger.debug(f"structured_data keys: {list(structured_data.keys()) if isinstance(structured_data, dict) else 'not a dict'}")
            break
    
    # If no structured data found, create default empty structure
    if not structured_data:
        logger.debug(f"No structured_data found for entry {entry_id}, creating default structure")
        structured_data = {
            'insight_text': entry.initial_insight or '',
            'reflection_prompt': "What thoughts come to mind as you reflect on this entry?",
        }
        logger.debug(f"Created default structured_data with keys: {list(structured_data.keys())}")

    return render_template('journal_entry.html', 
                          title=entry.title, 
                          entry=entry, 
                          form=form,
                          view_only=True, 
                          coach_response=styled_coach_response,
                          structured_data=structured_data,
                          recurring_patterns=recurring_patterns,
                          show_call_button=show_call_button,
                          earned_badge=earned_badge,
                          wellness_fact=wellness_fact)

# Update journal entry
@journal_bp.route('/<int:entry_id>/update', methods=['GET', 'POST'])
@login_required
def update_journal_entry(entry_id):
    # Use undefer() to explicitly load the deferred user_reflection column when needed
    entry = JournalEntry.query.options(undefer(JournalEntry.user_reflection)).get_or_404(entry_id)

    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)

    form = JournalEntryForm()
    if form.validate_on_submit():
        # First update the basic entry data
        entry.title = form.title.data
        entry.content = form.content.data
        entry.anxiety_level = form.anxiety_level.data
        entry.updated_at = datetime.utcnow()

        # Save the changes immediately so they're not lost if analysis fails
        db.session.commit()

        # Clear old recommendations
        CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()

        # Re-analyze the entry with the improved GPT analysis
        try:
            analysis_result = analyze_journal_with_gpt(
                journal_text=form.content.data, 
                anxiety_level=form.anxiety_level.data,
                user_id=current_user.id
            )

            gpt_response = analysis_result.get("gpt_response")
            cbt_patterns = analysis_result.get("cbt_patterns", [])

            # Save the patterns to the database
            is_api_error = False
            is_config_error = False

            for pattern in cbt_patterns:
                # Check for different error patterns
                if pattern["pattern"] == "API Quota Exceeded":
                    is_api_error = True
                elif pattern["pattern"] == "API Configuration Issue":
                    is_config_error = True

                # Save recommendation to database
                recommendation = CBTRecommendation(
                    thought_pattern=pattern["pattern"],
                    recommendation=f"{pattern['description']} - {pattern['recommendation']}",
                    journal_entry_id=entry.id
                )
                db.session.add(recommendation)

            entry.is_analyzed = True
            db.session.commit()

            # Save the updated journal entry to JSON file
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
                structured_data=analysis_result.get("structured_data", None)
            )

            # Show appropriate message based on error type
            if is_api_error:
                flash('Your journal entry has been updated! AI analysis is currently unavailable due to API usage limits.', 'info')
            elif is_config_error:
                flash('Your journal entry has been updated! AI analysis is currently unavailable due to a configuration issue.', 'info')
            else:
                flash('Your journal entry has been updated with new AI analysis!', 'success')

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error analyzing journal entry: {error_msg}")

            # Update the entry to indicate analysis failed
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
                flash('Your journal entry has been updated! AI analysis is currently unavailable due to API usage limits.', 'info')
            elif "INVALID_API_KEY" in error_msg:
                flash('Your journal entry has been updated! AI analysis is currently unavailable due to a configuration issue.', 'info')
            else:
                flash('Your journal entry has been updated, but analysis could not be completed. You can try analyzing it later.', 'warning')

        # Wrap the redirect in a try/except to guarantee we don't have a blank page
        try:
            # Use direct path instead of url_for
            return redirect(f'/journal/{entry.id}')
        except Exception as redirect_error:
            logger.error(f"Critical error during redirect after update: {str(redirect_error)}")
            # Use a hardcoded URL as absolute fallback to avoid blank page
            flash('Your journal entry has been updated. Redirecting to journal list.', 'info')
            # Use direct path instead of url_for
            return redirect('/journal')

    # Pre-populate the form with existing data
    elif request.method == 'GET':
        form.title.data = entry.title
        form.content.data = entry.content
        form.anxiety_level.data = entry.anxiety_level

    return render_template('journal_entry.html', 
                          title='Update Journal Entry', 
                          form=form, 
                          legend='Update Journal Entry')

# API route to get the coach response for a journal entry
@journal_bp.route('/api/<int:entry_id>/coach', methods=['GET'])
@journal_bp.route('/api/journal-coach/<int:entry_id>', methods=['GET', 'POST'])
@journal_bp.route('/api_journal_coach/<int:entry_id>', methods=['GET', 'POST'])  # Legacy support
@login_required
def api_journal_coach(entry_id):
    # Use undefer() to explicitly load the deferred user_reflection column when needed
    entry = JournalEntry.query.options(undefer(JournalEntry.user_reflection)).get_or_404(entry_id)

    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)

    # Get the GPT response from JSON file or generate it if missing
    coach_response = ""
    structured_data = None

    # Try to get from saved journal entries first
    user_entries = get_journal_entries_for_user(current_user.id)
    for json_entry in user_entries:
        if json_entry.get('id') == entry_id:
            coach_response = json_entry.get('gpt_response', "")
            structured_data = json_entry.get('structured_data')
            break

    # If not found, generate a new one
    if not coach_response:
        try:
            analysis_result = analyze_journal_with_gpt(
                journal_text=entry.content, 
                anxiety_level=entry.anxiety_level,
                user_id=current_user.id
            )
            coach_response = analysis_result.get("gpt_response")
            structured_data = analysis_result.get("structured_data")

            # We'll save the full analysis in the background but don't need to wait for it
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating API coach response: {error_msg}")

            # Provide different messages based on error type
            if "API_QUOTA_EXCEEDED" in error_msg:
                coach_response = "Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Remember that the act of journaling itself is a powerful tool for self-reflection and growth.\n\nWarmly,\nCoach Mira"
            elif "INVALID_API_KEY" in error_msg:
                coach_response = "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself.\n\nWarmly,\nCoach Mira"
            else:
                coach_response = "Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey.\n\nWarmly,\nCoach Mira"
            structured_data = None

    # Format the coach response with markdown conversion
    if coach_response:
        # Convert any markdown formatting to proper HTML
        formatted_response = convert_markdown_to_html(coach_response)

        # Double-check for any leftover markdown symbols
        formatted_response = formatted_response.replace('#', '')
        formatted_response = formatted_response.replace('*', '')
        formatted_response = formatted_response.replace('- ', '')
        formatted_response = re.sub(r'^\s*-\s*', '', formatted_response, flags=re.MULTILINE)

        # Clean up any double spaces that might have been created during cleaning
        formatted_response = re.sub(r'\s{2,}', ' ', formatted_response)

        # Our enhanced converter now handles both markdown and legacy formats
        if "##" not in coach_response and "**" not in coach_response:
            # Replace newlines with <br> tags for proper paragraph breaks
            formatted_response = formatted_response.replace("\n\n", "</p><p>").replace("\n", "<br>")

            # Format section headers with more emphasis for legacy content
            formatted_response = formatted_response.replace("Here are a few thought patterns", "<h5 class='mt-4 mb-3'>Thought Patterns</h5>")
            formatted_response = formatted_response.replace("Here are a few gentle CBT strategies", "<h5 class='mt-4 mb-3'>CBT Strategies</h5>")
            formatted_response = formatted_response.replace("And a little reflection for today:", "<h5 class='mt-4 mb-3'>Reflection Prompt</h5>")

        # Add paragraph tags around the whole response if they're not already there
        if not formatted_response.startswith("<p>") and not formatted_response.startswith("<h4") and not formatted_response.startswith("<div"):
            formatted_response = f"<p>{formatted_response}</p>"

        styled_coach_response = f'<div style="color: #000000; font-weight: normal; background-color: white;">{formatted_response}</div>'
    else:
        styled_coach_response = f'<div style="color: #000000; font-weight: normal; background-color: white;">{coach_response}</div>'

    return jsonify({
        'success': True, 
        'response': styled_coach_response,
        'structured_data': structured_data
    })

# API endpoint for analyzing a journal entry
@journal_bp.route('/api/analyze-entry/<int:entry_id>', methods=['GET', 'POST'])
@journal_bp.route('/api_analyze_entry/<int:entry_id>', methods=['GET', 'POST'])  # Legacy support
@login_required
def api_analyze_entry(entry_id):
    # Use undefer() to explicitly load the deferred user_reflection column when needed
    entry = JournalEntry.query.options(undefer(JournalEntry.user_reflection)).get_or_404(entry_id)

    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)

    try:
        # Clear old recommendations
        CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()

        # Analyze the entry using the GPT service
        analysis_result = analyze_journal_with_gpt(
            journal_text=entry.content, 
            anxiety_level=entry.anxiety_level,
            user_id=current_user.id
        )

        gpt_response = analysis_result.get("gpt_response")
        cbt_patterns = analysis_result.get("cbt_patterns", [])

        # Save the patterns to the database
        is_api_error = False
        is_config_error = False

        for pattern in cbt_patterns:
            # Check for different error patterns
            if pattern["pattern"] == "API Quota Exceeded":
                is_api_error = True
            elif pattern["pattern"] == "API Configuration Issue":
                is_config_error = True

            # Save recommendation to database
            recommendation = CBTRecommendation(
                thought_pattern=pattern["pattern"],
                recommendation=f"{pattern['description']} - {pattern['recommendation']}",
                journal_entry_id=entry.id
            )
            db.session.add(recommendation)

        entry.is_analyzed = True
        db.session.commit()

        # Save the complete journal entry to JSON file
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
            structured_data=analysis_result.get("structured_data", None)
        )

        # Return appropriate response based on error type
        if is_api_error:
            return jsonify({
                'success': True,
                'status': 'API_LIMIT',
                'message': 'Entry saved. AI analysis is currently unavailable due to API usage limits.',
                'recommendations': [{'pattern': r.thought_pattern, 'recommendation': r.recommendation} 
                                for r in entry.recommendations]
            })
        elif is_config_error:
            return jsonify({
                'success': True,
                'status': 'CONFIG_ERROR',
                'message': 'Entry saved. AI analysis is currently unavailable due to a configuration issue.',
                'recommendations': [{'pattern': r.thought_pattern, 'recommendation': r.recommendation} 
                                for r in entry.recommendations]
            })
        else:
            return jsonify({
                'success': True,
                'status': 'SUCCESS',
                'message': 'Entry analyzed successfully!',
                'recommendations': [{'pattern': r.thought_pattern, 'recommendation': r.recommendation} 
                                for r in entry.recommendations]
            })

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error analyzing journal entry: {error_msg}")

        # Save the entry even if analysis fails
        entry.is_analyzed = False
        db.session.commit()

        # Return more specific error messages
        if "API_QUOTA_EXCEEDED" in error_msg:
            return jsonify({
'success': False,
                'status': 'API_LIMIT',
                'message': 'Your entry was saved, but AI analysis is currently unavailable due to API limits.'
            }), 429
        elif "INVALID_API_KEY" in error_msg:
            return jsonify({
                'success': False,
                'status': 'CONFIG_ERROR',
                'message': 'Your entry was saved, but AI analysis is currently unavailable due to a configuration issue.'
            }), 500
        else:
            return jsonify({
                'success': False,
                'status': 'ERROR',
                'message': 'Your entry was saved, but there was an error during analysis. You can try again later.'
            }), 500

# Delete journal entry
@journal_bp.route('/<int:entry_id>/delete_entry', methods=['GET', 'POST'])
@login_required
def delete_journal_entry(entry_id):
    # Use undefer() to explicitly load the deferred user_reflection column when needed
    entry = JournalEntry.query.options(undefer(JournalEntry.user_reflection)).get_or_404(entry_id)

    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)

    try:
        # Delete recommendations first (cascade doesn't work with SQLAlchemy without setup)
        CBTRecommendation.query.filter_by(journal_entry_id=entry.id).delete()

        # Delete the entry from database
        db.session.delete(entry)
        db.session.commit()

        # Also delete from JSON storage to update insights/patterns
        from journal_service import delete_journal_entry as delete_json_entry
        delete_success = delete_json_entry(entry_id, current_user.id)

        if delete_success:
            logger.debug(f"Successfully deleted journal entry {entry_id} from database and JSON storage")
        else:
            logger.warning(f"Deleted journal entry {entry_id} from database but not found in JSON storage")

        flash('Your journal entry has been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting journal entry {entry_id}: {str(e)}")
        flash('An error occurred while deleting your journal entry. Please try again.', 'danger')

    # Use the same error-handling pattern here for consistency
    try:
        # Use direct path instead of url_for
        return redirect('/journal')
    except Exception as redirect_error:
        logger.error(f"Critical error during redirect after deletion: {str(redirect_error)}")
        # Provide a direct HTML response as absolute fallback
        return '<html><body><p>Your journal entry has been processed.</p><p><a href="/">Return to Home</a></p></body></html>'
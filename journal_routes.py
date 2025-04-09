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
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
journal_bp = Blueprint('journal_blueprint', __name__, url_prefix='/journal')

# Journal entry list
@journal_bp.route('/')
@login_required
def journal_list():
    page = request.args.get('page', 1, type=int)
    entries = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(desc(JournalEntry.created_at))\
        .paginate(page=page, per_page=10)
    
    # Get all entries for visualization (limiting to last 30 for performance)
    all_entries = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(desc(JournalEntry.created_at))\
        .limit(30).all()
    
    # Format the entry data for visualization
    journal_data = [{
        'id': entry.id,
        'title': entry.title,
        'anxiety_level': entry.anxiety_level,
        'created_at': entry.created_at.isoformat(),
        'content': entry.content[:100],  # Only send snippet for privacy/performance
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
        # Check for recently created similar entries to prevent duplicates
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_entries = JournalEntry.query.filter_by(
            user_id=current_user.id,
            title=form.title.data
        ).filter(JournalEntry.created_at >= five_minutes_ago).all()
        
        # If a similar entry was recently created, redirect to that entry
        if recent_entries:
            logger.info(f"Prevented duplicate entry: {form.title.data}")
            flash('A similar journal entry was just created. Redirecting to the existing entry.', 'info')
            return redirect(url_for('journal_blueprint.view_journal_entry', entry_id=recent_entries[0].id))
        
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
                cbt_patterns=cbt_patterns
            )
            
            # Show appropriate message based on error type
            if is_api_error:
                flash('Your journal entry has been saved! AI analysis is currently unavailable due to API usage limits.', 'info')
            elif is_config_error:
                flash('Your journal entry has been saved! AI analysis is currently unavailable due to a configuration issue.', 'info')
            else:
                flash('Your journal entry has been created with AI analysis!', 'success')
            
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
                }]
            )
            
            # Show specific error messages based on error type
            if "API_QUOTA_EXCEEDED" in error_msg:
                flash('Your journal entry has been saved! AI analysis is currently unavailable due to API usage limits.', 'info')
            elif "INVALID_API_KEY" in error_msg:
                flash('Your journal entry has been saved! AI analysis is currently unavailable due to a configuration issue.', 'info')
            else:
                flash('Your journal entry has been saved, but analysis could not be completed. You can try analyzing it later.', 'warning')
        
        return redirect(url_for('journal_blueprint.view_journal_entry', entry_id=entry.id))
    
    return render_template('journal_entry.html', title='New Journal Entry', 
                          form=form, legend='New Journal Entry')

# View journal entry
@journal_bp.route('/<int:entry_id>')
@login_required
def view_journal_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)
    
    # Get the GPT response from JSON file or generate it if missing
    coach_response = ""
    
    # Try to get from saved journal entries first
    user_entries = get_journal_entries_for_user(current_user.id)
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
                cbt_patterns=cbt_patterns
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating automatic coach response: {error_msg}")
            
            # Provide different messages based on error type
            if "API_QUOTA_EXCEEDED" in error_msg:
                coach_response = "Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Remember that the act of journaling itself is a powerful tool for self-reflection and growth."
            elif "INVALID_API_KEY" in error_msg:
                coach_response = "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself."
            else:
                coach_response = "Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey."
    
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
    
    # Wrap the coach response in styled HTML to ensure it's visible
    styled_coach_response = f'<div style="color: #000000;">{coach_response}</div>'
    
    return render_template('journal_entry.html', 
                          title=entry.title, 
                          entry=entry, 
                          form=form,
                          view_only=True, 
                          coach_response=styled_coach_response,
                          recurring_patterns=recurring_patterns,
                          show_call_button=show_call_button)

# Update journal entry
@journal_bp.route('/<int:entry_id>/update', methods=['GET', 'POST'])
@login_required
def update_journal_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    
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
                cbt_patterns=cbt_patterns
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
                }]
            )
            
            # Show specific error messages based on error type
            if "API_QUOTA_EXCEEDED" in error_msg:
                flash('Your journal entry has been updated! AI analysis is currently unavailable due to API usage limits.', 'info')
            elif "INVALID_API_KEY" in error_msg:
                flash('Your journal entry has been updated! AI analysis is currently unavailable due to a configuration issue.', 'info')
            else:
                flash('Your journal entry has been updated, but analysis could not be completed. You can try analyzing it later.', 'warning')
        
        return redirect(url_for('journal_blueprint.view_journal_entry', entry_id=entry.id))
    
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
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Ensure the entry belongs to the current user
    if entry.user_id != current_user.id:
        abort(403)
    
    # Get the GPT response from JSON file or generate it if missing
    coach_response = ""
    
    # Try to get from saved journal entries first
    user_entries = get_journal_entries_for_user(current_user.id)
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
            
            # We'll save the full analysis in the background but don't need to wait for it
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating API coach response: {error_msg}")
            
            # Provide different messages based on error type
            if "API_QUOTA_EXCEEDED" in error_msg:
                coach_response = "Thank you for sharing your thoughts today. While I can't provide a personalized response right now due to technical limitations, your entry has been saved. Remember that the act of journaling itself is a powerful tool for self-reflection and growth."
            elif "INVALID_API_KEY" in error_msg:
                coach_response = "I appreciate you taking the time to journal today. Your entry has been saved, though I'm unable to provide specific feedback at the moment. The practice of putting your thoughts into words is valuable in itself."
            else:
                coach_response = "Thank you for sharing your journal entry. Although I can't offer specific insights right now, the process of writing down your thoughts is an important step in your wellness journey."
    
    # Style the response for better visibility
    styled_coach_response = f'<div style="color: #000000; font-weight: normal; background-color: white;">{coach_response}</div>'
    
    return jsonify({'success': True, 'response': styled_coach_response})

# API endpoint for analyzing a journal entry
@journal_bp.route('/api/analyze-entry/<int:entry_id>', methods=['GET', 'POST'])
@journal_bp.route('/api_analyze_entry/<int:entry_id>', methods=['GET', 'POST'])  # Legacy support
@login_required
def api_analyze_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    
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
            cbt_patterns=cbt_patterns
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
    entry = JournalEntry.query.get_or_404(entry_id)
    
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
    
    return redirect(url_for('journal_blueprint.journal_list'))
"""
One-time script to update existing journal entries to use properly formatted markdown.
This will run through all journal entries and make sure any existing markdown symbols 
are properly converted to HTML.
"""
import sys
import re
from app import app, db
from models import JournalEntry
from journal_routes import convert_markdown_to_html
from journal_service import save_journal_entry

def convert_markdown_to_html(text):
    """
    Convert markdown formatting to HTML for better display.
    
    Args:
        text: Text containing markdown formatting
        
    Returns:
        Text with markdown converted to HTML
    """
    if not text:
        return ""
    
    # First, standardize newlines to avoid inconsistencies
    text = text.replace('\r\n', '\n')
    
    # Process sections in order to avoid formatting conflicts
    
    # 1. Convert markdown headers (##) to styled headers
    text = re.sub(r'##\s+(.*?)$', r'<h4 class="mt-4 mb-3">\1</h4>', text, flags=re.MULTILINE)
    
    # 2. Convert bold text (**text**) to <strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # 3. Convert bullet points
    text = re.sub(r'^\s*•\s+(.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # 4. Wrap lists in <ul> tags
    text = re.sub(r'(<li>.*?</li>\n)+', r'<ul class="mb-3">\n\g<0></ul>', text, flags=re.DOTALL)
    
    # 5. Handle paragraph breaks but avoid extra breaks after headers and before lists
    # Replace double newlines with paragraph breaks, but not if preceded by header or followed by list
    text = re.sub(r'(?<!</h4>)\n\n(?!<ul)', '<br><br>', text)
    
    # 6. Remove any remaining excessive newlines around HTML elements
    text = re.sub(r'\n+(<h4|<ul|<li|</ul>)', r'\1', text)
    text = re.sub(r'(</h4>|</ul>|</li>)\n+', r'\1', text)
    
    return text

def update_existing_journal_entries():
    """
    Update all journal entries to properly format any markdown.
    This should be run once to ensure all existing entries are properly formatted.
    """
    with app.app_context():
        # Get all journal entries
        entries = JournalEntry.query.all()
        
        print(f"Found {len(entries)} journal entries to process")
        updated_count = 0
        
        for entry in entries:
            if not entry.is_analyzed or not entry.initial_insight:
                continue
                
            # Check if the entry contains raw markdown in any field
            fields_to_check = [
                ('initial_insight', entry.initial_insight),
                ('followup_insight', entry.followup_insight),
                ('closing_message', entry.closing_message)
            ]
            
            updated = False
            
            for field_name, field_content in fields_to_check:
                if field_content and ("**" in field_content or "##" in field_content):
                    print(f"Processing entry {entry.id}, field {field_name}...")
                    
                    # Treat this as a markdown entry and convert any symbols
                    # Store the original content in case we need to revert
                    original_content = field_content
                    
                    # Apply markdown conversion
                    try:
                        formatted_content = convert_markdown_to_html(field_content)
                        setattr(entry, field_name, formatted_content)
                        updated = True
                        
                        print(f"Successfully updated entry {entry.id}, field {field_name}")
                    except Exception as e:
                        print(f"Error updating entry {entry.id}, field {field_name}: {str(e)}")
                        # Revert to original content if there was an error
                        setattr(entry, field_name, original_content)
            
            if updated:
                db.session.commit()
                updated_count += 1
                
                # Also update the entry in the JSON file
                try:
                    save_journal_entry(
                        entry_id=entry.id,
                        user_id=entry.user_id,
                        title=entry.title,
                        content=entry.content,
                        anxiety_level=entry.anxiety_level,
                        created_at=entry.created_at,
                        updated_at=entry.updated_at,
                        is_analyzed=entry.is_analyzed,
                        gpt_response=entry.initial_insight
                    )
                except Exception as e:
                    print(f"Error updating entry in JSON file: {str(e)}")
                    
        print(f"Updated {updated_count} journal entries with markdown formatting")
        
if __name__ == "__main__":
    update_existing_journal_entries()
    print("Journal entry formatting update complete")
#!/usr/bin/env python3
"""
Script to fix the pattern processing in journal_routes.py
"""
import sys

def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the first occurrence (new journal entry)
    old_pattern_code = """            # Save the patterns to the database
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
                db.session.add(recommendation)"""
    
    new_pattern_code = """            # Save the patterns to the database
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
                    # Continue with the next pattern instead of failing completely"""
    
    content = content.replace(old_pattern_code, new_pattern_code, 1)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Updated {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_pattern_processing.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    fix_file(file_path)
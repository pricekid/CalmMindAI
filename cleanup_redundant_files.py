#!/usr/bin/env python3
"""
Script to remove redundant authentication and registration files.
Keeps only the core functionality needed for the application.
"""

import os
import shutil

# Files to remove - these are redundant or experimental
files_to_remove = [
    # Redundant login systems
    "emergency_login.py",
    "emergency_hardcoded_login.py", 
    "emergency_direct_login.py",
    "emergency_standalone.py",
    "emergency_app.py",
    "emergency_dashboard.py",
    "emergency_admin.py",
    "emergency_production_fix.py",
    "emergency_direct_render.py",
    "debug_production_login.py",
    "production_login_fix.py",
    "minimal_production_login.py",
    "direct_login_fix.py",
    "direct_session_login.py",
    "login_routes.py",
    "render_login_fix.py",
    "stable_login.py",
    "redirect_to_stable.py",
    "test_login.py",
    "test_login_route.py",
    "test_admin_login.py",
    "test_admin_login_request.py",
    "send_basic_login_link.py",
    "send_login_link_to_all_users.py",
    
    # Redundant registration systems  
    "emergency_registration_fix.py",
    "final_register.py",
    "isolated_register.py",
    "minimal_register.py",
    "simple_register.py",
    "working_register.py",
    
    # Redundant test files
    "simple_auth_test.py",
    "basic_test.py",
    "isolated_test.py",
    "minimal_auth_fix.py",
    "direct_production_test.py",
    "direct_test_coach.py",
    "direct_test_followup.py",
    "test_direct_reflection.py",
    
    # Redundant dashboard files
    "simple_dashboard.py",
    
    # Redundant TTS files
    "simple_tts.py",
    "simple_direct_tts.py", 
    "direct_tts.py",
    
    # Redundant email test files
    "direct_email_test.py",
    "direct_sendgrid_test.py",
    "simple_sendgrid_test.py",
    "simpler_sendgrid_test.py",
    
    # Redundant notification files
    "direct_notification_fix.py",
    "simple_fix_notifications.py",
    
    # Redundant test files
    "direct_openai_test.py",
    "create_direct_entry.py",
]

def cleanup_files():
    """Remove redundant files"""
    removed_count = 0
    
    for filename in files_to_remove:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"Removed: {filename}")
                removed_count += 1
            except Exception as e:
                print(f"Error removing {filename}: {e}")
        else:
            print(f"File not found: {filename}")
    
    print(f"\nRemoved {removed_count} redundant files")
    return removed_count

if __name__ == "__main__":
    cleanup_files()
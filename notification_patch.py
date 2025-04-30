"""
Patch for notification_service.py that maintains all function signatures but prevents actual email sending.
"""
import os
import re

def patch_notification_service():
    """
    Patch notification_service.py to prevent sending emails while preserving all function signatures.
    """
    notification_file = "notification_service.py"
    backup_file = f"{notification_file}.original_backup"
    
    if not os.path.exists(notification_file):
        print(f"Error: {notification_file} not found")
        return False
    
    # Create a backup if none exists
    if not os.path.exists(backup_file):
        os.system(f"cp {notification_file} {backup_file}")
        print(f"Created backup at {backup_file}")
    
    with open(notification_file, "r") as f:
        content = f.read()
    
    # Add check_notifications_blocked function if not present
    if "def check_notifications_blocked():" not in content:
        check_function = """
# Function to check if notifications are blocked
def check_notifications_blocked():
    '''Check if notifications are blocked by the existence of a block file'''
    return True  # Always block notifications
"""
        
        # Find a good insertion point (before the first function)
        import_section_end = content.find("def ")
        if import_section_end > 0:
            content = content[:import_section_end] + check_function + content[import_section_end:]
            print("Added check_notifications_blocked function")
    
    # Create our block pattern to modify each function
    block_pattern = """
    # NOTIFICATIONS DISABLED
    logger.info(f"Notification blocked: {func_name}")
    return {"success": False, "error": "Notifications are permanently disabled"}
"""
    
    # Find all function definitions to patch
    function_pattern = r"def ([\w_]+)\(([^)]*)\):"
    functions = re.findall(function_pattern, content)
    
    # Skip certain functions we don't want to patch
    skip_functions = ["check_notifications_blocked", "render_template", "get_template", "load_templates"]
    
    # Track which functions we've patched
    patched_functions = []
    
    # Patch each function
    for func_name, params in functions:
        if func_name in skip_functions:
            continue
        
        # Find the function
        func_def = f"def {func_name}({params}):"
        func_start = content.find(func_def)
        
        if func_start == -1:
            print(f"Warning: Could not find function {func_name}")
            continue
        
        # Find the first line after the function definition
        func_body_start = content.find("\n", func_start) + 1
        while content[func_body_start:func_body_start+4] == "    #" or content[func_body_start:func_body_start+5] == '    "' or content[func_body_start:func_body_start+5] == "    '":
            # Skip over docstring and comments
            next_line = content.find("\n", func_body_start) + 1
            if next_line <= func_body_start:
                break  # No more newlines found
            func_body_start = next_line
        
        # Create the patched function body with our blocking code
        new_block = block_pattern.replace("func_name", func_name)
        
        # Insert our block
        content = content[:func_body_start] + new_block + content[func_body_start:]
        patched_functions.append(func_name)
    
    # Save the modified file
    with open(notification_file, "w") as f:
        f.write(content)
    
    print(f"Patched {len(patched_functions)} functions in {notification_file}:")
    for func in patched_functions:
        print(f"- {func}")
    
    # Create block file
    block_file = "data/notifications_blocked"
    if not os.path.exists("data"):
        os.mkdir("data")
    
    with open(block_file, "w") as f:
        f.write("Notifications permanently blocked")
    
    print(f"Created notification block file: {block_file}")
    return True

if __name__ == "__main__":
    print("Patching notification service to prevent sending emails...")
    if patch_notification_service():
        print("Successfully patched notification service")
    else:
        print("Failed to patch notification service")
"""
Patch for sms_notification_service.py that maintains all function signatures but prevents actual SMS sending.
"""
import os
import re

def patch_sms_notification_service():
    """
    Patch sms_notification_service.py to prevent sending SMS while preserving all function signatures.
    """
    sms_file = "sms_notification_service.py"
    backup_file = f"{sms_file}.original_backup"
    
    if not os.path.exists(sms_file):
        print(f"Error: {sms_file} not found")
        return False
    
    # Create a backup if none exists
    if not os.path.exists(backup_file):
        os.system(f"cp {sms_file} {backup_file}")
        print(f"Created backup at {backup_file}")
    
    with open(sms_file, "r") as f:
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
    # SMS NOTIFICATIONS DISABLED
    logger.info(f"SMS notification blocked: {func_name}")
    return {"success": False, "error": "SMS notifications are permanently disabled"}
"""
    
    # Find all function definitions to patch
    function_pattern = r"def ([\w_]+)\(([^)]*)\):"
    functions = re.findall(function_pattern, content)
    
    # Skip certain functions we don't want to patch
    skip_functions = ["check_notifications_blocked"]
    
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
    with open(sms_file, "w") as f:
        f.write(content)
    
    print(f"Patched {len(patched_functions)} functions in {sms_file}:")
    for func in patched_functions:
        print(f"- {func}")
    
    return True

if __name__ == "__main__":
    print("Patching SMS notification service to prevent sending SMS...")
    if patch_sms_notification_service():
        print("Successfully patched SMS notification service")
    else:
        print("Failed to patch SMS notification service")
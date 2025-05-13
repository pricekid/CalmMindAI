"""
Count entries in backup files to compare with current database.
"""
import json
import os
import glob
from datetime import datetime

def count_users_in_backup():
    """Count users in the backup file."""
    try:
        with open('data/users.json.bak', 'r') as f:
            users = json.load(f)
            print(f"User count in backup: {len(users)}")
            
            # Show some sample user data
            if users:
                print("\nSample users from backup:")
                for i, user in enumerate(users[:5]):
                    print(f"  {i+1}. {user.get('username')} ({user.get('email')}) - ID: {user.get('id')}")
            
            return len(users)
    except Exception as e:
        print(f"Error reading users backup: {e}")
        return 0

def count_journal_entries():
    """Count journal entries in all backup files."""
    total_entries = 0
    try:
        # Check main journals.json file if it exists
        if os.path.exists('data/journals.json.bak'):
            with open('data/journals.json.bak', 'r') as f:
                entries = json.load(f)
                print(f"Entries in journals.json.bak: {len(entries)}")
                total_entries += len(entries)
        
        # Check per-user journal files
        journal_files = glob.glob('data/journals/user_*_journals.json*')
        
        print(f"\nFound {len(journal_files)} journal files")
        for file_path in journal_files:
            try:
                with open(file_path, 'r') as f:
                    entries = json.load(f)
                    print(f"  {file_path}: {len(entries)} entries")
                    total_entries += len(entries)
            except Exception as e:
                print(f"  Error reading {file_path}: {e}")
        
        print(f"\nTotal journal entries in all backup files: {total_entries}")
        return total_entries
    except Exception as e:
        print(f"Error counting journal entries: {e}")
        return 0

if __name__ == "__main__":
    print("Backup Statistics")
    print("=" * 50)
    count_users_in_backup()
    print("\n" + "=" * 50)
    count_journal_entries()
    print("=" * 50)
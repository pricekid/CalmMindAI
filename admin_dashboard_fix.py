#!/usr/bin/env python3
"""
Admin dashboard fix to use real data from the database instead of synthetic data.
This is a permanent fix for the admin dashboard data.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from collections import defaultdict

from app import app, db
from models import JournalEntry, User

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_real_journal_counts():
    """
    Get real journal entry counts from the database for the past 7 days.
    
    Returns:
        tuple: (dates, counts) where dates is a list of date strings and counts is a list of entry counts
    """
    with app.app_context():
        # Get entries from the past 7 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        try:
            entries = db.session.query(JournalEntry).filter(
                JournalEntry.created_at >= start_date,
                JournalEntry.created_at <= end_date
            ).all()
            
            # Group entries by date
            entry_counts = defaultdict(int)
            for entry in entries:
                date_str = entry.created_at.strftime('%Y-%m-%d')
                entry_counts[date_str] += 1
                
            # Generate list for all 7 days even if no entries
            dates = []
            counts = []
            
            for i in range(6, -1, -1):
                date = end_date - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                dates.append(date_str)
                counts.append(entry_counts.get(date_str, 0))
                
            logger.info(f"Found {sum(counts)} journal entries in the past 7 days")
            return dates, counts
        except Exception as e:
            logger.error(f"Error getting journal counts: {e}")
            # Return dummy data in case of error
            dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
            return dates, [0] * 7

def get_database_stats():
    """
    Get real statistics from the database.
    
    Returns:
        dict: Statistics about the database
    """
    with app.app_context():
        try:
            # Get user count
            user_count = db.session.query(User).count()
            
            # Get journal count
            journal_count = db.session.query(JournalEntry).count()
            
            # Get journals in the past 24 hours
            last_day = datetime.utcnow() - timedelta(days=1)
            recent_journals = db.session.query(JournalEntry).filter(JournalEntry.created_at >= last_day).count()
            
            # Get average anxiety level
            anxiety_query = db.session.query(db.func.avg(JournalEntry.anxiety_level))
            anxiety_query = anxiety_query.filter(JournalEntry.anxiety_level != None)
            avg_anxiety = anxiety_query.scalar() or 0
            
            stats = {
                "user_count": user_count,
                "journal_count": journal_count,
                "recent_journals": recent_journals,
                "avg_anxiety": round(avg_anxiety, 1)
            }
            
            logger.info(f"Database stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                "user_count": 0,
                "journal_count": 0,
                "recent_journals": 0,
                "avg_anxiety": 0
            }

def update_admin_utils():
    """
    Update the admin_utils.py file to use real data from the database.
    """
    file_path = "admin_utils.py"
    if not os.path.exists(file_path):
        logger.error(f"admin_utils.py not found at {file_path}")
        return False
    
    # Create backup
    backup_path = file_path + '.bak'
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the get_admin_stats function
        func_def = "def get_admin_stats():"
        if func_def not in content:
            logger.error("Could not find get_admin_stats function in admin_utils.py")
            return False
        
        # Replace the function implementation
        func_start = content.find(func_def)
        next_func = content.find("def ", func_start + len(func_def))
        if next_func == -1:
            logger.error("Could not find end of get_admin_stats function")
            return False
        
        new_func = """def get_admin_stats():
    \"\"\"Get statistics for the admin dashboard\"\"\"
    from app import db
    from models import User, JournalEntry
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    try:
        # Get user count
        user_count = db.session.query(User).count()
        
        # Get journal count
        journal_count = db.session.query(JournalEntry).count()
        
        # Get journals in the past 24 hours
        last_day = datetime.utcnow() - timedelta(days=1)
        recent_journals = db.session.query(JournalEntry).filter(JournalEntry.created_at >= last_day).count()
        
        # Get average anxiety level
        anxiety_query = db.session.query(db.func.avg(JournalEntry.anxiety_level))
        anxiety_query = anxiety_query.filter(JournalEntry.anxiety_level != None)
        avg_anxiety = anxiety_query.scalar() or 0
        
        # Get journal counts for the last 7 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        entries = db.session.query(JournalEntry).filter(
            JournalEntry.created_at >= start_date,
            JournalEntry.created_at <= end_date
        ).all()
        
        # Group entries by date
        entry_counts = defaultdict(int)
        for entry in entries:
            date_str = entry.created_at.strftime('%Y-%m-%d')
            entry_counts[date_str] += 1
            
        # Generate list for all 7 days even if no entries
        dates = []
        counts = []
        
        for i in range(6, -1, -1):
            date = end_date - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            dates.append(date_str)
            counts.append(entry_counts.get(date_str, 0))
        
        stats = {
            "user_count": user_count,
            "journal_count": journal_count,
            "recent_journals": recent_journals,
            "avg_anxiety": round(avg_anxiety, 1),
            "journal_dates": dates,
            "journal_counts": counts
        }
        
        return stats
    except Exception as e:
        print(f"Error getting admin stats: {e}")
        # Return minimal stats to prevent dashboard errors
        return {
            "user_count": 0,
            "journal_count": 0,
            "recent_journals": 0,
            "avg_anxiety": 0,
            "journal_dates": [],
            "journal_counts": []
        }
"""
        
        # Replace the function
        new_content = content[:func_start] + new_func + content[next_func:]
        
        # Write the updated file
        with open(file_path, 'w') as f:
            f.write(new_content)
            
        logger.info("Successfully updated admin_utils.py to use real data")
        return True
    except Exception as e:
        logger.error(f"Error updating admin_utils.py: {e}")
        return False

def update_admin_dashboard_template():
    """
    Update the admin dashboard template to use real data.
    """
    template_path = "templates/admin/dashboard.html"
    if not os.path.exists(template_path):
        logger.error(f"Admin dashboard template not found at {template_path}")
        return False
    
    # Create backup
    backup_path = template_path + '.real_data.bak'
    try:
        import shutil
        shutil.copy2(template_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False
    
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Find the chart script section
        chart_script_start = "document.addEventListener('DOMContentLoaded', function() {"
        chart_script_end = "});"
        
        if chart_script_start not in content or chart_script_end not in content:
            logger.error("Could not find chart script in template")
            return False
        
        # Create replacement that uses server-provided data
        chart_replacement = """document.addEventListener('DOMContentLoaded', function() {
    // Journal Activity Chart
    const dates = {{ stats.journal_dates|tojson }};
    const counts = {{ stats.journal_counts|tojson }};
    
    const ctx = document.getElementById('journalActivityChart').getContext('2d');
    const journalChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Journal Entries',
                data: counts,
                backgroundColor: 'rgba(13, 202, 240, 0.6)', // Bootstrap info color with transparency
                borderColor: 'rgba(13, 202, 240, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });"""
        
        # Find and replace the chart script
        start_idx = content.find(chart_script_start)
        end_idx = content.find(chart_script_end, start_idx) + len(chart_script_end)
        new_content = content[:start_idx] + chart_replacement + content[end_idx:]
        
        # Write the patched content
        with open(template_path, 'w') as f:
            f.write(new_content)
            
        logger.info("Successfully updated admin dashboard template to use real data")
        return True
    except Exception as e:
        logger.error(f"Error updating admin dashboard template: {e}")
        return False

def main():
    """
    Apply all the fixes to use real data in the admin dashboard.
    """
    logger.info("Starting admin dashboard fixes")
    
    # Get real statistics for verification
    dates, counts = get_real_journal_counts()
    logger.info(f"Real journal counts for the past 7 days: {counts}")
    stats = get_database_stats()
    
    # Update admin utils to use real data
    utils_updated = update_admin_utils()
    logger.info(f"Admin utils update {'succeeded' if utils_updated else 'failed'}")
    
    # Update admin dashboard template
    template_updated = update_admin_dashboard_template()
    logger.info(f"Admin dashboard template update {'succeeded' if template_updated else 'failed'}")
    
    logger.info("Admin dashboard fixes complete")
    return utils_updated and template_updated

if __name__ == "__main__":
    success = main()
    print("Admin dashboard fixes " + ("successful" if success else "failed"))
"""
Script to check the next scheduled run time for email notifications.
"""
import os
import json
import datetime
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def calculate_next_notification():
    """Calculate when the next notification will be sent."""
    # Based on the scheduler configuration, notifications are sent at 6:00 AM
    now = datetime.datetime.now()
    today_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    # If it's already past 6 AM today, the next notification will be tomorrow at 6 AM
    if now > today_6am:
        next_notification = today_6am + datetime.timedelta(days=1)
    else:
        next_notification = today_6am
    
    # Format the time for display
    next_notification_str = next_notification.strftime("%Y-%m-%d %H:%M:%S")
    time_until = next_notification - now
    
    # Hours and minutes until next notification
    hours, remainder = divmod(time_until.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    logger.info(f"Next scheduled notification: {next_notification_str}")
    logger.info(f"Time until next notification: {time_until.days} days, {hours} hours, {minutes} minutes")
    
    return {
        "next_notification": next_notification_str,
        "time_until": {
            "days": time_until.days,
            "hours": hours,
            "minutes": minutes
        }
    }

def check_sent_notifications():
    """Check which notifications have been sent today."""
    try:
        tracking_file = "data/email_notifications_sent.json"
        
        if not os.path.exists(tracking_file):
            logger.info("No notification tracking file found.")
            return {"tracking_file_exists": False}
        
        with open(tracking_file, "r") as f:
            tracking_data = json.load(f)
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        email_sent = []
        sms_sent = []
        weekly_summary_sent = []
        
        if "email" in tracking_data and today in tracking_data["email"]:
            email_sent = tracking_data["email"][today]
        
        if "sms" in tracking_data and today in tracking_data["sms"]:
            sms_sent = tracking_data["sms"][today]
        
        if "weekly_summary" in tracking_data and today in tracking_data["weekly_summary"]:
            weekly_summary_sent = tracking_data["weekly_summary"][today]
        
        logger.info(f"Notifications sent today ({today}):")
        logger.info(f"  Email: {len(email_sent)} users")
        logger.info(f"  SMS: {len(sms_sent)} users")
        logger.info(f"  Weekly Summary: {len(weekly_summary_sent)} users")
        
        return {
            "tracking_file_exists": True,
            "today": today,
            "email_sent": len(email_sent),
            "sms_sent": len(sms_sent),
            "weekly_summary_sent": len(weekly_summary_sent)
        }
    except Exception as e:
        logger.error(f"Error checking sent notifications: {str(e)}")
        return {"error": str(e)}

def check_scheduler_logs():
    """Check recent scheduler logs for notification activities."""
    try:
        log_file = "data/scheduler_logs.json"
        
        if not os.path.exists(log_file):
            logger.info("No scheduler logs found.")
            return {"logs_exist": False}
        
        with open(log_file, "r") as f:
            logs = json.load(f)
        
        # Get the last 10 logs
        recent_logs = logs[-10:]
        
        logger.info("Recent scheduler activity:")
        for log in recent_logs:
            timestamp = log.get("timestamp", "Unknown")
            log_type = log.get("type", "Unknown")
            message = log.get("message", "No message")
            success = log.get("success", False)
            
            status = "✓" if success else "✗"
            logger.info(f"  [{timestamp}] {status} {log_type}: {message}")
        
        # Check for any notification logs
        notification_logs = [log for log in logs if "notification" in log.get("type", "")]
        recent_notification_logs = notification_logs[-5:] if notification_logs else []
        
        if recent_notification_logs:
            logger.info("\nRecent notification activity:")
            for log in recent_notification_logs:
                timestamp = log.get("timestamp", "Unknown")
                log_type = log.get("type", "Unknown")
                message = log.get("message", "No message")
                success = log.get("success", False)
                
                status = "✓" if success else "✗"
                logger.info(f"  [{timestamp}] {status} {log_type}: {message}")
        else:
            logger.info("\nNo recent notification activity found in logs.")
        
        return {
            "logs_exist": True,
            "recent_logs": recent_logs,
            "recent_notification_logs": recent_notification_logs
        }
    except Exception as e:
        logger.error(f"Error checking scheduler logs: {str(e)}")
        return {"error": str(e)}

def main():
    """Main function to check notification schedule."""
    logger.info("=" * 80)
    logger.info("NOTIFICATION SCHEDULE CHECK")
    logger.info("=" * 80)
    
    # Calculate next notification time
    calculate_next_notification()
    
    logger.info("\n" + "=" * 80)
    logger.info("SENT NOTIFICATIONS CHECK")
    logger.info("=" * 80)
    
    # Check sent notifications
    check_sent_notifications()
    
    logger.info("\n" + "=" * 80)
    logger.info("SCHEDULER LOGS CHECK")
    logger.info("=" * 80)
    
    # Check scheduler logs
    check_scheduler_logs()
    
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
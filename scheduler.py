
from apscheduler.schedulers.blocking import BlockingScheduler
from notification_service import send_daily_reminder
import logging

logging.basicConfig(level=logging.INFO)
scheduler = BlockingScheduler()

# Run every hour to check for users who should receive notifications
scheduler.add_job(send_daily_reminder, 'cron', minute=0)

if __name__ == '__main__':
    logging.info("Starting notification scheduler...")
    scheduler.start()

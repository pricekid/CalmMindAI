
from apscheduler.schedulers.blocking import BlockingScheduler
from notification_service import send_daily_reminder
import logging

logging.basicConfig(level=logging.INFO)
scheduler = BlockingScheduler()

# Run every day at 6 AM to send reminders
# The function will filter users based on their preference time
scheduler.add_job(send_daily_reminder, 'cron', hour='6', minute=0)

if __name__ == '__main__':
    logging.info("Starting notification scheduler...")
    scheduler.start()

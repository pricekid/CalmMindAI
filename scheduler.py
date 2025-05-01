import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simply log that scheduler is disabled
logger.info("Scheduler disabled")
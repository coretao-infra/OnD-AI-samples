import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")


logger = logging.getLogger("speech_app")
logger.setLevel(logging.INFO)
# Remove all handlers associated with the root logger object (prevents duplicate output)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
# Add only file handler
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.handlers = [file_handler]

# DO NOT globally redirect sys.stdout/sys.stderr here.
# The rich UI and other libraries require a real terminal for rendering.
# If you need to capture stray output, use a context manager or patch only in subprocesses or background threads.

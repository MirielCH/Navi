# logs.py
"""Contains the logger"""

import logging
import logging.handlers
import os

from resources import settings


settings.LOG_FILE = os.path.join(settings.BOT_DIR, 'logs/discord.log')
if not os.path.isfile(settings.LOG_FILE):
    open(settings.LOG_FILE, 'a').close()


logger = logging.getLogger('discord')
if settings.DEBUG_MODE:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(filename=settings.LOG_FILE,when='D',interval=1, encoding='utf-8', utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
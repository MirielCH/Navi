# logs.py
"""Contains the logger"""

import logging
import logging.handlers
import os
import sys

from resources import settings


settings.LOG_FILE = os.path.join(settings.BOT_DIR, 'logs/discord.log')
if not os.path.isfile(settings.LOG_FILE):
    open(settings.LOG_FILE, 'a').close()

def get_logger(name: str) -> logging.Logger:
    new_logger = logging.getLogger(name)
    new_logger.setLevel(logging.INFO)
    handler = logging.handlers.TimedRotatingFileHandler(filename=settings.LOG_FILE,when='D',interval=1, encoding='utf-8', utc=True)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    new_logger.addHandler(handler)
    if "--log-to-stdout" in sys.argv:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        new_logger.addHandler(stream_handler)
    return new_logger

logger = get_logger('discord')
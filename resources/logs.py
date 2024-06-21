# logs.py
"""Contains the logger"""

import logging
import logging.handlers
import os
import sys

from resources import settings


if not os.path.isfile(settings.LOG_FILE):
    open(settings.LOG_FILE, 'a').close()

logger: logging.Logger = logging.getLogger('Navi')
logger.setLevel(logging.INFO)
handler: logging.Handler = logging.handlers.TimedRotatingFileHandler(filename=settings.LOG_FILE,when='D',interval=1, encoding='utf-8', utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
if "--log-to-stdout" in sys.argv:
    stream_handler: logging.Handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(stream_handler)
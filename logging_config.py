import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "bot.log")

# Rotate at 5MB, keeping 5 old files (bot.log.1 ... bot.log.5) - transcripts
# get logged at INFO level for debugging (see setup_logging), so this caps
# how much disk space that can consume over time.
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def setup_logging():
    """
    Configure the root logger with both a rotating file handler and a
    console handler, so terminal output during development keeps working
    exactly as before, while everything also persists to logs/bot.log for
    debugging after the fact - real issues on this project (network
    failures, the Arabic cleanup fabrication bug) have all been diagnosed
    by reading exactly this kind of output.
    """

    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # httpx (used internally by python-telegram-bot) logs every single HTTP
    # request at INFO level, which would drown out our own logs given how
    # often the bot polls Telegram - keep those quiet unless something's
    # actually wrong.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

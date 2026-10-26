import logging
import os
import time

logger = logging.getLogger(__name__)


def cleanup_stale_files(directory: str = "downloads", max_age_seconds: int = 3 * 3600) -> int:
    """
    Deletes regular files in the bot's own temp folder that are older than
    `max_age_seconds`. Normal processing deletes its files itself; this only
    catches what a crash or restart left behind. Never touches
    subdirectories or symlinks. Returns how many files were removed.
    """

    if not os.path.isdir(directory):
        return 0

    cutoff = time.time() - max_age_seconds
    removed = 0

    for entry in os.scandir(directory):
        try:
            if entry.is_file(follow_symlinks=False) and entry.stat().st_mtime < cutoff:
                os.remove(entry.path)
                removed += 1
        except OSError:
            logger.warning(f"Could not remove stale file: {entry.path}")

    if removed:
        logger.info(f"Removed {removed} stale file(s) from {directory}/")
    return removed

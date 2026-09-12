import asyncio
import logging
import random
import time

from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut

logger = logging.getLogger(__name__)

DEFAULT_MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 1.0

# Substrings that mean a download failed for a PERMANENT reason (private/
# deleted video, no audio track, file too large) rather than a transient
# network hiccup - retrying these wastes time since they fail identically
# every attempt. Mirrors the error classification already used in
# link_handler.py's except block, so the two stay in agreement about what
# counts as "worth trying again".
PERMANENT_FAILURE_MARKERS = (
    "no video could be found",
    "does not contain an audio track",
    "private",
    "unavailable",
    "not available",
    "removed",
    "too large",
    "entity too large",
)


def _is_permanent_failure(error: Exception) -> bool:
    return any(marker in str(error).lower() for marker in PERMANENT_FAILURE_MARKERS)


async def call_with_retry(func, *args, max_attempts: int = DEFAULT_MAX_ATTEMPTS, **kwargs):
    """
    Call a python-telegram-bot API method (message.reply_text,
    message.reply_audio, message.reply_document, ...) with retry-and-backoff
    for transient network failures.

    python-telegram-bot retries its OWN get_updates long-polling loop
    indefinitely by default (telegram.ext._updater, network_retry_loop) -
    but it does NOT retry any outbound Bot API call. HTTPXRequest.do_request
    catches a raw httpx transport error (httpx.ReadError, httpx.ConnectError,
    a read timeout, ...) and immediately re-raises it as
    telegram.error.NetworkError/TimedOut with no retry of its own. That gap
    is exactly what has produced the recurring httpx.ReadError/NetworkError
    crashes around reply_audio/reply_text in this project - this helper
    closes it for outbound calls.

    Note: telegram.error.BadRequest is (surprisingly) a NetworkError
    subclass, but it represents a permanent problem - bad file id, message
    too long, chat not found - that will fail identically on every retry,
    so it's excluded explicitly rather than being caught by a broad
    `except NetworkError`.
    """

    attempt = 0
    while True:
        attempt += 1
        try:
            return await func(*args, **kwargs)
        except RetryAfter as error:
            # Telegram's own flood-control signal - it tells us exactly how
            # long to wait, so honor that instead of our own backoff curve.
            if attempt >= max_attempts:
                raise
            logger.warning(
                f"Rate-limited by Telegram - waiting {error.retry_after}s "
                f"(attempt {attempt}/{max_attempts})"
            )
            await asyncio.sleep(error.retry_after)
        except BadRequest:
            raise
        except (TimedOut, NetworkError) as error:
            if attempt >= max_attempts:
                logger.error(f"Giving up after {attempt} attempts: {type(error).__name__}: {error}")
                raise
            delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            logger.warning(
                f"Transient network error ({type(error).__name__}: {error}) - "
                f"retrying in {delay:.1f}s (attempt {attempt}/{max_attempts})"
            )
            await asyncio.sleep(delay)


def call_sync_with_retry(func, *args, max_attempts: int = DEFAULT_MAX_ATTEMPTS, **kwargs):
    """
    Retry a blocking download call (yt-dlp) on transient failures, without
    retrying permanent ones (private/deleted video, no audio track, file
    too large) that would fail identically every time.

    This runs synchronously and sleeps with time.sleep, not asyncio.sleep -
    call it from INSIDE an asyncio.to_thread(...) wrapper (not the other way
    around), so the retry loop and its backoff sleeps happen off the event
    loop, same as the download call itself.

    This is a coarse, whole-attempt safety net layered on top of yt-dlp's
    own per-request retries (see youtube_service.py etc. for why those
    needed to be set explicitly) - it catches failures that persist across
    an entire extract_info/download attempt, e.g. a DNS blip or connection
    reset that outlasts yt-dlp's own retry budget.
    """

    attempt = 0
    while True:
        attempt += 1
        try:
            return func(*args, **kwargs)
        except Exception as error:
            if _is_permanent_failure(error):
                raise
            if attempt >= max_attempts:
                logger.error(f"Giving up after {attempt} attempts: {type(error).__name__}: {error}")
                raise
            delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            logger.warning(
                f"Transient download error ({type(error).__name__}: {error}) - "
                f"retrying in {delay:.1f}s (attempt {attempt}/{max_attempts})"
            )
            time.sleep(delay)

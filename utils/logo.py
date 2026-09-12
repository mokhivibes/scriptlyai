import logging

from config import LOGO_PATH
from utils.network_retry import call_with_retry

logger = logging.getLogger(__name__)

# Cached across the whole bot process, not per-user - a Telegram file_id is
# a permanent reference to a file already on Telegram's servers, valid for
# any chat, not just the one that first uploaded it. Without this cache,
# the 1.3MB logo would be re-uploaded in full on every single /start call
# from every user, forever.
_logo_file_id = None
_logo_bytes = None


async def send_logo(send_func, caption=None, parse_mode=None, reply_markup=None):
    """
    Send the bot's logo via `send_func` (a bound .reply_photo method, e.g.
    update.message.reply_photo or query.message.reply_photo), with
    `caption` as the photo's caption - one message, not a photo followed by
    a separate text message.

    First call of the process reads the file from disk (once - cached as
    bytes, not just the path, so a retry-on-failure doesn't hit a
    partially-consumed file cursor the way passing an open file handle to
    call_with_retry would) and uploads it, then caches the file_id Telegram
    returns. Every call after that sends by file_id, which Telegram treats
    as instant - no re-upload.
    """

    global _logo_file_id, _logo_bytes

    if _logo_file_id:
        return await call_with_retry(
            send_func, photo=_logo_file_id, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup
        )

    if _logo_bytes is None:
        with open(LOGO_PATH, "rb") as logo_file:
            _logo_bytes = logo_file.read()

    message = await call_with_retry(
        send_func, photo=_logo_bytes, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup
    )
    _logo_file_id = message.photo[-1].file_id
    logger.info(f"Logo uploaded and cached as file_id={_logo_file_id}")
    return message

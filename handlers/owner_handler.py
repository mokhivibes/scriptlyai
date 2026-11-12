import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import OWNER_USER_ID
from services.cookie_service import MAX_COOKIE_FILE_BYTES, install_cookies
from utils.network_retry import call_with_retry

logger = logging.getLogger(__name__)


async def handle_cookie_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    The owner sends a fresh YouTube cookies.txt to the bot (a .txt document):
    it is checked, tried against YouTube and installed with no server login.
    The message is deleted afterwards - the file holds a login.
    Registered for the owner only; anyone else's .txt goes to the normal
    "send a link or a media file" reply.
    """

    message = update.message
    if not message or not message.document or update.effective_user.id != OWNER_USER_ID:
        return

    document = message.document
    if document.file_size and document.file_size > MAX_COOKIE_FILE_BYTES:
        await call_with_retry(message.reply_text, "That file is too big to be a cookies file.")
        return

    status = await call_with_retry(message.reply_text, "🍪 Checking the cookie file with YouTube…")
    try:
        telegram_file = await call_with_retry(context.bot.get_file, document.file_id)
        data = await call_with_retry(telegram_file.download_as_bytearray)
        ok, report = await asyncio.to_thread(install_cookies, bytes(data).decode("utf-8", errors="replace"))
        await call_with_retry(status.edit_text, ("✅ " if ok else "❌ ") + report)
    except Exception:
        logger.exception("Cookie upload failed")
        await call_with_retry(status.edit_text, "❌ Something went wrong while installing the file. The old one is still in use.")
    finally:
        try:
            await message.delete()
        except Exception:
            logger.warning("Could not delete the cookie file message")

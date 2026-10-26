import asyncio
import logging
import os
import time
import uuid
from urllib.parse import quote_plus

from telegram import CopyTextButton, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.link_detector import extract_url, detect_platform
from utils.text_chunker import split_into_chunks
from utils.rich_text import CODE, QUOTE_BOLD, build_bold_message, simple_markdown_parts
from utils import messages as msg
from services.youtube_service import download_youtube_video
from services.twitter_service import download_twitter_video
from services.tiktok_service import download_tiktok_video
from services.facebook_service import download_facebook_video
from services.audio_service import extract_audio
from services.ai_cleanup_service import clean_transcript
from services.export_service import export_to_pdf, export_to_text
from services.translation_service import translate_text
from services.summary_service import summarize_transcript
from database import (
    add_transcript,
    get_transcript_by_id,
    get_interface_language,
    get_uzbek_alphabet,
    set_uzbek_alphabet,
    get_daily_usage_count,
    increment_daily_usage,
    decrement_daily_usage,
    get_total_usage_today,
    has_sent_capacity_alert_today,
    get_counters,
    owner_alert_already_sent,
    mark_owner_alert_sent,
    next_quota_reset,
    mark_capacity_alert_sent,
)
from utils.network_retry import call_with_retry, call_sync_with_retry
from utils.stickers import STICKER_PROCESSING, STICKER_DONE, STICKER_ERROR
from handlers.command_handler import help_command, history_command, language_command
from utils.uzbek_script import render_uzbek, pipeline_alphabet, user_alphabet
from config import OWNER_USER_ID, BOT_USERNAME, YOUTUBE_COOKIES_PATH, YT_DLP_JS_RUNTIMES

logger = logging.getLogger(__name__)


# Telegram hard-rejects any single message over 4096 characters. Stay
# comfortably under that so a long transcript doesn't crash with "Message
# is too long".
TELEGRAM_MESSAGE_MAX_CHARS = 4000

EXPORT_DIR = "downloads"

LYRICS_SEARCH_MAX_CHARS = 80

# Signature under everything sent: a blank line, then the handle bold in a quote block.
BRAND_FOOTER_PARTS = [("\n\n", False), (BOT_USERNAME, QUOTE_BOLD)]

# Telegram's standard Bot API refuses getFile for anything bigger than
# this; going higher needs a self-hosted local Bot API server.
TELEGRAM_BOT_DOWNLOAD_LIMIT_BYTES = 20 * 1024 * 1024

# Above this, show a confirm/cancel warning before committing to the full
# pipeline instead of silently making someone wait - a full song can take
# 5+ minutes to transcribe, and results are less reliable for music/singing
# than speech (see README Known Limitations). Chosen to comfortably clear
# typical short-form clips (YouTube Shorts, TikTok, Reels) while catching
# most full songs and longer spoken content.
LONG_CONTENT_THRESHOLD_SECONDS = 90

# Every full pipeline run costs at least 2 Groq calls (Whisper transcribe +
# gpt-oss-120b cleanup, sometimes +1 more for a Summarize tap) against a
# free-tier quota that's shared across every user of this bot, not
# per-user (~1,000 chat completions/day, ~2,000 transcriptions/day as of
# 2026-09-24 - see console.groq.com/docs/rate-limits). Without a per-user
# cap, one heavy user could exhaust the whole shared daily quota and lock
# out everyone else. 15/day comfortably covers normal use while keeping
# that from happening; raise this (or drop it entirely) once billing is
# on a paid tier without daily caps.
PER_USER_DAILY_LIMIT = 15

# Realistic safe capacity on Groq's shared free tier is ~500 full pipeline
# runs/day (bottlenecked by gpt-oss-120b's 1,000 RPD / 2 calls per run -
# see PER_USER_DAILY_LIMIT's comment). 350 (70%) gives the owner real lead
# time to upgrade to a paid tier before actually hitting the wall, instead
# of finding out from a wave of ERROR_RATE_LIMITED reports. Checked once
# per pipeline run in _process_link; see database.py's capacity_alerts
# table for why this only fires once per day rather than on every request
# past the threshold.
GROQ_CAPACITY_WARNING_THRESHOLD = 350

# Turned off 2026-09-25 - both of translation's free backends (Google's
# unofficial endpoint, MyMemory) share one per-IP rate-limit budget with
# no real SLA, and a single day of real testing exhausted it for over an
# hour straight. Rather than exposing a feature that can silently fail for
# real users, hiding it until there's either real demand to justify a paid
# API (Google Cloud Translation - the only option that both supports
# Uzbek and has an actual SLA, ~$20/million characters after a 500k/month
# free tier) or the decision is revisited. The underlying implementation
# (translation_service.py, the Translate button/handlers below) is left
# fully intact - flip this back to True to bring it back with no other
# changes needed.
TRANSLATION_ENABLED = False


def _lang(user_id) -> str:
    return get_interface_language(user_id) or msg.DEFAULT_LANGUAGE


# --- "Get text" on demand ---
#
# For a pasted LINK the bot downloads and sends the audio first, with a
# "Get text" button, and only transcribes when the user taps it (saves the
# free Groq/Gemini quota - e.g. for people who just wanted a song's mp3).
# The extracted audio waits on disk for up to an hour, tracked here in
# memory (a restart forgets it - the tap then asks for the link again).
PENDING_TEXT_TTL_SECONDS = 3600


def _pending_registry(context) -> dict:
    return context.application.bot_data.setdefault("pending_text", {})


def _remove_file(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            logger.warning(f"Failed to remove temp file: {path}")


def _purge_expired_pending(context):
    now = time.time()
    registry = _pending_registry(context)
    for token, info in list(registry.items()):
        if now - info["created"] > PENDING_TEXT_TTL_SECONDS:
            registry.pop(token, None)
            _remove_file(info.get("audio_path"))


def _alphabet_for(user_id) -> str:
    """This user's chosen Uzbek alphabet ('new'/'old'), default if never chosen."""
    return user_alphabet(get_uzbek_alphabet(user_id))


def _alphabet_button_state(lang, media_language, user_id):
    """The user's current alphabet if the toggle button belongs on this
    result - any user (whatever their interface language) looking at Uzbek
    text - else None. `lang` is unused but kept so call sites read the same."""
    if media_language == "uz":
        return _alphabet_for(user_id)
    return None


def _get_duration_seconds(url):
    """
    Best-effort, download-free duration lookup via yt-dlp metadata only
    (skip_download=True - no video/audio bytes fetched). Deliberately not
    wrapped in call_sync_with_retry: this is an optional nicety gating a
    UX warning, not a required step - if it fails or times out for any
    reason, returning None just skips the warning and lets the real
    download attempt (which DOES have full retry/error handling) proceed
    and surface whatever actual problem exists.
    """
    import yt_dlp

    options = {"quiet": True, "no_warnings": True, "skip_download": True, "socket_timeout": 15}
    if "youtube.com" in url or "youtu.be" in url:
        if os.path.exists(YOUTUBE_COOKIES_PATH):
            options["cookiefile"] = YOUTUBE_COOKIES_PATH
        if YT_DLP_JS_RUNTIMES:
            options["js_runtimes"] = YT_DLP_JS_RUNTIMES
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        return info.get("duration")
    except Exception as error:
        logger.warning(f"Duration lookup failed (non-fatal, proceeding without warning): {error}")
        return None


def build_long_content_confirm_keyboard(lang):
    keyboard = [[
        InlineKeyboardButton(msg.t(lang, "CONFIRM_YES_BUTTON"), callback_data="confirm_process"),
        InlineKeyboardButton(msg.t(lang, "CONFIRM_NO_BUTTON"), callback_data="cancel_process"),
    ]]
    return InlineKeyboardMarkup(keyboard)


async def _delete_silently(message):
    """
    Best-effort cleanup of a now-superseded message (a progress sticker or
    status line that no longer serves a purpose once the real result is
    ready) - never lets a delete failure (already deleted, too old, etc.)
    break the flow it's cleaning up after, so this is a plain try/except
    rather than routed through call_with_retry (which re-raises after
    exhausting retries).
    """

    try:
        await message.delete()
    except Exception:
        logger.warning(f"Failed to delete message {getattr(message, 'message_id', '?')} - leaving it in place")


async def send_result_text(message, header_parts, content: str):
    """
    Sends a transcript/translation/summary as plain text (selectable, not
    monospaced), in one or more messages split at paragraph/sentence
    boundaries so it stays under Telegram's per-message limit. header_parts
    is prepended to the first chunk only, in the same message.

    Entity-based, not parse_mode="Markdown": content is unpredictable (raw
    transcript/AI output) and could contain Markdown syntax characters.
    The copy button (see build_export_keyboard) handles one-tap copying.
    """

    chunks, _ = split_into_chunks(content, max_chars=TELEGRAM_MESSAGE_MAX_CHARS)
    if not chunks:
        chunks = [""]

    for index, chunk in enumerate(chunks):
        parts = []
        if index == 0:
            parts += list(header_parts) + [("\n\n", False)]
        parts.append((chunk, False))
        if index == len(chunks) - 1:
            parts += BRAND_FOOTER_PARTS

        chunk_text, chunk_entities = build_bold_message(parts)
        await call_with_retry(message.reply_text, chunk_text, entities=chunk_entities)


def _caption_kwargs(caption_markdown: str):
    """caption + caption_entities for a developer-written caption (*bold*
    markers) with the bot signature appended."""
    text, entities = build_bold_message(simple_markdown_parts(caption_markdown) + BRAND_FOOTER_PARTS)
    return {"caption": text, "caption_entities": entities}


# Telegram's native copy-to-clipboard button only accepts 1-256 characters.
COPY_BUTTON_MAX_CHARS = 256


def _copy_button(lang, copy_text):
    """One-tap native copy for short text; longer text falls back to a
    callback that re-sends it as tap-to-copy monospace messages."""
    label = msg.t(lang, "COPY_BUTTON")
    if copy_text and len(copy_text) <= COPY_BUTTON_MAX_CHARS:
        return InlineKeyboardButton(label, copy_text=CopyTextButton(text=copy_text))
    return InlineKeyboardButton(label, callback_data="copy_text")


def _alphabet_row(lang, alphabet):
    """One button naming the alphabet a tap switches TO."""
    key = "ALPHABET_TO_OLD_BUTTON" if alphabet == "new" else "ALPHABET_TO_NEW_BUTTON"
    return [InlineKeyboardButton(msg.t(lang, key), callback_data="toggle_alphabet")]


def build_export_keyboard(lang, copy_text=None, alphabet=None):
    keyboard = [[
        InlineKeyboardButton(msg.t(lang, "EXPORT_PDF_BUTTON"), callback_data="export_pdf"),
        InlineKeyboardButton(msg.t(lang, "EXPORT_TXT_BUTTON"), callback_data="export_txt"),
        _copy_button(lang, copy_text),
    ]]

    # Second row - Translate + Summarize side by side while translation is
    # enabled, Summarize alone (matching build_summarize_retry_keyboard's
    # single-button-row pattern) while it's off - see TRANSLATION_ENABLED.
    if TRANSLATION_ENABLED:
        keyboard.append([
            InlineKeyboardButton(msg.t(lang, "TRANSLATE_BUTTON"), callback_data="translate_menu"),
            InlineKeyboardButton(msg.t(lang, "SUMMARIZE_BUTTON"), callback_data="summarize"),
        ])
    else:
        keyboard.append([InlineKeyboardButton(msg.t(lang, "SUMMARIZE_BUTTON"), callback_data="summarize")])

    if alphabet:
        keyboard.append(_alphabet_row(lang, alphabet))

    return InlineKeyboardMarkup(keyboard)


def build_save_keyboard(lang, copy_text=None, alphabet=None):
    """
    A smaller export-only keyboard (no Translate/Summary) shown after a
    translation or summary - Translate/Summary always operate on the
    ORIGINAL transcript (context.user_data["last_transcript"], never
    overwritten), so offering them again here would either be a no-op
    repeat or, worse, imply "translate this translation" / "summarize
    this summary", neither of which this bot is set up to do sensibly.
    Saving what's currently on screen, on the other hand, always makes
    sense - see _handle_export's comment on export_text/export_language.
    """

    keyboard = [
        [
            InlineKeyboardButton(msg.t(lang, "EXPORT_PDF_BUTTON"), callback_data="export_pdf"),
            InlineKeyboardButton(msg.t(lang, "EXPORT_TXT_BUTTON"), callback_data="export_txt"),
            _copy_button(lang, copy_text),
        ],
    ]
    if alphabet:
        keyboard.append(_alphabet_row(lang, alphabet))
    return InlineKeyboardMarkup(keyboard)


def build_summarize_retry_keyboard(lang):
    """
    A single-button keyboard attached to SUMMARY_FAILED so the retry it
    promises ("tap the button below") is an actual tap target, not just
    text - mirrors the retry buttons attached to EXPORT_FAILED and
    TRANSLATION_FAILED. There's no shared "just the Summarize button"
    builder elsewhere since build_export_keyboard always pairs it with
    Translate, so this is its own small keyboard.
    """

    keyboard = [[InlineKeyboardButton(msg.t(lang, "SUMMARIZE_BUTTON"), callback_data="summarize")]]
    return InlineKeyboardMarkup(keyboard)


def build_translate_language_keyboard(lang, exclude_code=None):
    """
    Target-language picker for translation - deliberately separate from
    command_handler.py's build_language_picker_keyboard (that one sets the
    BOT's interface language and its buttons are labeled in each
    language's own name; this one picks a TRANSLATION target and its
    labels are in the user's current interface language, since they're
    choosing what to translate INTO, not which language to read the UI in).

    exclude_code drops the transcript's own detected language from the
    list - offering it would only lead to a dead-end "that's already the
    language this is in!" tap, so it's better left off the menu entirely
    rather than shown and then rejected.
    """

    # target_language_name() already includes the flag (TARGET_LANGUAGE_NAMES
    # in each locale) - no need to prepend msg.LANGUAGE_FLAGS separately here.
    codes = [code for code in msg.SUPPORTED_LANGUAGES if code != exclude_code]
    buttons = [
        InlineKeyboardButton(
            msg.target_language_name(lang, code),
            callback_data=f"translate_to_{code}"
        )
        for code in codes
    ]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(keyboard)


# Per-user busy guard. context.user_data is PTB's own per-user_id store, so
# concurrent handler invocations for the SAME user share this exact dict -
# safe to check-then-set synchronously here since there's no `await` between
# the two, so no other coroutine can interleave. This only matters once
# concurrent_updates is enabled (see main.py) - PTB's own concurrency limit
# is a flat global semaphore with no per-chat ordering guarantee, so without
# this guard, two rapid messages from the same user could run their handlers
# truly concurrently and corrupt each other's context.user_data.
def _is_busy(context) -> bool:
    return context.user_data.get("busy", False)


def _mark_busy(context):
    context.user_data["busy"] = True


def _mark_free(context):
    context.user_data["busy"] = False


async def _maybe_alert_owner_of_capacity(context):
    """
    Best-effort, once-a-day DM to OWNER_USER_ID (config.py) when total
    usage across every user crosses GROQ_CAPACITY_WARNING_THRESHOLD - see
    that constant's comment. No-ops silently if OWNER_USER_ID isn't
    configured, so this feature is entirely opt-in. Checked on every
    pipeline run (cheap - two indexed lookups), but only ever sends once
    per calendar day regardless of how far over the threshold usage goes,
    and never raises - a failed notification should never break the
    transcription request that triggered the check.
    """

    if not OWNER_USER_ID:
        return

    try:
        if has_sent_capacity_alert_today():
            return

        total_today = get_total_usage_today()
        if total_today < GROQ_CAPACITY_WARNING_THRESHOLD:
            return

        mark_capacity_alert_sent()
        await context.bot.send_message(
            chat_id=OWNER_USER_ID,
            text=(
                f"📈 ScriptlyAI has processed {total_today} requests today, past the "
                f"{GROQ_CAPACITY_WARNING_THRESHOLD}/day watch threshold - Groq's free tier caps out "
                "around ~500/day shared across all users. Might be time to consider a paid tier."
            ),
        )
    except Exception:
        logger.exception("Failed to send owner capacity alert - continuing")


def _reset_text() -> str:
    left, reset_local = next_quota_reset()
    hours, minutes = divmod(int(left.total_seconds()) // 60, 60)
    return f"Google's daily quotas reset at {reset_local:%H:%M} Tashkent time (in {hours}h {minutes}m)."


async def _maybe_alert_owner_of_gemini(context):
    """
    Best-effort DMs to OWNER_USER_ID about the Gemini free-tier quotas (see
    services/speech_service.py), each at most once per Google quota day:
      - the best model's 25/day is used up   -> later clips use flash (20/day)
      - flash's 20/day is used up too (45)   -> later clips use weaker flash-lite
      - flash-lite approaching its ~500/day cap
      - Gemini returning nothing repeatedly
    Never raises - a failed notification must not break the request.
    """

    if not OWNER_USER_ID:
        return

    try:
        counters = get_counters()
        lite_calls = counters.get("id_calls", 0) + counters.get("done:lite", 0)
        clips = counters.get("cluster", 0)

        alerts = []
        if counters.get("quota_hit:gemini-3.5-transcribe") and not owner_alert_already_sent("best_quota"):
            alerts.append(("best_quota",
                f"🔔 The best Gemini transcription quota (25/day) is used up. Uzbek/Kazakh/Kyrgyz clips now use "
                f"gemini-3.5-flash (20/day). Clips so far today: {clips}. {_reset_text()}"))
        if counters.get("quota_hit:gemini-3.5-flash") and not owner_alert_already_sent("flash_quota"):
            alerts.append(("flash_quota",
                f"⚠️ All ~45 higher-quality Gemini transcriptions for today are used. From now on Uzbek/Kazakh/Kyrgyz "
                f"clips use the weaker gemini-3.5-flash-lite until the reset. Clips so far today: {clips}. {_reset_text()} "
                "If this happens most days, consider turning on Google billing (about $0.003 per minute)."))
        if lite_calls >= 400 and not owner_alert_already_sent("lite_high"):
            alerts.append(("lite_high",
                f"⚠️ gemini-3.5-flash-lite is at about {lite_calls} of its ~500 free calls today. {_reset_text()}"))
        if counters.get("gemini_failed", 0) >= 3 and not owner_alert_already_sent("gemini_failed"):
            alerts.append(("gemini_failed",
                f"⚠️ Gemini returned no transcript {counters['gemini_failed']} times today - those clips fell back "
                "to the slower/weaker path. Check the server log."))

        for kind, text in alerts:
            mark_owner_alert_sent(kind)
            await context.bot.send_message(chat_id=OWNER_USER_ID, text=text)
    except Exception:
        logger.exception("Failed to send owner Gemini alert - continuing")


# Persistent-reply-keyboard shortcut labels ("❓ Help" etc.) aren't real
# Telegram commands - Telegram only auto-routes a literal "/command", so a
# tap on one of these arrives here as a plain text message, same as any
# link. Route it to the matching command handler and bypass the rest of
# handle_link entirely, same as typing /help would (real slash-commands are
# registered as separate CommandHandlers in main.py, matched via
# ~filters.COMMAND before this handler ever runs, so they already skip the
# busy-guard below - this dict keeps shortcut taps behaving identically,
# checked BEFORE the busy-guard for the same reason).
_SHORTCUT_HANDLERS = {
    "help": help_command,
    "history": history_command,
    "language": language_command,
}


async def handle_unsupported_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Catches a photo, voice note, video file, document, or sticker sent
    directly - previously these had no handler registered at all (only
    filters.TEXT reached handle_link), so a user who attached a video or
    voice note instead of pasting a link got complete silence. A
    transcription bot's users trying to hand it media directly is a very
    natural mistake to make, so this replies rather than staying quiet.
    Not busy-guarded - this is a fixed, immediate reply that doesn't
    touch any pipeline state, unlike handle_link's link-processing path.
    """

    if not update.message:
        return

    lang = _lang(update.effective_user.id)
    text, entities = msg.unsupported_message_text(lang)
    await call_with_retry(update.message.reply_text, text, entities=entities)


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    shortcut = msg.match_shortcut(update.message.text)
    if shortcut:
        await _SHORTCUT_HANDLERS[shortcut](update, context)
        return

    lang = _lang(update.effective_user.id)

    if _is_busy(context):
        await call_with_retry(update.message.reply_text, msg.t(lang, "STILL_WORKING"), parse_mode="Markdown")
        return

    text = update.message.text
    url = extract_url(text)

    if not url:
        query = text.strip()
        # A short non-link message is most likely a song name: offer a web
        # search link (never the lyrics themselves - copyrighted, and no
        # free licensed source exists). Longer text just gets the usual hint.
        looks_like_song_name = 0 < len(query) <= LYRICS_SEARCH_MAX_CHARS
        no_link_text, no_link_entities = msg.no_link_found_text(lang, with_lyrics_hint=looks_like_song_name)
        reply_markup = None
        if looks_like_song_name:
            search_url = "https://www.google.com/search?q=" + quote_plus(f"{query} lyrics")
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(msg.t(lang, "LYRICS_BUTTON"), url=search_url)]])
        await call_with_retry(
            update.message.reply_text, no_link_text, entities=no_link_entities, reply_markup=reply_markup
        )
        return

    platform = detect_platform(url)
    logger.info(f"Link received: platform={platform} user={update.effective_user.id}")

    if platform in ("youtube", "instagram", "twitter", "tiktok", "facebook"):
        # Marked busy synchronously, BEFORE the duration lookup below awaits
        # anything - the lookup is a real await point, and leaving busy
        # unset until after it would reopen exactly the race the busy-guard
        # exists to prevent (two rapid links from the same user both
        # passing the "not busy" check above before either's lookup
        # resolves). Busy stays True through the long-content warning too,
        # if that path is taken - not just during active processing -
        # since a pending confirm/cancel tap is still "something in flight"
        # that a second incoming link shouldn't be able to interleave with.
        _mark_busy(context)

        platform_name = {
            "youtube": "YouTube",
            "instagram": "Instagram",
            "twitter": "X/Twitter",
            "tiktok": "TikTok",
            "facebook": "Facebook",
        }[platform]

        # Instant acknowledgement - the duration lookup below can take
        # several seconds (or stall on a bad connection), and silence
        # makes users think the bot is dead.
        ack_message = None
        try:
            ack_message = await call_with_retry(update.message.reply_text, msg.t(lang, "LINK_RECEIVED"), parse_mode="Markdown")
        except Exception:
            logger.warning("Could not send the link-received acknowledgement (continuing)")

        try:
            try:
                duration = await asyncio.wait_for(asyncio.to_thread(_get_duration_seconds, url), timeout=30)
            except asyncio.TimeoutError:
                logger.warning("Duration lookup timed out (non-fatal, proceeding without warning)")
                duration = None

            if ack_message:
                await _delete_silently(ack_message)

            if duration and duration > LONG_CONTENT_THRESHOLD_SECONDS:
                context.user_data["pending_url"] = url
                context.user_data["pending_platform"] = platform
                context.user_data["pending_platform_name"] = platform_name

                # busy is deliberately left True here (not released in a
                # finally below) - a pending confirm/cancel tap is still
                # "something in flight" for this user, released either by
                # _handle_confirm_long_content/_handle_cancel_long_content
                # or by _process_link's own finally once that runs.
                await call_with_retry(
                    update.message.reply_text,
                    msg.long_content_warning(lang, duration / 60),
                    parse_mode="Markdown",
                    reply_markup=build_long_content_confirm_keyboard(lang)
                )
                return

        except Exception:
            # Anything here (duration lookup, or the warning message itself
            # failing after exhausting retries - e.g. a transient network
            # blip) previously left `busy` stuck True forever, since this
            # whole section had no cleanup path of its own - only the
            # actual processing pipeline below did. That silently locked
            # the user out of ever sending another link until a manual bot
            # restart, with no error shown to them at all.
            logger.exception(f"Failed before processing could start for platform={platform}")
            _mark_free(context)
            await call_with_retry(update.message.reply_text, msg.t(lang, "ERROR_GENERIC"), parse_mode="Markdown")
            return

        await _process_link(update.message, context, url, platform, platform_name, lang, update.effective_user.id)

    else:
        unrecognized_text, unrecognized_entities = msg.unrecognized_link_text(lang)
        await call_with_retry(update.message.reply_text, unrecognized_text, entities=unrecognized_entities)


async def handle_media_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    A voice note, audio file, video, video note, or audio/video document
    sent straight to the bot - fed into the same _process_link pipeline as
    a pasted link, just with Telegram as the "download" source.
    """

    message = update.message
    if not message:
        return

    lang = _lang(update.effective_user.id)

    if _is_busy(context):
        await call_with_retry(message.reply_text, msg.t(lang, "STILL_WORKING"), parse_mode="Markdown")
        return

    attachment = message.voice or message.audio or message.video or message.video_note or message.document

    if attachment.file_size and attachment.file_size > TELEGRAM_BOT_DOWNLOAD_LIMIT_BYTES:
        await call_with_retry(message.reply_text, msg.t(lang, "FILE_TOO_BIG_TO_DOWNLOAD"), parse_mode="Markdown")
        return

    _mark_busy(context)

    upload = {"file_id": attachment.file_id, "title": getattr(attachment, "file_name", None)}
    await _process_link(message, context, None, "upload", "File", lang, update.effective_user.id, upload=upload)


async def _process_link(message, context, url, platform, platform_name, lang, user_id, upload=None, resume=None):
    """
    Runs the actual download -> extract -> transcribe -> clean -> export
    pipeline. Called either immediately (short content) or from the
    confirm/cancel callback (long content, after the user taps "go ahead").
    `message` is whichever object has .reply_text/.reply_audio available -
    update.message for the immediate path, query.message for the
    confirmed-after-warning path.
    """

    # Checked here (not earlier in handle_link) so BOTH entry points - the
    # immediate short-content path and the confirm/cancel callback for
    # long content - go through one place. By the time _process_link runs,
    # the CALLER has already set busy=True (see handle_link and
    # _handle_confirm_long_content) - _mark_free here on the rejected path
    # is required, not optional, or the user would stay stuck "busy"
    # forever with nothing actually running. See PER_USER_DAILY_LIMIT's
    # comment for why this cap exists at all.
    # `resume` = the user tapped "Get text" on audio sent earlier; `ask_first`
    # = a pasted link, where we send the audio and wait for that tap instead
    # of transcribing straight away. Only actual transcription counts toward
    # the daily limit.
    ask_first = upload is None and resume is None

    if not ask_first:
        if get_daily_usage_count(user_id) >= PER_USER_DAILY_LIMIT:
            _mark_free(context)
            if resume:
                _remove_file(resume["audio_path"])
            await call_with_retry(message.reply_text, msg.t(lang, "DAILY_LIMIT_REACHED"), parse_mode="Markdown")
            return

        increment_daily_usage(user_id)
        await _maybe_alert_owner_of_capacity(context)

    _mark_busy(context)

    # Populated as the pipeline progresses, so the finally block below can
    # clean up whichever of these actually got created before an error (or
    # successful completion) - without this, every downloaded video and
    # every extracted audio file accumulates in downloads/ forever, since
    # nothing else ever removes them.
    video_path = None
    audio_path = None
    keep_audio = False  # True when the audio must outlive this call (waiting for "Get text")

    # Captured (not discarded) so it can be deleted once STICKER_DONE takes
    # over its role - see the success path below for why.
    processing_sticker_message = await call_with_retry(message.reply_sticker, STICKER_PROCESSING)

    # One status message, edited in place through each processing step,
    # instead of sending a new message per step - keeps the chat from
    # filling up with transient "still working on it" messages.
    # downloading_message returns (text, entities) - see its docstring
    # for why (branded platform icon via custom emoji entity).
    if resume:
        status_message = await call_with_retry(
            message.reply_text, msg.transcribing_message(lang), parse_mode="Markdown"
        )
    elif upload:
        status_message = await call_with_retry(
            message.reply_text, msg.t(lang, "DOWNLOADING_FILE"), parse_mode="Markdown"
        )
    else:
        downloading_text, downloading_entities = msg.downloading_message(lang, platform, platform_name)
        status_message = await call_with_retry(
            message.reply_text, downloading_text, entities=downloading_entities
        )

    try:
        # download_*/extract_audio/transcribe_audio/clean_transcript are
        # all synchronous, blocking calls (subprocess, CPU-bound inference,
        # blocking HTTP). Run them in a thread so they don't freeze the
        # whole event loop - otherwise concurrent_updates would be
        # meaningless, since one user's multi-minute transcription would
        # still block every other user's updates from being dispatched at
        # all. call_sync_with_retry adds a coarse retry-with-backoff around
        # the whole download attempt, on top of yt-dlp's own now-explicit
        # per-request retries (see youtube_service.py) - see
        # utils/network_retry.py for why both layers exist and how
        # permanent failures (private/deleted video) are told apart from
        # transient ones.
        if resume:
            audio_path = resume["audio_path"]
            video_title = resume["title"]

        elif upload:
            # ".upload" (not the real extension) so extract_audio's output
            # <name>.mp3 can never collide with the source when a user
            # sends an .mp3 - ffmpeg detects the format from content anyway.
            video_path = os.path.join(EXPORT_DIR, f"upload_{uuid.uuid4().hex}.upload")
            telegram_file = await call_with_retry(context.bot.get_file, upload["file_id"])
            await call_with_retry(telegram_file.download_to_drive, video_path)
            video_title = upload["title"]

        elif platform == "youtube":
            video_path, video_title = await asyncio.to_thread(
                call_sync_with_retry, download_youtube_video, url
            )

        elif platform == "twitter":
            video_path, video_title = await asyncio.to_thread(
                call_sync_with_retry, download_twitter_video, url
            )

        elif platform == "tiktok":
            video_path, video_title = await asyncio.to_thread(
                call_sync_with_retry, download_tiktok_video, url
            )

        elif platform == "facebook":
            video_path, video_title = await asyncio.to_thread(
                call_sync_with_retry, download_facebook_video, url
            )

        elif platform == "instagram":
            def _download_instagram():
                import yt_dlp

                options = {
                    "format": "best",
                    # Use the post's title/caption so the file is
                    # recognizable later (falls back to the post id if
                    # unavailable); the .100s cap keeps long Instagram
                    # captions from producing unwieldy filenames.
                    "outtmpl": "downloads/%(title,id).100s.%(ext)s",
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    # See youtube_service.py's identical option - yt-dlp's
                    # Python API does not apply its CLI default of 10
                    # retries unless set explicitly.
                    "retries": 5,
                    "fragment_retries": 5,
                }

                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info), info.get("title")

            video_path, video_title = await asyncio.to_thread(call_sync_with_retry, _download_instagram)

        if not resume:
            logger.info(f"Video downloaded: {video_path}")

            await call_with_retry(status_message.edit_text, msg.extracting_audio_message(lang), parse_mode="Markdown")

            audio_path = await asyncio.to_thread(extract_audio, video_path)

            logger.info(f"Audio extracted: {audio_path}")

        if not upload and not resume:
            token = uuid.uuid4().hex[:12]
            ask_markup = None
            if ask_first:
                ask_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton(msg.t(lang, "GET_TEXT_BUTTON"), callback_data=f"get_text_{token}")
                ]])

            with open(audio_path, "rb") as audio_file:
                await call_with_retry(
                    message.reply_audio,
                    audio=audio_file,
                    filename=os.path.basename(audio_path),
                    reply_markup=ask_markup,
                    **_caption_kwargs(msg.t(lang, "AUDIO_CAPTION_ASK" if ask_first else "AUDIO_CAPTION"))
                )

            if ask_first:
                _purge_expired_pending(context)
                _pending_registry(context)[token] = {
                    "audio_path": audio_path, "title": video_title, "url": url, "platform": platform,
                    "platform_name": platform_name, "user_id": user_id, "created": time.time(),
                }
                keep_audio = True
                logger.info(f"Audio sent, waiting for 'Get text' tap: token={token} user={user_id}")

                await _delete_silently(processing_sticker_message)
                await _delete_silently(status_message)
                return

        await call_with_retry(status_message.edit_text, msg.transcribing_message(lang), parse_mode="Markdown")

        from services.speech_service import transcribe_audio

        # Blind auto-detection has repeatedly misdetected real Uzbek audio
        # as a linguistically-related-but-wrong language (Kazakh, Turkish,
        # Persian all observed on real content) - see README Known
        # Limitations. Plain Groq auto-detect still runs first for every
        # language, same as before; transcribe_audio now transparently
        # retries with a local Uzbek-specific model when Groq's own result
        # lands in that known misdetection cluster (evidence from the
        # audio itself, not from the user's interface language - unlike
        # the earlier forced-uz attempt that was reverted for breaking on
        # genuinely non-Uzbek content). That fallback is real local CPU
        # work with no progress of its own to report, so the callback
        # below updates the status message to explain the extra wait
        # rather than leaving the user looking at "Transcribing..." with
        # no sign anything is happening. asyncio.run_coroutine_threadsafe
        # is required here (not a plain await) because transcribe_audio
        # itself runs in a worker thread via asyncio.to_thread below, and
        # the status message edit is a coroutine that must run back on the
        # main event loop.
        event_loop = asyncio.get_running_loop()

        def _on_uzbek_fallback_start():
            asyncio.run_coroutine_threadsafe(
                call_with_retry(
                    status_message.edit_text,
                    msg.t(lang, "TRANSCRIBING_UZBEK_FALLBACK"),
                    parse_mode="Markdown"
                ),
                event_loop
            )

        transcript, detected_language = await asyncio.to_thread(
            transcribe_audio, audio_path, on_uzbek_fallback_start=_on_uzbek_fallback_start
        )

        await _maybe_alert_owner_of_gemini(context)

        if not transcript.strip():
            decrement_daily_usage(user_id)
            raise ValueError("No speech detected in this audio.")

        logger.info(f"Detected language: {detected_language}")
        logger.info(f"Raw transcript: {transcript}")

        await call_with_retry(status_message.edit_text, msg.cleaning_message(lang), parse_mode="Markdown")

        cleaned_transcript = await asyncio.to_thread(clean_transcript, transcript)
        logger.info(f"Cleaned transcript: {cleaned_transcript}")

        # Cleanup ran on the standard Uzbek Latin; what the user sees (and
        # what's stored for /history, Copy and exports) uses the revised
        # alphabet - see utils/uzbek_script.py.
        if detected_language == "uz":
            cleaned_transcript = render_uzbek(cleaned_transcript, _alphabet_for(user_id))

        context.user_data["last_transcript"] = cleaned_transcript
        context.user_data["detected_language"] = detected_language
        # export_text/export_language track whatever's CURRENTLY on screen
        # (the original transcript, or a translation/summary of it) - see
        # build_save_keyboard()'s comment for why this is separate from
        # last_transcript/detected_language, which always stay the
        # original (Translate/Summary always operate on the source, never
        # on a translation-of-a-translation).
        context.user_data["export_text"] = cleaned_transcript
        context.user_data["export_language"] = detected_language

        add_transcript(
            user_id=user_id,
            platform=platform,
            detected_language=detected_language,
            title=video_title,
            transcript=cleaned_transcript
        )

        await call_with_retry(message.reply_sticker, STICKER_DONE)
        await send_result_text(message, msg.transcript_header_parts(lang), cleaned_transcript)

        await call_with_retry(
            message.reply_text,
            msg.t(lang, "NEXT_ACTIONS_PROMPT"),
            reply_markup=build_export_keyboard(
                lang, cleaned_transcript, alphabet=_alphabet_button_state(lang, detected_language, user_id)
            )
        )

        # The processing sticker and the "cleaning up..." status line have
        # both been superseded by the result just sent - delete them now
        # that everything landed, so the chat isn't left with stale
        # progress indicators. Deleted only at the very end (not earlier)
        # so the except block below still has a live status_message to
        # edit into an error if anything above it fails instead.
        await _delete_silently(processing_sticker_message)
        await _delete_silently(status_message)

    except Exception as error:
        error_name = type(error).__name__
        error_text = str(error).lower()

        logger.exception(f"Processing failed for platform={platform}: {error_name}: {error}")

        if "no speech detected" in error_text:
            error_reply_text = msg.t(lang, "ERROR_NO_SPEECH")
        elif "no video could be found" in error_text:
            error_reply_text = msg.t(lang, "ERROR_NO_VIDEO")
        elif "does not contain an audio track" in error_text:
            error_reply_text = msg.t(lang, "ERROR_NO_AUDIO")
        elif "private" in error_text:
            error_reply_text = msg.t(lang, "ERROR_PRIVATE")
        elif "unavailable" in error_text or "not available" in error_text or "removed" in error_text:
            error_reply_text = msg.t(lang, "ERROR_UNAVAILABLE")
        elif "timeout" in error_text or "timed out" in error_text:
            error_reply_text = msg.t(lang, "ERROR_TIMEOUT")
        elif "networkerror" in error_name.lower() or "readerror" in error_name.lower():
            error_reply_text = msg.t(lang, "ERROR_NETWORK")
        elif upload and "too big" in error_text:
            error_reply_text = msg.t(lang, "FILE_TOO_BIG_TO_DOWNLOAD")
        elif "too large" in error_text or "entity too large" in error_text:
            error_reply_text = msg.t(lang, "ERROR_TOO_LARGE")
        elif "429" in error_text or "too many requests" in error_text or "rate limit" in error_text:
            # Groq (transcription/cleanup) hit its own rate limit - see
            # utils/network_retry.py's _is_rate_limited. Distinct from
            # ERROR_GENERIC on purpose: telling the user to "check your
            # link" here would be actively wrong, since the link is fine
            # and the problem is capacity that only clears with time.
            error_reply_text = msg.t(lang, "ERROR_RATE_LIMITED")
        else:
            error_reply_text = msg.t(lang, "ERROR_GENERIC")

        await call_with_retry(message.reply_sticker, STICKER_ERROR)
        await call_with_retry(status_message.edit_text, error_reply_text, parse_mode="Markdown")

    finally:
        # Best-effort - a missing/already-removed file shouldn't mask
        # whatever the actual pipeline result was.
        for path in (video_path, None if keep_audio else audio_path):
            _remove_file(path)

        _mark_free(context)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await call_with_retry(query.answer)

    lang = _lang(query.from_user.id)
    data = query.data

    # Checked BEFORE the busy-guard below on purpose: while a long-content
    # confirmation is pending, `busy` IS True (set in handle_link before
    # the duration lookup, deliberately left set through the warning) -
    # without this early check, the busy-guard right below would reject
    # the user's own confirm/cancel tap with STILL_WORKING, since from its
    # perspective this user already has something in flight.
    if data == "confirm_process":
        await _handle_confirm_long_content(query, context, lang)
        return
    if data == "cancel_process":
        await _handle_cancel_long_content(query, context, lang)
        return

    # Copy is a cheap re-send of text already in memory (no pipeline work),
    # so like confirm/cancel above it skips the busy-guard.
    if data == "copy_text":
        await _handle_copy(query, context, lang)
        return

    # Same for the Uzbek alphabet toggle - a re-render of text in memory.
    if data == "toggle_alphabet":
        await _handle_toggle_alphabet(query, context, lang)
        return

    if _is_busy(context):
        await call_with_retry(query.message.reply_text, msg.t(lang, "STILL_WORKING"), parse_mode="Markdown")
        return

    _mark_busy(context)
    try:
        if data in ("export_pdf", "export_txt"):
            await _handle_export(query, context, lang, data)
        elif data == "translate_menu" or data.startswith("translate_to_"):
            # Catches a tap on a translate button from a keyboard that was
            # already on screen before TRANSLATION_ENABLED was turned off -
            # without this, an old message's button would silently route
            # into handlers that still work fine but expose a feature
            # that's meant to be hidden right now.
            if not TRANSLATION_ENABLED:
                await call_with_retry(
                    query.message.reply_text, msg.t(lang, "TRANSLATION_UNAVAILABLE"), parse_mode="Markdown"
                )
            elif data == "translate_menu":
                await _handle_translate_menu(query, context, lang)
            else:
                await _handle_translate_to(query, context, lang, data.replace("translate_to_", ""))
        elif data == "summarize":
            await _handle_summarize(query, context, lang)
        elif data.startswith("get_text_"):
            await _handle_get_text(query, context, lang, data.replace("get_text_", ""))
        elif data.startswith("history_"):
            await _handle_history_select(query, context, lang, data.replace("history_", ""))
    finally:
        _mark_free(context)


async def _handle_get_text(query, context, lang, token):
    """The user tapped "Get text" under audio sent earlier - transcribe the
    audio we kept for them (one-shot: _process_link deletes it when done)."""

    registry = _pending_registry(context)
    info = registry.get(token)

    if not info or info["user_id"] != query.from_user.id or not os.path.exists(info["audio_path"]):
        if info and info["user_id"] == query.from_user.id:
            registry.pop(token, None)
        await call_with_retry(query.message.reply_text, msg.t(lang, "GET_TEXT_EXPIRED"), parse_mode="Markdown")
        return

    registry.pop(token, None)

    # Remove the button so a second tap can't start the same job twice.
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        logger.warning("Could not remove the Get text button")

    await _process_link(
        query.message, context, info["url"], info["platform"], info["platform_name"],
        lang, query.from_user.id, resume=info,
    )


async def _handle_toggle_alphabet(query, context, lang):
    """Flips this user's Uzbek alphabet (saved for next time) and re-sends
    what's on screen in the other one. Cheap - no pipeline work."""

    user_id = query.from_user.id
    on_screen = context.user_data.get("export_text") or context.user_data.get("last_transcript")

    if not on_screen or context.user_data.get("export_language") != "uz":
        await call_with_retry(query.message.reply_text, msg.t(lang, "NO_TRANSCRIPT_SAVED"), parse_mode="Markdown")
        return

    choice = "old" if _alphabet_for(user_id) == "new" else "new"
    set_uzbek_alphabet(user_id, choice)

    original_on_screen = on_screen == context.user_data.get("last_transcript")

    # Translate/Summarize always start from last_transcript, so keep it in
    # the chosen alphabet too (it's Uzbek whenever detected_language is).
    if context.user_data.get("detected_language") == "uz" and context.user_data.get("last_transcript"):
        context.user_data["last_transcript"] = render_uzbek(context.user_data["last_transcript"], choice)

    rendered = render_uzbek(on_screen, choice)
    context.user_data["export_text"] = rendered

    changed = msg.t(lang, "ALPHABET_CHANGED_NEW" if choice == "new" else "ALPHABET_CHANGED_OLD")
    await send_result_text(query.message, [(changed, False)], rendered)

    if original_on_screen:
        await call_with_retry(
            query.message.reply_text,
            msg.t(lang, "NEXT_ACTIONS_PROMPT"),
            reply_markup=build_export_keyboard(lang, rendered, alphabet=choice),
        )
    else:
        await call_with_retry(
            query.message.reply_text,
            msg.t(lang, "EXPORT_PROMPT"),
            reply_markup=build_save_keyboard(lang, rendered, alphabet=choice),
        )


async def _handle_copy(query, context, lang):
    """Re-sends whatever is currently on screen as monospace (tap-to-copy)
    messages - the fallback for text too long for Telegram's native copy button."""

    text = context.user_data.get("export_text") or context.user_data.get("last_transcript")
    if not text:
        await call_with_retry(query.message.reply_text, msg.t(lang, "NO_TRANSCRIPT_SAVED"), parse_mode="Markdown")
        return

    chunks, _ = split_into_chunks(text, max_chars=TELEGRAM_MESSAGE_MAX_CHARS)
    hint = msg.t(lang, "COPY_HINT")

    for index, chunk in enumerate(chunks):
        parts = [(hint, False), ("\n\n", False)] if index == 0 else []
        copy_text, copy_entities = build_bold_message(parts + [(chunk, CODE)])
        await call_with_retry(query.message.reply_text, copy_text, entities=copy_entities)


async def _handle_confirm_long_content(query, context, lang):
    url = context.user_data.pop("pending_url", None)
    platform = context.user_data.pop("pending_platform", None)
    platform_name = context.user_data.pop("pending_platform_name", None)

    if not url:
        # Pending state is gone (e.g. the bot restarted between the warning
        # and this tap) - nothing to resume. Release busy (set when the
        # original link came in) rather than leaving the user stuck, and
        # ask for the link again.
        _mark_free(context)
        no_link_text, no_link_entities = msg.no_link_found_text(lang)
        await call_with_retry(query.message.reply_text, no_link_text, entities=no_link_entities)
        return

    # busy is already True from when the original link triggered the
    # warning - _process_link marks it again (harmless, idempotent) and
    # releases it in its own finally block once processing ends.
    await _process_link(query.message, context, url, platform, platform_name, lang, query.from_user.id)


async def _handle_cancel_long_content(query, context, lang):
    context.user_data.pop("pending_url", None)
    context.user_data.pop("pending_platform", None)
    context.user_data.pop("pending_platform_name", None)
    # Releases the busy flag set when the original long-content link came
    # in - without this, the user would stay "occupied" forever with
    # nothing actually in flight to resolve it.
    _mark_free(context)

    await call_with_retry(query.message.reply_text, msg.t(lang, "PROCESSING_CANCELLED"), parse_mode="Markdown")


async def _handle_export(query, context, lang, data):
    # Reads export_text/export_language, NOT last_transcript/
    # detected_language - this exports whatever's CURRENTLY on screen
    # (the original transcript, or a translation/summary of it), which is
    # what "save this" should mean regardless of which screen the user
    # tapped it from. Falls back to last_transcript for any older
    # in-flight session that set that but not export_text yet.
    transcript = context.user_data.get("export_text") or context.user_data.get("last_transcript")
    detected_language = context.user_data.get("export_language") or context.user_data.get("detected_language", "en")

    if not transcript:
        await call_with_retry(query.message.reply_text, msg.t(lang, "NO_TRANSCRIPT_SAVED"), parse_mode="Markdown")
        return

    os.makedirs(EXPORT_DIR, exist_ok=True)

    # A per-request unique name - a fixed "transcript_{language}.pdf" name
    # would be shared by every user exporting that language, so concurrent
    # exports (real with concurrent_updates) could read or overwrite each
    # other's file.
    unique_id = uuid.uuid4().hex
    filepath = None

    try:
        if data == "export_pdf":
            filepath = os.path.join(EXPORT_DIR, f"transcript_{unique_id}.pdf")
            # language_code drives RTL/Arabic reshaping in export_to_pdf, so
            # it must match the TRANSCRIPT's own spoken language, not the
            # bot's interface language.
            await asyncio.to_thread(export_to_pdf, transcript, filepath, language_code=detected_language)
            caption = msg.export_ready_caption(lang, "pdf")
        else:
            filepath = os.path.join(EXPORT_DIR, f"transcript_{unique_id}.txt")
            await asyncio.to_thread(export_to_text, transcript, filepath)
            caption = msg.export_ready_caption(lang, "text")

        # caption's {file_format} comes from a fixed dict ("PDF"/"text
        # file"), never from the transcript content itself - safe.
        with open(filepath, "rb") as document_file:
            await call_with_retry(
                query.message.reply_document, document=document_file, **_caption_kwargs(caption)
            )

    except Exception as error:
        logger.exception(f"Export failed: {type(error).__name__}: {error}")
        await call_with_retry(
            query.message.reply_text,
            msg.t(lang, "EXPORT_FAILED"),
            parse_mode="Markdown",
            reply_markup=build_save_keyboard(lang, transcript),
        )

    finally:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                logger.warning(f"Failed to remove export file: {filepath}")


async def _handle_translate_menu(query, context, lang):
    if not context.user_data.get("last_transcript"):
        await call_with_retry(query.message.reply_text, msg.t(lang, "NO_TRANSCRIPT_SAVED"), parse_mode="Markdown")
        return

    detected_language = context.user_data.get("detected_language")

    await call_with_retry(
        query.message.reply_text,
        msg.t(lang, "TRANSLATE_PICKER_PROMPT"),
        reply_markup=build_translate_language_keyboard(lang, exclude_code=detected_language)
    )


async def _handle_translate_to(query, context, lang, target_code):
    transcript = context.user_data.get("last_transcript")
    detected_language = context.user_data.get("detected_language", "en")

    if not transcript:
        await call_with_retry(query.message.reply_text, msg.t(lang, "NO_TRANSCRIPT_SAVED"), parse_mode="Markdown")
        return

    if target_code not in msg.SUPPORTED_LANGUAGES:
        return

    if target_code == detected_language:
        await call_with_retry(query.message.reply_text, msg.t(lang, "TRANSLATION_SAME_LANGUAGE"), parse_mode="Markdown")
        return

    status_message = await call_with_retry(
        query.message.reply_text, msg.t(lang, "TRANSLATING"), parse_mode="Markdown"
    )

    try:
        # Uzbek source text is shown in the revised alphabet, which Google
        # Translate doesn't know - hand it the standard Latin and convert an
        # Uzbek RESULT back to the revised alphabet.
        source_text = pipeline_alphabet(transcript) if detected_language == "uz" else transcript
        translated = await asyncio.to_thread(translate_text, source_text, target_code, detected_language)
        if target_code == "uz":
            translated = render_uzbek(translated, _alphabet_for(query.from_user.id))
        await send_result_text(query.message, msg.translation_header_parts(lang), translated)
        # "Translating..." has been superseded by the result just sent -
        # delete it now that it's actually landed, rather than leaving it
        # as a stale status line. Deleted only AFTER a successful send (not
        # before) so the except block below still has a live message to
        # edit into TRANSLATION_FAILED if send_result_text itself fails.
        await _delete_silently(status_message)

        # Now the translation (not the original) is what's on screen, so
        # that's what "save this" should export - see build_save_keyboard's
        # comment. export_language becomes the TRANSLATION's language
        # (target_code), not the original - matters for PDF's RTL/Arabic
        # reshaping if translating into/out of Arabic.
        context.user_data["export_text"] = translated
        context.user_data["export_language"] = target_code

        await call_with_retry(
            query.message.reply_text,
            msg.t(lang, "EXPORT_PROMPT"),
            reply_markup=build_save_keyboard(
                lang, translated, alphabet=_alphabet_button_state(lang, target_code, query.from_user.id)
            )
        )
    except Exception as error:
        logger.exception(f"Translation failed: {type(error).__name__}: {error}")
        await call_with_retry(
            status_message.edit_text,
            msg.t(lang, "TRANSLATION_FAILED"),
            parse_mode="Markdown",
            reply_markup=build_translate_language_keyboard(lang, exclude_code=detected_language),
        )


async def _handle_summarize(query, context, lang):
    transcript = context.user_data.get("last_transcript")

    if not transcript:
        await call_with_retry(query.message.reply_text, msg.t(lang, "NO_TRANSCRIPT_SAVED"), parse_mode="Markdown")
        return

    status_message = await call_with_retry(
        query.message.reply_text, msg.t(lang, "SUMMARIZING"), parse_mode="Markdown"
    )

    try:
        summary_is_uzbek = context.user_data.get("detected_language") == "uz"
        summary_source = pipeline_alphabet(transcript) if summary_is_uzbek else transcript
        summary = await asyncio.to_thread(summarize_transcript, summary_source)
        if summary_is_uzbek:
            summary = render_uzbek(summary, _alphabet_for(query.from_user.id))
        await send_result_text(query.message, msg.summary_header_parts(lang), summary)
        # "Summarizing..." has been superseded by the result just sent -
        # delete it now that it's actually landed (only after a successful
        # send, not before - see _handle_translate_to's identical comment
        # for why the except block below needs status_message to still
        # exist if send_result_text itself fails).
        await _delete_silently(status_message)

        # Now the summary (not the full transcript) is what's on screen -
        # see build_save_keyboard's comment. Language stays the original
        # detected_language - summarize_transcript() keeps the transcript's
        # own language, it doesn't translate.
        context.user_data["export_text"] = summary
        context.user_data["export_language"] = context.user_data.get("detected_language", "en")

        await call_with_retry(
            query.message.reply_text,
            msg.t(lang, "EXPORT_PROMPT"),
            reply_markup=build_save_keyboard(
                lang, summary,
                alphabet=_alphabet_button_state(lang, context.user_data.get("detected_language"), query.from_user.id),
            )
        )
    except Exception as error:
        logger.exception(f"Summarization failed: {type(error).__name__}: {error}")
        await call_with_retry(
            status_message.edit_text,
            msg.t(lang, "SUMMARY_FAILED"),
            parse_mode="Markdown",
            reply_markup=build_summarize_retry_keyboard(lang),
        )


async def _handle_history_select(query, context, lang, transcript_id_raw):
    try:
        transcript_id = int(transcript_id_raw)
    except ValueError:
        await call_with_retry(query.message.reply_text, msg.t(lang, "HISTORY_NOT_FOUND"), parse_mode="Markdown")
        return

    row = get_transcript_by_id(transcript_id, query.from_user.id)

    if not row:
        await call_with_retry(query.message.reply_text, msg.t(lang, "HISTORY_NOT_FOUND"), parse_mode="Markdown")
        return

    _id, platform, detected_language, title, transcript_text, created_at = row

    # Stored Uzbek may be in either alphabet - show it in this user's choice.
    if detected_language == "uz":
        transcript_text = render_uzbek(transcript_text, _alphabet_for(query.from_user.id))

    # Selecting a history entry makes it the active transcript, so any
    # export/translate/summarize tap afterward applies to this one, not
    # whatever was active before.
    context.user_data["last_transcript"] = transcript_text
    context.user_data["detected_language"] = detected_language
    context.user_data["export_text"] = transcript_text
    context.user_data["export_language"] = detected_language

    short_date = msg.format_short_date(lang, created_at)
    await call_with_retry(
        query.message.reply_text, msg.history_selected_info(lang, title, platform, detected_language, short_date)
    )

    await send_result_text(query.message, msg.transcript_header_parts(lang), transcript_text)

    await call_with_retry(
        query.message.reply_text,
        msg.t(lang, "NEXT_ACTIONS_PROMPT"),
        reply_markup=build_export_keyboard(
            lang, transcript_text, alphabet=_alphabet_button_state(lang, detected_language, query.from_user.id)
        )
    )

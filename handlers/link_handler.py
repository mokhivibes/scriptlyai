import asyncio
import logging
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.link_detector import extract_url, detect_platform
from utils.text_chunker import split_into_chunks
from utils import messages as msg
from services.youtube_service import download_youtube_video
from services.twitter_service import download_twitter_video
from services.tiktok_service import download_tiktok_video
from services.audio_service import extract_audio
from services.ai_cleanup_service import clean_transcript
from services.export_service import export_to_pdf, export_to_text
from database import add_transcript, get_transcript_by_id, get_interface_language
from utils.network_retry import call_with_retry, call_sync_with_retry
from handlers.command_handler import help_command, history_command, language_command

logger = logging.getLogger(__name__)


# Telegram hard-rejects any single message over 4096 characters. Stay
# comfortably under that so a long transcript doesn't crash with "Message
# is too long".
TELEGRAM_MESSAGE_MAX_CHARS = 4000

EXPORT_DIR = "downloads"

# Above this, show a confirm/cancel warning before committing to the full
# pipeline instead of silently making someone wait - a full song can take
# 5+ minutes to transcribe, and results are less reliable for music/singing
# than speech (see README Known Limitations). Chosen to comfortably clear
# typical short-form clips (YouTube Shorts, TikTok, Reels) while catching
# most full songs and longer spoken content.
LONG_CONTENT_THRESHOLD_SECONDS = 90


def _lang(user_id) -> str:
    return get_interface_language(user_id) or msg.DEFAULT_LANGUAGE


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

    options = {"quiet": True, "no_warnings": True, "skip_download": True}
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


async def send_long_text(message, text: str):
    """
    Send text as one or more Telegram messages, splitting at paragraph/
    sentence boundaries (never mid-sentence) so a long transcript doesn't
    hit Telegram's per-message character limit.
    """

    chunks, _ = split_into_chunks(text, max_chars=TELEGRAM_MESSAGE_MAX_CHARS)

    for chunk in chunks:
        await call_with_retry(message.reply_text, chunk)


def build_export_keyboard(lang):
    keyboard = [
        [
            InlineKeyboardButton(msg.t(lang, "EXPORT_PDF_BUTTON"), callback_data="export_pdf"),
            InlineKeyboardButton(msg.t(lang, "EXPORT_TXT_BUTTON"), callback_data="export_txt"),
        ],
    ]
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


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    shortcut = msg.match_shortcut(update.message.text)
    if shortcut:
        await _SHORTCUT_HANDLERS[shortcut](update, context)
        return

    lang = _lang(update.effective_user.id)

    if _is_busy(context):
        await call_with_retry(update.message.reply_text, msg.t(lang, "STILL_WORKING"))
        return

    text = update.message.text
    url = extract_url(text)

    if not url:
        await call_with_retry(update.message.reply_text, msg.t(lang, "NO_LINK_FOUND"))
        return

    platform = detect_platform(url)

    if platform in ("youtube", "instagram", "twitter", "tiktok"):
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
        }[platform]

        duration = await asyncio.to_thread(_get_duration_seconds, url)

        if duration and duration > LONG_CONTENT_THRESHOLD_SECONDS:
            context.user_data["pending_url"] = url
            context.user_data["pending_platform"] = platform
            context.user_data["pending_platform_name"] = platform_name

            await call_with_retry(
                update.message.reply_text,
                msg.long_content_warning(lang, duration / 60),
                reply_markup=build_long_content_confirm_keyboard(lang)
            )
            return

        await _process_link(update.message, context, url, platform, platform_name, lang, update.effective_user.id)

    elif platform == "facebook":
        await call_with_retry(update.message.reply_text, msg.t(lang, "FACEBOOK_PLACEHOLDER"))

    else:
        await call_with_retry(update.message.reply_text, msg.t(lang, "UNRECOGNIZED_LINK"))


async def _process_link(message, context, url, platform, platform_name, lang, user_id):
    """
    Runs the actual download -> extract -> transcribe -> clean -> export
    pipeline. Called either immediately (short content) or from the
    confirm/cancel callback (long content, after the user taps "go ahead").
    `message` is whichever object has .reply_text/.reply_audio available -
    update.message for the immediate path, query.message for the
    confirmed-after-warning path.
    """

    _mark_busy(context)

    # One status message, edited in place through each processing step,
    # instead of sending a new message per step - keeps the chat from
    # filling up with transient "still working on it" messages.
    # parse_mode is safe here: platform_name comes from the fixed dict
    # above (exactly 4 known values), never from unpredictable content.
    status_message = await call_with_retry(
        message.reply_text, msg.downloading_message(lang, platform_name), parse_mode="Markdown"
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
        if platform == "youtube":
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

        logger.info(f"Video downloaded: {video_path}")

        await call_with_retry(status_message.edit_text, msg.extracting_audio_message(lang))

        audio_path = await asyncio.to_thread(extract_audio, video_path)

        logger.info(f"Audio extracted: {audio_path}")

        with open(audio_path, "rb") as audio_file:
            await call_with_retry(
                message.reply_audio,
                audio=audio_file,
                filename=os.path.basename(audio_path),
                caption=msg.t(lang, "AUDIO_CAPTION")
            )

        await call_with_retry(status_message.edit_text, msg.transcribing_message(lang))

        from services.speech_service import transcribe_audio

        # Blind auto-detection has repeatedly misdetected real Uzbek audio
        # as a linguistically-related-but-wrong language (Kazakh, Turkish,
        # Persian all observed on real content) - see README Known
        # Limitations. A same-day fix forcing language="uz" for Uzbek-
        # interface users was tried and DID help on one real case, but was
        # reverted before launch: further testing showed the same audio
        # produced wildly different quality across separate runs even with
        # the language forced (Whisper's own decoding randomness on
        # hard/singing content, not something the language hint fixes), and
        # forcing still carried the tradeoff of misforcing genuinely
        # non-Uzbek content for Uzbek-interface users. Superseded by the
        # duration-based warning + /help disclaimer (see
        # LONG_CONTENT_THRESHOLD_SECONDS below), which is honest about
        # reliability without forcing anyone's language. Plain auto-detect
        # for all 4 interface languages.
        transcript, detected_language = await asyncio.to_thread(transcribe_audio, audio_path)

        logger.info(f"Detected language: {detected_language}")
        logger.info(f"Raw transcript: {transcript}")

        await call_with_retry(status_message.edit_text, msg.cleaning_message(lang))

        cleaned_transcript = await asyncio.to_thread(clean_transcript, transcript)
        logger.info(f"Cleaned transcript: {cleaned_transcript}")

        context.user_data["last_transcript"] = cleaned_transcript
        context.user_data["detected_language"] = detected_language

        add_transcript(
            user_id=user_id,
            platform=platform,
            detected_language=detected_language,
            title=video_title,
            transcript=cleaned_transcript
        )

        await call_with_retry(message.reply_text, msg.t(lang, "TRANSCRIPT_HEADER"))
        await send_long_text(message, cleaned_transcript)

        await call_with_retry(
            message.reply_text,
            msg.t(lang, "EXPORT_PROMPT"),
            reply_markup=build_export_keyboard(lang)
        )

    except Exception as error:
        error_name = type(error).__name__
        error_text = str(error).lower()

        logger.exception(f"Processing failed for platform={platform}: {error_name}: {error}")

        if "no video could be found" in error_text:
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
        elif "too large" in error_text or "entity too large" in error_text:
            error_reply_text = msg.t(lang, "ERROR_TOO_LARGE")
        else:
            error_reply_text = msg.t(lang, "ERROR_GENERIC")

        await call_with_retry(status_message.edit_text, error_reply_text)

    finally:
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

    if _is_busy(context):
        await call_with_retry(query.message.reply_text, msg.t(lang, "STILL_WORKING"))
        return

    _mark_busy(context)
    try:
        if data in ("export_pdf", "export_txt"):
            await _handle_export(query, context, lang, data)
        elif data.startswith("history_"):
            await _handle_history_select(query, context, lang, data.replace("history_", ""))
    finally:
        _mark_free(context)


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
        await call_with_retry(query.message.reply_text, msg.t(lang, "NO_LINK_FOUND"))
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

    await call_with_retry(query.message.reply_text, msg.t(lang, "PROCESSING_CANCELLED"))


async def _handle_export(query, context, lang, data):
    transcript = context.user_data.get("last_transcript")
    detected_language = context.user_data.get("detected_language", "en")

    if not transcript:
        await call_with_retry(query.message.reply_text, msg.t(lang, "NO_TRANSCRIPT_SAVED"))
        return

    os.makedirs(EXPORT_DIR, exist_ok=True)

    try:
        if data == "export_pdf":
            filepath = os.path.join(EXPORT_DIR, f"transcript_{detected_language}.pdf")
            # language_code drives RTL/Arabic reshaping in export_to_pdf, so
            # it must match the TRANSCRIPT's own spoken language, not the
            # bot's interface language.
            await asyncio.to_thread(export_to_pdf, transcript, filepath, language_code=detected_language)
            caption = msg.export_ready_caption(lang, "pdf")
        else:
            filepath = os.path.join(EXPORT_DIR, f"transcript_{detected_language}.txt")
            await asyncio.to_thread(export_to_text, transcript, filepath)
            caption = msg.export_ready_caption(lang, "text")

        # caption's {file_format} comes from a fixed dict ("PDF"/"text
        # file"), never from the transcript content itself - safe.
        with open(filepath, "rb") as document_file:
            await call_with_retry(
                query.message.reply_document, document=document_file, caption=caption, parse_mode="Markdown"
            )

    except Exception as error:
        logger.exception(f"Export failed: {type(error).__name__}: {error}")
        await call_with_retry(query.message.reply_text, msg.t(lang, "EXPORT_FAILED"))


async def _handle_history_select(query, context, lang, transcript_id_raw):
    try:
        transcript_id = int(transcript_id_raw)
    except ValueError:
        await call_with_retry(query.message.reply_text, msg.t(lang, "HISTORY_NOT_FOUND"))
        return

    row = get_transcript_by_id(transcript_id, query.from_user.id)

    if not row:
        await call_with_retry(query.message.reply_text, msg.t(lang, "HISTORY_NOT_FOUND"))
        return

    _id, platform, detected_language, title, transcript_text, created_at = row

    # Selecting a history entry makes it the active transcript, so any
    # export tap afterward applies to this one, not whatever was active
    # before.
    context.user_data["last_transcript"] = transcript_text
    context.user_data["detected_language"] = detected_language

    short_date = msg.format_short_date(lang, created_at)
    await call_with_retry(
        query.message.reply_text, msg.history_selected_info(lang, title, platform, detected_language, short_date)
    )

    await call_with_retry(query.message.reply_text, msg.t(lang, "TRANSCRIPT_HEADER"))
    await send_long_text(query.message, transcript_text)

    await call_with_retry(
        query.message.reply_text,
        msg.t(lang, "EXPORT_PROMPT"),
        reply_markup=build_export_keyboard(lang)
    )

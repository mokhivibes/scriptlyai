import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database import get_transcripts_for_user, get_interface_language, set_interface_language, delete_user_data
from utils import messages as msg
from utils.network_retry import call_with_retry
from utils.stickers import STICKER_WELCOME
from config import OWNER_USER_ID

HISTORY_LIMIT = 10
FEEDBACK_MAX_CHARS = 1000
FEEDBACK_COOLDOWN_SECONDS = 60


def _lang(user_id) -> str:
    return get_interface_language(user_id) or msg.DEFAULT_LANGUAGE


def _picker_button(code: str) -> InlineKeyboardButton:
    label = f"{msg.LANGUAGE_FLAGS[code]} {msg.language_native_name(code)}"
    return InlineKeyboardButton(label, callback_data=f"setlang_{code}")


def build_language_picker_keyboard():
    """Buttons labeled in each language's OWN name (with a matching flag), so
    a user can recognize their language before they've picked anything - not
    affected by any current interface-language setting."""

    keyboard = [
        [_picker_button("en"), _picker_button("ru")],
        [_picker_button("ar"), _picker_button("uz")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_shortcuts_keyboard(lang):
    """
    A persistent reply keyboard (always visible below the text input,
    survives across messages until replaced), separate from the inline
    keyboards used elsewhere for contextual, per-message choices (language
    picker, export buttons) - both are kept since they serve different
    purposes. Labels are friendly, localized, emoji-prefixed text (not raw
    "/help" etc.) to match the bot's tone - since Telegram only
    auto-recognizes a literal "/command" as a command, tapping one of these
    sends its label as a plain text message, which handle_link() checks
    against msg.match_shortcut() before falling through to link detection.
    """

    help_label, history_label, language_label = msg.shortcut_labels(lang)
    keyboard = [[help_label, history_label, language_label]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(update.effective_user.id)
    text, entities = msg.help_text(lang)
    await call_with_retry(update.message.reply_text, text, entities=entities)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(update.effective_user.id)
    had_data = bool(context.user_data)
    context.user_data.clear()

    key = "CANCEL_HAD_DATA" if had_data else "CANCEL_NOTHING"
    # Fully static, developer-written copy - safe to format.
    await call_with_retry(update.message.reply_text, msg.t(lang, key), parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(update.effective_user.id)
    rows = get_transcripts_for_user(update.effective_user.id, limit=HISTORY_LIMIT)

    if not rows:
        empty_text, empty_entities = msg.history_empty_text(lang)
        await call_with_retry(update.message.reply_text, empty_text, entities=empty_entities)
        return

    keyboard = []
    for transcript_id, platform, detected_language, title, _transcript, created_at in rows:
        short_date = msg.format_short_date(lang, created_at)
        label = msg.history_entry_label(lang, platform, title, detected_language, short_date)
        keyboard.append([InlineKeyboardButton(label, callback_data=f"history_{transcript_id}")])

    await call_with_retry(
        update.message.reply_text,
        msg.t(lang, "HISTORY_HEADER"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Always shows the picker, regardless of any saved preference, so users can change their mind anytime."""

    await call_with_retry(
        update.message.reply_text,
        msg.LANGUAGE_PICKER_PROMPT,
        reply_markup=build_language_picker_keyboard()
    )


async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await call_with_retry(query.answer)

    language_code = query.data.replace("setlang_", "")

    if language_code not in msg.SUPPORTED_LANGUAGES:
        return

    user_id = query.from_user.id
    # Check BEFORE writing - this is the only way to tell "never chosen
    # before" (first-time onboarding) apart from "already had one, just
    # switching" (short confirmation), since both paths share this same
    # callback regardless of whether the picker was opened via /start or
    # /language.
    is_first_time = get_interface_language(user_id) is None

    set_interface_language(user_id, language_code)

    if is_first_time:
        # No logo here - it's shown exactly once, on the language-picker
        # message in main.py's start(), not repeated here right after.
        # welcome_text() returns (text, entities) - see rich_text.py for
        # why the user's own Telegram first name (which can contain
        # anything, including a literal * or _) gets entity-based bold
        # instead of parse_mode="Markdown". The persistent shortcuts
        # keyboard is attached here rather than on the language-picker
        # message itself, since a message can only carry one keyboard
        # type (inline XOR reply) - this is the first message after
        # language selection completes, for either the first-time or
        # switching path.
        first_name = query.from_user.first_name or ""
        await call_with_retry(query.message.reply_sticker, STICKER_WELCOME)
        text, entities = msg.welcome_text(language_code, first_name)
        await call_with_retry(
            query.message.reply_text,
            text,
            entities=entities,
            reply_markup=build_shortcuts_keyboard(language_code)
        )
    else:
        # Fully static, developer-written copy - safe to format.
        await call_with_retry(
            query.message.reply_text,
            msg.t(language_code, "LANGUAGE_CHANGED"),
            parse_mode="Markdown",
            reply_markup=build_shortcuts_keyboard(language_code)
        )


def build_privacy_keyboard(lang):
    keyboard = [[InlineKeyboardButton(msg.t(lang, "DELETE_DATA_BUTTON"), callback_data="request_delete_data")]]
    return InlineKeyboardMarkup(keyboard)


def build_delete_data_confirm_keyboard(lang):
    keyboard = [[
        InlineKeyboardButton(msg.t(lang, "DELETE_DATA_CONFIRM_YES_BUTTON"), callback_data="confirm_delete_data"),
        InlineKeyboardButton(msg.t(lang, "CONFIRM_NO_BUTTON"), callback_data="cancel_delete_data"),
    ]]
    return InlineKeyboardMarkup(keyboard)


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(update.effective_user.id)
    # Fully static, developer-written copy - safe to format.
    await call_with_retry(
        update.message.reply_text,
        msg.t(lang, "PRIVACY_TEXT"),
        parse_mode="Markdown",
        reply_markup=build_privacy_keyboard(lang)
    )


async def request_delete_data_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Separate confirm step before request_delete_data_callback actually
    deletes anything - this is a permanent, irreversible action (unlike
    /cancel, which only clears in-flight in-memory state), so it gets the
    same explicit confirm/cancel pattern already used for long-content
    warnings in handlers/link_handler.py.
    """

    query = update.callback_query
    await call_with_retry(query.answer)
    lang = _lang(query.from_user.id)

    await call_with_retry(
        query.message.reply_text,
        msg.t(lang, "DELETE_DATA_CONFIRM_PROMPT"),
        parse_mode="Markdown",
        reply_markup=build_delete_data_confirm_keyboard(lang)
    )


async def confirm_delete_data_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await call_with_retry(query.answer)
    lang = _lang(query.from_user.id)

    delete_user_data(query.from_user.id)
    context.user_data.clear()

    await call_with_retry(query.message.reply_text, msg.t(lang, "DELETE_DATA_DONE"), parse_mode="Markdown")


async def cancel_delete_data_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await call_with_retry(query.answer)
    lang = _lang(query.from_user.id)

    await call_with_retry(query.message.reply_text, msg.t(lang, "DELETE_DATA_CANCELLED"), parse_mode="Markdown")


async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/feedback <text> - relays the message to the owner. Plain text both
    ways (no parse_mode): the content is user-controlled."""

    user = update.effective_user
    lang = _lang(user.id)
    text = " ".join(context.args or []).strip()

    if not text:
        await call_with_retry(update.message.reply_text, msg.t(lang, "FEEDBACK_USAGE"))
        return

    now = time.time()
    if now - context.user_data.get("last_feedback_at", 0) < FEEDBACK_COOLDOWN_SECONDS:
        await call_with_retry(update.message.reply_text, msg.t(lang, "FEEDBACK_TOO_SOON"))
        return

    context.user_data["last_feedback_at"] = now

    if OWNER_USER_ID:
        handle = f"@{user.username}" if user.username else "no username"
        await call_with_retry(
            context.bot.send_message,
            chat_id=OWNER_USER_ID,
            text=f"💬 Feedback from {user.first_name} ({handle}, id {user.id}, lang {lang}):\n\n{text[:FEEDBACK_MAX_CHARS]}",
        )

    await call_with_retry(update.message.reply_text, msg.t(lang, "FEEDBACK_THANKS"))

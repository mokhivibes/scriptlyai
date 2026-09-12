from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database import get_transcripts_for_user, get_interface_language, set_interface_language
from utils import messages as msg
from utils.network_retry import call_with_retry

HISTORY_LIMIT = 10


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
    # Fully static, developer-written copy - safe to format.
    await call_with_retry(update.message.reply_text, msg.t(lang, "HELP_TEXT"), parse_mode="Markdown")


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
        await call_with_retry(update.message.reply_text, msg.t(lang, "HISTORY_EMPTY"))
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
        # welcome_text embeds the user's own Telegram first name, which can
        # contain anything (including a literal * or _) - kept plain text,
        # no parse_mode, same reasoning as transcript/title content. The
        # persistent shortcuts keyboard is attached here rather than on the
        # language-picker message itself, since a message can only carry
        # one keyboard type (inline XOR reply) - this is the first message
        # after language selection completes, for either the first-time or
        # switching path.
        first_name = query.from_user.first_name or ""
        await call_with_retry(
            query.message.reply_text,
            msg.welcome_text(language_code, first_name),
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

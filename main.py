import logging

from telegram import BotCommand, MenuButtonCommands, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from logging_config import setup_logging
from config import BOT_TOKEN
from database import init_database, add_user, get_interface_language
from handlers.link_handler import handle_link, handle_callback_query
from handlers.command_handler import (
    help_command,
    cancel_command,
    history_command,
    language_command,
    set_language_callback,
    build_language_picker_keyboard,
    build_shortcuts_keyboard,
)
from utils import messages as msg
from utils.network_retry import call_with_retry
from utils.logo import send_logo

logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """
    Runs once after the bot connects, before polling starts. Sets up two
    pieces of Telegram-native discoverability that don't belong to any one
    chat: the command list shown by the chat menu button, and the menu
    button itself, which defaults to Telegram's own icon rather than the
    command list unless explicitly set to MenuButtonCommands.

    IMPORTANT: setMyCommands' language_code matches the user's TELEGRAM APP
    language (device/client UI setting), not our own /language preference
    stored in the database - those are two independent settings. A user
    could have our bot's interface language set to Arabic while their
    Telegram app itself is in English, and they'd see the English command
    list, not the Arabic one. The per-language calls below are a best-effort
    match for users whose app language happens to line up; the final call
    with no language_code sets the default every other user falls back to.
    """

    for lang in msg.SUPPORTED_LANGUAGES:
        commands = [
            BotCommand(command, description)
            for command, description in msg.command_descriptions(lang)
        ]
        await application.bot.set_my_commands(commands, language_code=lang)

    default_commands = [
        BotCommand(command, description)
        for command, description in msg.command_descriptions(msg.DEFAULT_LANGUAGE)
    ]
    await application.bot.set_my_commands(default_commands)

    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    lang = get_interface_language(user.id)

    if lang is None:
        # First time (or a pre-existing user from before this feature) -
        # ask which language to use rather than guessing from Telegram's
        # own language_code. A single message can only carry ONE keyboard
        # (inline XOR reply), so the persistent shortcuts keyboard isn't
        # attached here - it's attached once language selection completes,
        # in command_handler.py's set_language_callback, which chronologically
        # makes more sense anyway (shortcuts appear once the user is set up).
        # LANGUAGE_PICKER_PROMPT is static (no {first_name} or other
        # unpredictable content) and comfortably fits Telegram's 1024-char
        # photo caption limit, so this is the logo + text in one message.
        await send_logo(
            update.message.reply_photo,
            caption=msg.LANGUAGE_PICKER_PROMPT,
            reply_markup=build_language_picker_keyboard()
        )
        return

    # No logo here - it's shown exactly once, on the language-picker
    # message above, not on every subsequent /start from an already-set-up
    # user. start_text embeds {first_name} (genuinely user-controlled) -
    # stays plain, no parse_mode, same reasoning as elsewhere this string
    # is used.
    await call_with_retry(
        update.message.reply_text,
        msg.start_text(lang, user.first_name),
        reply_markup=build_shortcuts_keyboard(lang)
    )


def main():
    setup_logging()

    # Initialize the database
    init_database()

    # Create the Telegram application.
    # By default python-telegram-bot processes updates one at a time,
    # globally, across ALL users - a single long-running job (transcription
    # can take minutes) would block every other user from getting so much
    # as a /start response. concurrent_updates lets a few users be served in
    # parallel; it's a flat global limit with no per-chat ordering guarantee,
    # so the per-user busy-guard in link_handler.py is what actually keeps a
    # single user's own overlapping requests from corrupting shared state.
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(60)
        .write_timeout(300)
        .connect_timeout(60)
        .pool_timeout(60)
        .concurrent_updates(4)
        .post_init(post_init)
        .build()
    )

    # Register commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    # Interface-language selection is its own callback namespace (setlang_*),
    # kept completely separate from the export/history callbacks handled by
    # the catch-all handler below - registered first so it takes priority
    # for matching callback_data.
    application.add_handler(CallbackQueryHandler(set_language_callback, pattern="^setlang_"))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    logger.info("Bot is starting...")

    # Start receiving Telegram messages
    application.run_polling()


if __name__ == "__main__":
    main()

import random
from datetime import datetime
from importlib import import_module

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "ru", "ar", "uz")

_LOCALES = {code: import_module(f"locales.{code}") for code in SUPPORTED_LANGUAGES}

# Platform brand names aren't translated (standard localization practice),
# so their emoji-only lookup for history labels stays global too.
PLATFORM_EMOJIS = {"youtube": "🎥", "instagram": "📸", "twitter": "✖️", "tiktok": "🎵"}

# Flags shown on the interface-language picker.
LANGUAGE_FLAGS = {"uz": "🇺🇿", "en": "🇬🇧", "ru": "🇷🇺", "ar": "🇸🇦"}

# Shown before we know the user's interface language (first /start, or
# /language) - deliberately not localized, since we don't yet know which
# language to show it in. Not put in a locale file since it's identical
# regardless of chosen language. The greeting line stacks a short "hi" in
# all 4 languages (mirroring the prompt's own style below it) so the very
# first thing a new user sees is warm rather than a cold, functional
# question with no personality at all.
LANGUAGE_PICKER_PROMPT = (
    "👋 Hey there! / Привет! / أهلاً! / Salom!\n\n"
    "Which language should I use? / На каком языке говорить? / "
    "ما اللغة التي تفضلها؟ / Qaysi tilda gaplashaylik?"
)

# Telegram inline button labels get cramped fast - keep the title short
# enough to stay readable alongside the emoji and a trailing ellipsis.
MAX_HISTORY_TITLE_LENGTH = 40


def _locale(lang):
    return _LOCALES.get(lang, _LOCALES[DEFAULT_LANGUAGE])


def t(lang, key, **kwargs):
    """
    Generic accessor for plain-string locale messages. Falls back to
    English (and then a visible placeholder) rather than crashing or
    silently showing nothing if a key is ever missing for a language.
    """

    locale = _locale(lang)
    template = getattr(locale, key, None)

    if template is None:
        template = getattr(_LOCALES[DEFAULT_LANGUAGE], key, f"[[missing:{key}]]")

    return template.format(**kwargs) if kwargs else template


def language_native_name(code: str) -> str:
    """Each language's own name for itself, e.g. 'Русский' - used for the language picker buttons."""
    return _locale(code).NATIVE_NAME


# Fixed order for Telegram's chat menu button command list - matches the
# CommandHandler registration order in main.py.
COMMAND_ORDER = ("start", "help", "cancel", "history", "language")


def command_descriptions(lang):
    """(command, description) pairs for setMyCommands, in COMMAND_ORDER."""
    locale = _locale(lang)
    return [(name, locale.COMMAND_DESCRIPTIONS[name]) for name in COMMAND_ORDER]


def shortcut_labels(lang):
    """(help, history, language) button labels for the persistent reply keyboard, in that order."""
    locale = _locale(lang)
    return (locale.SHORTCUT_HELP, locale.SHORTCUT_HISTORY, locale.SHORTCUT_LANGUAGE)


# Reverse lookup: exact button label (in ANY supported language) -> command
# name. Built once at import time, checked against ALL 4 languages rather
# than just the user's own current one - the persistent keyboard is only
# re-sent (and so only visibly updates) at specific moments (a language
# switch, /start), so a client could in principle still be showing a
# previous language's labels for a moment; checking every language's set is
# cheap (12 exact-string comparisons) and removes any dependency on that
# timing being perfect.
_SHORTCUT_LOOKUP = {}
for _lang_code in SUPPORTED_LANGUAGES:
    _help_label, _history_label, _language_label = shortcut_labels(_lang_code)
    _SHORTCUT_LOOKUP[_help_label] = "help"
    _SHORTCUT_LOOKUP[_history_label] = "history"
    _SHORTCUT_LOOKUP[_language_label] = "language"


def match_shortcut(text: str):
    """
    Returns "help", "history", or "language" if `text` is an EXACT match
    for one of the persistent keyboard's button labels in any supported
    language, otherwise None. Exact-match only (no substring/casefold) -
    these labels are specific emoji+word combinations, not generic text a
    real link or transcript-adjacent message would ever coincidentally match.
    """
    return _SHORTCUT_LOOKUP.get(text)


def start_text(lang, first_name: str) -> str:
    return _locale(lang).START_TEXT.format(first_name=first_name)


def welcome_text(lang, first_name: str) -> str:
    """
    Shown once, the first time a user ever picks a language (via /start's
    picker or /language if that happens to be their first interaction) -
    distinct from LANGUAGE_CHANGED, which is the short confirmation shown
    every other time someone switches languages via /language.
    """
    return _locale(lang).LANGUAGE_ONBOARDING.format(first_name=first_name)


def downloading_message(lang, platform: str) -> str:
    return random.choice(_locale(lang).DOWNLOADING).format(platform=platform)


def extracting_audio_message(lang) -> str:
    return random.choice(_locale(lang).EXTRACTING_AUDIO)


def transcribing_message(lang) -> str:
    return random.choice(_locale(lang).TRANSCRIBING)


def cleaning_message(lang) -> str:
    return random.choice(_locale(lang).CLEANING)


def target_language_name(lang, target_code: str) -> str:
    locale = _locale(lang)
    return locale.TARGET_LANGUAGE_NAMES.get(target_code, locale.UNKNOWN_LANGUAGE)


def export_ready_caption(lang, file_format: str) -> str:
    """
    file_format: 'pdf' or 'text'. Safe to bold {file_format} here - it comes
    from a controlled dict ("PDF"/"text file"), never from the transcript
    content itself.
    """

    locale = _locale(lang)
    format_name = locale.FILE_FORMAT_PDF if file_format == "pdf" else locale.FILE_FORMAT_TEXT

    return locale.EXPORT_READY_CAPTION.format(label=locale.EXPORT_LABEL_TRANSCRIPT, file_format=format_name)


def platform_label(lang, platform: str) -> str:
    return _locale(lang).PLATFORM_LABELS.get(platform, platform.title())


def _truncate_title(title: str) -> str:
    if len(title) <= MAX_HISTORY_TITLE_LENGTH:
        return title
    return title[:MAX_HISTORY_TITLE_LENGTH].rstrip() + "..."


def history_entry_label(lang, platform: str, title, target_code: str, short_date: str) -> str:
    """
    Prioritize the video's title (what actually distinguishes one entry
    from another) - fall back to the old platform/language/date format for
    entries saved before titles were tracked.
    """

    if title:
        emoji = PLATFORM_EMOJIS.get(platform, "🔗")
        return f"{emoji} {_truncate_title(title)}"

    language = target_language_name(lang, target_code)
    return f"{platform_label(lang, platform)} • {language} • {short_date}"


def history_selected_info(lang, title, platform: str, target_code: str, short_date: str) -> str:
    """The fuller platform/language/date context, shown once an entry is reopened."""

    language = target_language_name(lang, target_code)
    meta = f"{platform_label(lang, platform)} • {language} • {short_date}"

    return f"{title}\n{meta}" if title else meta


def format_short_date(lang, created_at: str) -> str:
    try:
        dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return created_at

    month = _locale(lang).MONTH_ABBREVIATIONS[dt.month - 1]
    return f"{month} {dt.day}"

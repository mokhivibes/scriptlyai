from utils.rich_text import DYNAMIC
from utils.platform_emoji import YOUTUBE, INSTAGRAM, TIKTOK, FACEBOOK, X_TWITTER

NATIVE_NAME = "Русский"

# See en.py's _PLATFORM_LIST_PARTS for what this does and why.
_PLATFORM_LIST_PARTS = [
    ("🎥", YOUTUBE), (" YouTube, ", False),
    ("📸", INSTAGRAM), (" Instagram, ", False),
    ("🎵", TIKTOK), (" TikTok, ", False),
    ("📘", FACEBOOK), (" Facebook или ", False),
    ("✖️", X_TWITTER), (" X/Twitter", False),
]

LANGUAGE_CHANGED = (
    "Готово — теперь буду говорить с тобой *по-русски*!\n"
    "Присылай ссылку, чтобы начать, или набери /help, чтобы узнать больше."
)

# Shown once, the first time a user ever picks a language - see en.py's
# LANGUAGE_ONBOARDING_PARTS for why this is parts-based (utils/rich_text.py)
# rather than a Markdown string - DYNAMIC/{first_name} is genuinely
# user-controlled, and entity-based bold is immune to that in a way
# Markdown syntax scanning is not.
LANGUAGE_ONBOARDING_PARTS = [
    ("Привет, ", False),
    (DYNAMIC, False),
    ("! 👋 Отлично, буду говорить с тобой ", False),
    ("по-русски", True),
    ("!\n\nПросто пришли мне ссылку — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — я ", False),
    ("расшифрую и приведу текст в порядок", True),
    (".\n\n📄 Нужна копия?\n\nСделаю ", False),
    ("PDF", True),
    (" или ", False),
    ("текстовый файл", True),
    ("!\n\nПрисылай ссылку, чтобы начать, или набери ", False),
    ("/help", True),
    (", чтобы узнать больше!", False),
]

# START_TEXT_PARTS - see LANGUAGE_ONBOARDING_PARTS above for why this is
# parts-based rather than a Markdown string.
START_TEXT_PARTS = [
    ("Привет, ", False),
    (DYNAMIC, False),
    ("! 👋 Я ", False),
    ("ScriptlyAI", True),
    ("!\n\nПрисылай мне ссылку на видео — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — расшифрую, что там говорят, и приведу ", False),
    ("текст в порядок", True),
    (".\n\n📄 Нужна копия?\n\nМогу сделать ", False),
    ("PDF", True),
    (" или ", False),
    ("текстовый файл", True),
    ("!\n\nНе понимаешь, как это работает?\n\nПросто набери ", False),
    ("/help", True),
    ("!", False),
]
# HELP_TEXT_PARTS - see en.py's HELP_TEXT_PARTS comment for why this is
# parts-based rather than a plain Markdown string.
HELP_TEXT_PARTS = [
    ("Присылай ссылку на ", False),
    *_PLATFORM_LIST_PARTS,
    (" — я прослушаю, всё запишу и отдам тебе в чистом виде.\nНужна "
     "копия? Могу сделать ", False),
    ("PDF", True),
    (" или ", False),
    ("текстовый файл", True),
    (". Лучше всего работаю с речью — с песнями может быть медленнее и "
     "не так точно.\n\n", False),
    ("/history", True),
    (" — посмотреть прошлые расшифровки. ", False),
    ("/language", True),
    (" — сменить язык общения. ", False),
    ("/cancel", True),
    (" — начать заново. ", False),
    ("/start", True),
    (" — поздороваться ещё раз.", False),
]

DOWNLOADING = [
    "📥 Забираю аудио по твоей ссылке с *{platform}*...",
    "📥 Уже качаю с *{platform}*, погоди немного.",
    "📥 Тяну аудио с *{platform}*, секунду...",
]
EXTRACTING_AUDIO = [
    "✂️ Достаю звук из видео...",
    "🎬 Отделяю звук от видео...",
    "✂️ Готовлю аудио, чтобы прослушать...",
]
TRANSCRIBING = [
    "👂 Внимательно вслушиваюсь в каждое слово...",
    "✍️ Превращаю звук в текст...",
    "✍️ Записываю всё, что сказано...",
]

TRANSCRIBING_UZBEK_FALLBACK = (
    "🇺🇿 Похоже, это узбекский — переключаюсь на *специальную модель* для "
    "большей точности. На длинных роликах это может занять пару минут, "
    "спасибо за терпение!"
)

CLEANING = [
    "✨ Привожу расшифровку в порядок...",
    "✨ Сглаживаю шероховатости...",
    "✨ Навожу лоск на текст...",
]

TRANSCRIPT_HEADER = "Вот полная расшифровка, *уже причёсанная*:"
AUDIO_CAPTION = "Вот аудио, которое я достал 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 Текстовый файл"
EXPORT_PROMPT = "Хочешь сохранить копию? Выбери формат ниже:"
EXPORT_FAILED = "Хм, файл не получилось собрать. Попробуем ещё раз?"

TRANSLATE_BUTTON = "🌐 Перевести"
SUMMARIZE_BUTTON = "🔍 Обобщить"
TRANSLATE_PICKER_PROMPT = "На какой язык перевести?"
TRANSLATING = "🌐 Перевожу..."
TRANSLATION_HEADER = "Вот перевод:"
TRANSLATION_FAILED = "Хм, перевод не получился. Попробуем ещё раз?"
TRANSLATION_SAME_LANGUAGE = "Так это же уже на этом языке!"
SUMMARIZING = "🔍 Делаю краткое содержание..."
SUMMARY_HEADER = "Вот краткое содержание:"
SUMMARY_FAILED = "Хм, не получилось собрать краткое содержание. Попробуем ещё раз?"

# See en.py's NEXT_ACTIONS_PROMPT comment for why this is separate from
# EXPORT_PROMPT below.
NEXT_ACTIONS_PROMPT = "Что бы ты хотел(а) сделать с этим?"
# "твоя расшифровка" - EXPORT_LABEL_TRANSCRIPT is feminine, so this must
# agree as "твоя", not the "твой" that fit the old masculine "перевод" label.
EXPORT_READY_CAPTION = "Вот твоя {label} в формате *{file_format}*."
EXPORT_LABEL_TRANSCRIPT = "расшифровка"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "текстовый файл"

NO_LINK_FOUND_PARTS = [
    ("Хм, я не вижу здесь ссылки — пришли ссылку на ", False),
    *_PLATFORM_LIST_PARTS,
    (", и я начну.", False),
]
UNRECOGNIZED_LINK_PARTS = [
    ("Не узнаю эту ссылку. Я работаю с ", False),
    *_PLATFORM_LIST_PARTS,
    (" — попробуй одну из них.", False),
]
UNSUPPORTED_MESSAGE_PARTS = [
    ("Я работаю со ссылками, а не с файлами напрямую — пришли мне ссылку на ", False),
    *_PLATFORM_LIST_PARTS,
    (".", False),
]

ERROR_PRIVATE = (
    "Похоже, это *закрытый* аккаунт или видео — я могу доставать только то, "
    "что в открытом доступе. Если сделаешь его публичным, пришли ссылку ещё раз."
)
ERROR_UNAVAILABLE = (
    "Не могу найти это видео — возможно, оно *удалено*, *закрыто* или "
    "*недоступно* в некоторых регионах. Проверь ссылку и попробуй снова?"
)
ERROR_TIMEOUT = (
    "Загрузка заняла *слишком много времени* — так бывает при медленном "
    "соединении или с большими файлами. Попробуешь ещё раз?"
)
ERROR_NETWORK = "Похоже, произошёл *сетевой сбой*. Пришли ссылку ещё раз, попробуем снова."
ERROR_TOO_LARGE = (
    "Этот файл *слишком большой*, чтобы отправить его через Telegram прямо "
    "сейчас, извини. Может, попробуешь ролик покороче?"
)
ERROR_GENERIC = (
    "*Что-то пошло не так* с моей стороны, и я не смог это обработать. "
    "Проверь, что ссылка рабочая и видео публичное, и попробуй ещё раз?"
)
ERROR_NO_VIDEO = "Похоже, в этом посте нет *видео* — я умею работать только с постами, где оно есть."
ERROR_NO_AUDIO = "Похоже, в этом видео нет *звука* — я умею работать только с видео, где есть звук."

NO_TRANSCRIPT_SAVED = "У меня больше нет этой расшифровки — пришли ссылку ещё раз, и начнём заново."
STILL_WORKING = "*Ещё работаю* над прошлым запросом — дай мне немного времени его закончить!"

LONG_CONTENT_WARNING = (
    "Похоже, это что-то *подлиннее* (~{minutes} мин) — расшифровка может "
    "занять несколько минут, а для песен результат менее надёжен, чем для "
    "речи. Продолжаем?"
)
CONFIRM_YES_BUTTON = "✅ Да, давай"
CONFIRM_NO_BUTTON = "❌ Отмена"
PROCESSING_CANCELLED = "Хорошо, *отменил*. Присылай другую ссылку, когда будешь готов(а)."

CANCEL_HAD_DATA = (
    "Готово, всё *очищено*! То, что я держал, теперь удалено. Присылай "
    "новую ссылку, когда будешь готов(а).\n\n"
    "_(Кстати: если что-то ещё обрабатывается в фоне, может прийти ещё одно "
    "сообщение от этого процесса — просто не обращай внимания.)_"
)
CANCEL_NOTHING = "*Отменять пока нечего* — я просто жду. Присылай ссылку, когда будешь готов(а)."

HISTORY_HEADER = "Вот твои последние расшифровки — нажми на любую, чтобы открыть снова:"
HISTORY_EMPTY = "У тебя пока нет расшифровок — пришли ссылку на *YouTube* или *Instagram*, и она появится здесь в следующий раз."
HISTORY_NOT_FOUND = "Хм, не могу найти эту запись — возможно, она устарела или уже удалена. Попробуй /history ещё раз."

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
    "facebook": "📘 Facebook",
}

TARGET_LANGUAGE_NAMES = {
    "en": "английский",
    "ru": "русский",
    "ar": "арабский",
    "uz": "узбекский",
}
UNKNOWN_LANGUAGE = "неизвестный"

MONTH_ABBREVIATIONS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]

# Labels for the persistent reply-keyboard shortcuts - see en.py for the
# full rationale (friendly text + emoji instead of raw "/help" etc.).
SHORTCUT_HELP = "❓ Помощь"
SHORTCUT_HISTORY = "📜 История"
SHORTCUT_LANGUAGE = "🌍 Язык"

# Shown in Telegram's chat menu button (the "/" icon next to the text
# input) - order matches the command list everywhere else in the bot.
COMMAND_DESCRIPTIONS = {
    "start": "Поздороваться и начать",
    "help": "Что я умею",
    "cancel": "Начать заново",
    "history": "Прошлые расшифровки",
    "language": "Сменить язык общения",
}

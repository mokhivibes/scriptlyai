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

# See en.py's _FEATURE_LIST_PARTS for what this does and why.
# Translate is deliberately left out here - see TRANSLATION_ENABLED in
# handlers/link_handler.py for why; don't advertise a feature that's
# currently hidden from the button menu.
_FEATURE_LIST_PARTS = [
    ("✍️ ", False), ("Расшифровка", True), (" — превращаю сказанное в чистый, читаемый текст\n", False),
    ("🔍 ", False), ("Краткое содержание", True), (" — если нужна суть\n", False),
    ("📄 ", False), ("Экспорт", True), (" — сохраню как PDF или текстовый файл\n", False),
    ("📋 ", False), ("Копирование", True), (" — скопируй текст одним нажатием", False),
]

LANGUAGE_CHANGED = (
    "Готово — теперь буду говорить с тобой 🇷🇺 *по-русски*!\n"
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
    ("! 👋 Отлично, буду говорить с тобой 🇷🇺 ", False),
    ("по-русски", True),
    ("!\n\nПришли мне ссылку — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — и вот что я умею:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nПрисылай ссылку, чтобы начать, или набери ", False),
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
    (" — и вот что я умею:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nНе понимаешь, как это работает?\n\nПросто набери ", False),
    ("/help", True),
    ("!", False),
]
# HELP_TEXT_PARTS - see en.py's HELP_TEXT_PARTS comment for why this is
# parts-based rather than a plain Markdown string.
HELP_TEXT_PARTS = [
    ("Присылай мне ссылку — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — и вот что я умею:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nЛучше всего работаю с речью — с песнями может быть медленнее "
     "и не так точно.\n\n", False),
    ("/history", True),
    (" — посмотреть прошлые расшифровки\n", False),
    ("/language", True),
    (" — сменить язык общения\n", False),
    ("/cancel", True),
    (" — начать заново\n", False),
    ("/privacy", True),
    (" — что я храню и как удалить это\n", False),
    ("/feedback", True),
    (" — отправить отзыв или сообщить о проблеме\n", False),
    ("/start", True),
    (" — поздороваться ещё раз", False),
]

# See en.py's DOWNLOADING_TEMPLATES comment for why this is
# templates-with-a-gap rather than a {platform} string substitution.
DOWNLOADING_TEMPLATES = [
    ("📥 Забираю аудио по твоей ссылке с ", "..."),
    ("📥 Уже качаю с ", ", погоди немного."),
    ("📥 Тяну аудио с ", ", секунду..."),
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
    "🇺🇿 Это может быть узбекский (или близкий к нему язык) — уточняю с "
    "помощью *специальной модели* для точности. На длинных роликах это "
    "может занять пару минут, спасибо за терпение!"
)

CLEANING = [
    "✨ Привожу расшифровку в порядок...",
    "✨ Сглаживаю шероховатости...",
    "✨ Навожу лоск на текст...",
]

TRANSCRIPT_HEADER_PARTS = [
    ("Вот полная расшифровка, ", False), ("уже причёсанная", True), (":", False),
]
AUDIO_CAPTION = "Вот аудио, которое я достал 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 Текстовый файл"
EXPORT_PROMPT = "Хочешь сохранить копию? Выбери формат ниже:"
EXPORT_FAILED = "📄 Хм, файл не получилось собрать. _Нажми на кнопку ниже, чтобы попробовать снова._"

TRANSLATE_BUTTON = "🌐 Перевести"
SUMMARIZE_BUTTON = "🔍 Обобщить"
TRANSLATE_PICKER_PROMPT = "На какой язык перевести?"
TRANSLATING = "🌐 Перевожу..."
TRANSLATION_HEADER_PARTS = [("Вот перевод:", False)]
TRANSLATION_FAILED = "🌐 Хм, перевод не получился. _Выбери язык ниже, чтобы попробовать снова._"
TRANSLATION_SAME_LANGUAGE = "Так это же уже на этом языке!"
# Shown only for a translate button tapped from a keyboard that was
# already on screen before TRANSLATION_ENABLED was turned off - see that
# constant's comment in handlers/link_handler.py.
TRANSLATION_UNAVAILABLE = "🌐 Перевод пока недоступен — скоро появится!"
SUMMARIZING = "🔍 Делаю краткое содержание..."
SUMMARY_HEADER_PARTS = [("Вот краткое содержание:", False)]
SUMMARY_FAILED = "🔍 Хм, не получилось собрать краткое содержание. _Нажми на кнопку ниже, чтобы попробовать снова._"

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
    ("С таким файлом я не работаю. Пришли голосовое сообщение, аудио- или видеофайл (до 20 МБ) либо ссылку на ", False),
    *_PLATFORM_LIST_PARTS,
    (".", False),
]

ERROR_PRIVATE = (
    "🔒 Похоже, это *закрытый* аккаунт или видео — я могу доставать только то, "
    "что в открытом доступе. _Если сделаешь его публичным, пришли ссылку ещё раз._"
)
ERROR_UNAVAILABLE = (
    "🚫 Не могу найти это видео — возможно, оно *удалено*, *закрыто* или "
    "*недоступно* в некоторых регионах. _Проверь ссылку и пришли её мне ещё раз._"
)
ERROR_TIMEOUT = (
    "⏱️ Загрузка заняла *слишком много времени* — так бывает при медленном "
    "соединении или с большими файлами. _Пришли ссылку ещё раз, и я попробую снова._"
)
ERROR_NETWORK = "📡 Похоже, произошёл *сетевой сбой*. _Пришли ссылку ещё раз, попробуем снова._"
ERROR_TOO_LARGE = (
    "📦 Этот файл *слишком большой*, чтобы отправить его через Telegram прямо "
    "сейчас, извини. _Пришли ссылку на более короткий ролик._"
)
ERROR_GENERIC = (
    "⚠️ *Что-то пошло не так* с моей стороны, и я не смог это обработать. "
    "_Проверь, что ссылка рабочая и видео публичное, затем пришли её мне ещё раз._"
)
ERROR_NO_VIDEO = "🎬 Похоже, в этом посте нет *видео* — я умею работать только с постами, где оно есть."
ERROR_NO_AUDIO = "🔇 Похоже, в этом видео нет *звука* — я умею работать только с видео, где есть звук."
ERROR_RATE_LIMITED = (
    "⏳ Сейчас у меня *очень много запросов*, и я упёрся в лимит — дело не в "
    "твоей ссылке. _Подожди немного и пришли её снова._"
)

NO_TRANSCRIPT_SAVED = "🗂️ У меня больше нет этой расшифровки — _пришли ссылку ещё раз, и начнём заново._"
DAILY_LIMIT_REACHED = (
    "📅 Ты уже достиг(ла) сегодняшнего *лимита использования* — так я могу "
    "оставаться честным для всех, кто пользуется ботом. _Возвращайся завтра!_"
)
STILL_WORKING = "⚙️ *Ещё работаю* над прошлым запросом — дай мне немного времени его закончить!"

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

# --- /privacy ---
PRIVACY_TEXT = (
    "🔒 *Что я храню*\n\n"
    "• Твой Telegram ID, юзернейм и имя — чтобы узнавать тебя\n"
    "• Выбранный язык интерфейса — чтобы запомнить его\n"
    "• Расшифровки, которые ты получил(а) (платформа, определённый язык, название, дата) — для работы /history\n\n"
    "*Что я НЕ храню*\n\n"
    "• Само видео или аудио — удаляю сразу после обработки, каждый раз\n"
    "• Всё, что ты мне не присылал(а)\n\n"
    "Твои данные никогда не продаются и не передаются. Можешь удалить всё ниже, в любой момент."
)
DELETE_DATA_BUTTON = "🗑 Удалить мои данные"
DELETE_DATA_CONFIRM_PROMPT = (
    "⚠️ Это *безвозвратно* удалит все твои сохранённые расшифровки и сбросит язык интерфейса. "
    "Отменить это будет нельзя. Продолжить?"
)
DELETE_DATA_CONFIRM_YES_BUTTON = "🗑 Да, удалить всё"
DELETE_DATA_DONE = "✅ *Готово* — твои данные удалены. Пришли /start, когда захочешь начать заново."
DELETE_DATA_CANCELLED = "Хорошо, ничего не удалено."

HISTORY_HEADER = "Вот твои последние расшифровки — нажми на любую, чтобы открыть снова:"
# See en.py's _PLATFORM_LIST_PARTS comment for why this is entity-based.
HISTORY_EMPTY_PARTS = [
    ("У тебя пока нет расшифровок — пришли ссылку на ", False),
    ("🎥", YOUTUBE), (" YouTube", True),
    (" или ", False),
    ("📸", INSTAGRAM), (" Instagram", True),
    (", и она появится здесь в следующий раз.", False),
]
HISTORY_NOT_FOUND = "📜 Хм, не могу найти эту запись — возможно, она устарела или уже удалена. _Попробуй /history ещё раз._"

# Direct file uploads (voice note / audio / video sent straight to the bot).
DOWNLOADING_FILE = "📥 *Получаю твой файл…* _минутку._"
FILE_TOO_BIG_TO_DOWNLOAD = (
    "📦 Этот файл *больше 20 МБ*, а Telegram не позволяет мне скачивать такие большие файлы. "
    "_Пришли файл поменьше или ссылку на него._"
)

# Shown with a web-search button when a SHORT non-link text arrives (likely a song name).
LYRICS_HINT = "\n\n🎤 Если это название песни, нажми ниже, чтобы найти текст."
LYRICS_BUTTON = "🎤 Найти текст песни"

# Bot profile texts (shown on the bot's page / before /start) and /feedback.
BOT_DESCRIPTION = "Пришли ссылку или файл — получи чистый текст. 🎬 Вставь ссылку на YouTube, Instagram, TikTok, Facebook или X — либо отправь голосовое, аудио- или видеофайл (до 20 МБ). ✍️ Я расшифрую, приведу в порядок и дам краткое резюме, копирование в одно касание или файл PDF/текст. 🌍 Говорю на English, Русский, العربية и Oʻzbekcha. Нажми Start, чтобы начать."
BOT_SHORT_DESCRIPTION = "Видео, голосовые и аудио → чистый текст за секунды. Резюме, экспорт в PDF, 4 языка."
FEEDBACK_USAGE = "💬 Есть отзыв или нашёл ошибку? Отправь его вместе с командой, например:\n/feedback PDF обрезал последнюю строку"
FEEDBACK_THANKS = "🙏 Спасибо — твой отзыв дошёл до меня."
FEEDBACK_TOO_SOON = "⏳ Подожди минуту, прежде чем отправлять ещё один отзыв."

COPY_BUTTON = "📋 Копировать"
COPY_HINT = "📋 Нажми на текст ниже, чтобы скопировать."

LINK_RECEIVED = "👀 *Получил твою ссылку!* _Проверяю…_"

ERROR_NO_SPEECH = "🔇 Я не услышал в этом *речи* — возможно, там тишина, музыка или шум. _Попробуй запись, где кто-то говорит._"

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
    "facebook": "📘 Facebook",
    "upload": "📎 Файл",
}

TARGET_LANGUAGE_NAMES = {
    "en": "🇬🇧 английский",
    "ru": "🇷🇺 русский",
    "ar": "🇸🇦 арабский",
    "uz": "🇺🇿 узбекский",
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
    "privacy": "Что я храню и как удалить это",
    "feedback": "Отправить отзыв или сообщить о проблеме",
}

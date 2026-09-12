NATIVE_NAME = "Русский"

LANGUAGE_CHANGED = (
    "Готово — теперь буду говорить с тобой *по-русски*!\n"
    "Присылай ссылку, чтобы начать, или набери /help, чтобы узнать больше."
)

# Shown once, the first time a user ever picks a language - a fuller, warm
# greeting rather than the short LANGUAGE_CHANGED confirmation used every
# other time someone switches languages. Deliberately plain text, NOT
# formatted - contains {first_name}, which is genuinely user-controlled
# (a Telegram user can set their name to include a literal * or _), unlike
# every other formatted message in this file, which is 100% developer text.
LANGUAGE_ONBOARDING = (
    "Привет, {first_name}! 👋 Отлично, буду говорить с тобой по-русски.\n\n"
    "Просто пришли мне ссылку — 🎥 YouTube, 📸 Instagram, 🎵 TikTok или "
    "✖️ X/Twitter — я расшифрую и приведу текст в порядок ✨. Нужна "
    "копия? Сделаю PDF или текстовый файл. 📄\n\n"
    "Присылай ссылку, чтобы начать, или набери /help, чтобы узнать больше."
)

# START_TEXT also stays plain (no bold/italic) for the same {first_name}
# reason as LANGUAGE_ONBOARDING above.
START_TEXT = (
    "Привет, {first_name}! 👋 Я ScriptlyAI.\n\n"
    "Присылай мне ссылку на видео — 🎥 YouTube, 📸 Instagram, 🎵 TikTok "
    "или ✖️ X/Twitter пока что — расшифрую, что там говорят, и приведу "
    "текст в порядок. ✨ Нужна копия? Могу сделать PDF или текстовый "
    "файл. 📄\n\n"
    "Не понимаешь, как это работает? Просто набери /help."
)
HELP_TEXT = (
    "Присылай ссылку на *YouTube*, *Instagram*, *TikTok* или *X/Twitter* — я "
    "прослушаю, всё запишу и отдам тебе в чистом виде.\n"
    "Нужна копия? Могу сделать PDF или текстовый файл.\n\n"
    "_Facebook скоро подключу — потерпи!_\n\n"
    "/history — посмотреть прошлые расшифровки. /language — сменить язык "
    "общения. /cancel — начать заново. /start — поздороваться ещё раз."
)

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
CLEANING = [
    "✨ Привожу расшифровку в порядок...",
    "✨ Сглаживаю шероховатости...",
    "✨ Навожу лоск на текст...",
]

TRANSCRIPT_HEADER = "Вот полная расшифровка, уже причёсанная:"
AUDIO_CAPTION = "Вот аудио, которое я достал 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 Текстовый файл"
EXPORT_PROMPT = "Хочешь сохранить копию? Выбери формат ниже:"
EXPORT_FAILED = "Хм, файл не получилось собрать. Попробуем ещё раз?"
# "твоя расшифровка" - EXPORT_LABEL_TRANSCRIPT is feminine, so this must
# agree as "твоя", not the "твой" that fit the old masculine "перевод" label.
EXPORT_READY_CAPTION = "Вот твоя {label} в формате *{file_format}*."
EXPORT_LABEL_TRANSCRIPT = "расшифровка"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "текстовый файл"

NO_LINK_FOUND = "Хм, я не вижу здесь ссылки — пришли ссылку на YouTube, Instagram, TikTok или X/Twitter, и я начну."
UNRECOGNIZED_LINK = (
    "Не узнаю эту ссылку. Я работаю с YouTube, Instagram, TikTok, "
    "Facebook или X/Twitter — попробуй одну из них."
)
FACEBOOK_PLACEHOLDER = "Вижу ссылку на Facebook, но пока не умею с ними работать — скоро научусь!"

ERROR_PRIVATE = (
    "Похоже, это закрытый аккаунт или видео — я могу доставать только то, "
    "что в открытом доступе. Если сделаешь его публичным, пришли ссылку ещё раз."
)
ERROR_UNAVAILABLE = (
    "Не могу найти это видео — возможно, оно удалено, закрыто или "
    "недоступно в некоторых регионах. Проверь ссылку и попробуй снова?"
)
ERROR_TIMEOUT = (
    "Загрузка заняла слишком много времени — так бывает при медленном "
    "соединении или с большими файлами. Попробуешь ещё раз?"
)
ERROR_NETWORK = "Похоже, произошёл сетевой сбой. Пришли ссылку ещё раз, попробуем снова."
ERROR_TOO_LARGE = (
    "Этот файл слишком большой, чтобы отправить его через Telegram прямо "
    "сейчас, извини. Может, попробуешь ролик покороче?"
)
ERROR_GENERIC = (
    "Что-то пошло не так с моей стороны, и я не смог это обработать. "
    "Проверь, что ссылка рабочая и видео публичное, и попробуй ещё раз?"
)
ERROR_NO_VIDEO = "Похоже, в этом посте нет видео — я умею работать только с постами, где оно есть."
ERROR_NO_AUDIO = "Похоже, в этом видео нет звука — я умею работать только с видео, где есть звук."

NO_TRANSCRIPT_SAVED = "У меня больше нет этой расшифровки — пришли ссылку ещё раз, и начнём заново."
STILL_WORKING = "Ещё работаю над прошлым запросом — дай мне немного времени его закончить!"

CANCEL_HAD_DATA = (
    "Готово, всё *очищено*! То, что я держал, теперь удалено. Присылай "
    "новую ссылку, когда будешь готов(а).\n\n"
    "_(Кстати: если что-то ещё обрабатывается в фоне, может прийти ещё одно "
    "сообщение от этого процесса — просто не обращай внимания.)_"
)
CANCEL_NOTHING = "*Отменять пока нечего* — я просто жду. Присылай ссылку, когда будешь готов(а)."

HISTORY_HEADER = "Вот твои последние расшифровки — нажми на любую, чтобы открыть снова:"
HISTORY_EMPTY = "У тебя пока нет расшифровок — пришли ссылку на YouTube или Instagram, и она появится здесь в следующий раз."
HISTORY_NOT_FOUND = "Хм, не могу найти эту запись — возможно, она устарела или уже удалена. Попробуй /history ещё раз."

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
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

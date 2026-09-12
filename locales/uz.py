NATIVE_NAME = "Oʻzbek"

LANGUAGE_CHANGED = (
    "Boʻldi — bundan buyon *oʻzbekcha* gaplashaman!\n"
    "Boshlash uchun havola yuboring, yoki /help deb yozing."
)

# Shown once, the first time a user ever picks a language - a fuller, warm
# greeting rather than the short LANGUAGE_CHANGED confirmation used every
# other time someone switches languages. Deliberately plain text, NOT
# formatted - contains {first_name}, which is genuinely user-controlled
# (a Telegram user can set their name to include a literal * or _), unlike
# every other formatted message in this file, which is 100% developer text.
LANGUAGE_ONBOARDING = (
    "Salom, {first_name}! 👋 Ajoyib! Bundan buyon oʻzbekcha gaplashaman.\n\n"
    "Menga havola yuboring — 🎥 YouTube, 📸 Instagram, 🎵 TikTok yoki ✖️ "
    "X/Twitter — men uni yozib olib, tozalayman ✨. Nusxa kerakmi? PDF "
    "yoki matn fayli qilib beraman. 📄\n\n"
    "Boshlash uchun havola yuboring, yoki /help deb yozing."
)

# START_TEXT also stays plain (no bold/italic) for the same {first_name}
# reason as LANGUAGE_ONBOARDING above.
START_TEXT = (
    "Salom, {first_name}! 👋 Men ScriptlyAI'man.\n\n"
    "Menga video havolasini yuboring — 🎥 YouTube, 📸 Instagram, 🎵 "
    "TikTok yoki ✖️ X/Twitter hozircha — aytilganlarni toza va oʻqilishi "
    "oson matnga aylantirib beraman. ✨ Nusxa kerakmi? PDF yoki matn "
    "fayli qilib beraman. 📄\n\n"
    "Qanday ishlashini bilmayapsizmi? /help deb yozing."
)
HELP_TEXT = (
    "Menga *YouTube*, *Instagram*, *TikTok* yoki *X/Twitter* havolasini "
    "yuboring — men uni tinglab, hammasini yozib olib, toza holda "
    "qaytarib beraman.\n"
    "Nusxa kerakmi? PDF yoki matn fayli qilib bera olaman.\n\n"
    "_Facebook tez orada qoʻshiladi — biroz kuting!_\n\n"
    "/history — oldingi matnlaringizni koʻrish. /language — til "
    "sozlamasini oʻzgartirish. /cancel — bekor qilish va boshidan boshlash. "
    "/start — yana salomlashish."
)

DOWNLOADING = [
    "📥 *{platform}* havolangizdan audio olyapman...",
    "📥 *{platform}*'dan hozir yuklab olyapman...",
    "📥 *{platform}* audiosini tortib olyapman, biroz kuting.",
]
EXTRACTING_AUDIO = [
    "✂️ Audioni hozir ajratyapman...",
    "🎬 Ovozni videodan ajratyapman...",
    "✂️ Audioni tinglashga tayyorlayapman...",
]
TRANSCRIBING = [
    "👂 Har bir soʻzni diqqat bilan tinglayapman...",
    "✍️ Ovozni gaplarga aylantiryapman...",
    "✍️ Aytilganlarni aynan yozib olyapman...",
]
CLEANING = [
    "✨ Matnni tozalayapman...",
    "✨ Notekisliklarni silliqlayapman...",
    "✨ Matnga oxirgi tafsilotlarni qoʻshyapman...",
]

TRANSCRIPT_HEADER = "Mana toza va tayyor toʻliq matn:"
AUDIO_CAPTION = "Mana men ajratib olgan audio 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 Matn fayli"
EXPORT_PROMPT = "Nusxasini saqlab qolmoqchimisiz? Quyidan formatni tanlang:"
EXPORT_FAILED = "Voy, faylni tayyorlay olmadim. Yana urinib koʻramizmi?"
EXPORT_READY_CAPTION = "Mana {label} — *{file_format}* formatida."
EXPORT_LABEL_TRANSCRIPT = "tozalangan matn"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "matn fayli"

NO_LINK_FOUND = "Bu yerda havola koʻrinmayapti — YouTube, Instagram, TikTok yoki X/Twitter havolasini yuboring, boshlaymiz."
UNRECOGNIZED_LINK = (
    "Bu havolani tanimadim. Men YouTube, Instagram, TikTok, Facebook yoki "
    "X/Twitter havolalari bilan ishlayman — shulardan birini sinab koʻring."
)
FACEBOOK_PLACEHOLDER = "Bu Facebook havolasi ekanini koʻryapman, lekin hali ular bilan ishlay olmayman — tez orada boʻladi!"

ERROR_PRIVATE = (
    "Bu yopiq (private) akkaunt yoki video koʻrinyapti — men faqat ochiq "
    "kontent bilan ishlay olaman. Uni ochiq qilsangiz, havolani qayta yuboring."
)
ERROR_UNAVAILABLE = (
    "Bu videoni topa olmadim — balki oʻchirilgan, yopiq yoki baʼzi "
    "hududlarda toʻsilgan boʻlishi mumkin. Havolani tekshirib, qayta "
    "urinib koʻrasizmi?"
)
ERROR_TIMEOUT = (
    "Bu juda uzoq yuklandi — bu sekin internet yoki katta fayl bilan "
    "boʻlishi mumkin. Qayta urinib koʻrasizmi?"
)
ERROR_NETWORK = "Tarmoqda muammo boʻldi shekilli. Havolani qayta yuboring, yana urinib koʻramiz."
ERROR_TOO_LARGE = "Bu fayl hozir Telegram orqali yuborish uchun juda katta, uzr. Balki qisqaroq video sinab koʻrasiz?"
ERROR_GENERIC = (
    "Mening tomonimda nimadir xato ketdi va buni qayta ishlay olmadim. "
    "Havola toʻgʻri va ochiq ekanini tekshirib, yana urinib koʻrasizmi?"
)
ERROR_NO_VIDEO = "Bu postda video yoʻqday koʻrinadi — men faqat video boʻlgan postlar bilan ishlayman."
ERROR_NO_AUDIO = "Bu videoda ovoz yoʻqday koʻrinadi — men faqat ovozi bor videolar bilan ishlayman."

NO_TRANSCRIPT_SAVED = "Bu matn endi mendan yoʻqoldi — havolani qayta yuboring, yangidan boshlaymiz."
STILL_WORKING = "Hali oldingi soʻrovingiz ustida ishlayapman — uni tugatishga biroz vaqt bering!"

CANCEL_HAD_DATA = (
    "Boʻldi, *tozalandi*! Saqlab turgan narsalarim endi yoʻq. Tayyor "
    "boʻlganingizda yangi havola yuboring.\n\n"
    "_(Bir eslatma: agar orqa fonda hali nimadir ishlanayotgan boʻlsa, "
    "undan xabar kelishi mumkin — shunchaki eʼtibor bermang.)_"
)
CANCEL_NOTHING = "*Hozircha bekor qiladigan narsa yoʻq* — men shunchaki kutyapman. Tayyor boʻlganingizda havola yuboring."

HISTORY_HEADER = "Mana oxirgi matnlaringiz — qayta koʻrish uchun birortasini bosing:"
HISTORY_EMPTY = "Hali hech qanday matningiz yoʻq — YouTube yoki Instagram havolasini yuboring, keyingi safar shu yerda paydo boʻladi."
HISTORY_NOT_FOUND = "Buni topa olmadim — balki juda eski yoki oʻchirilgan boʻlishi mumkin. /history buyrugʻini yana sinab koʻring."

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
}

TARGET_LANGUAGE_NAMES = {
    "en": "Ingliz",
    "ru": "Rus",
    "ar": "Arab",
    "uz": "Oʻzbek",
}
UNKNOWN_LANGUAGE = "Nomaʼlum"

MONTH_ABBREVIATIONS = ["Yan", "Fev", "Mar", "Apr", "May", "Iyun", "Iyul", "Avg", "Sen", "Okt", "Noy", "Dek"]

# Labels for the persistent reply-keyboard shortcuts - see en.py for the
# full rationale (friendly text + emoji instead of raw "/help" etc.).
SHORTCUT_HELP = "❓ Yordam"
SHORTCUT_HISTORY = "📜 Tarix"
SHORTCUT_LANGUAGE = "🌍 Til"

# Shown in Telegram's chat menu button (the "/" icon next to the text
# input) - order matches the command list everywhere else in the bot.
COMMAND_DESCRIPTIONS = {
    "start": "Salomlashish va boshlash",
    "help": "Nima qila olaman",
    "cancel": "Bekor qilish va boshidan boshlash",
    "history": "Oldingi matnlarni koʻrish",
    "language": "Tilni oʻzgartirish",
}

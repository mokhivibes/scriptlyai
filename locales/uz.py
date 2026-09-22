from utils.rich_text import DYNAMIC
from utils.platform_emoji import YOUTUBE, INSTAGRAM, TIKTOK, FACEBOOK, X_TWITTER

NATIVE_NAME = "Oʻzbek"

# See en.py's _PLATFORM_LIST_PARTS for what this does and why.
_PLATFORM_LIST_PARTS = [
    ("🎥", YOUTUBE), (" YouTube, ", False),
    ("📸", INSTAGRAM), (" Instagram, ", False),
    ("🎵", TIKTOK), (" TikTok, ", False),
    ("📘", FACEBOOK), (" Facebook yoki ", False),
    ("✖️", X_TWITTER), (" X/Twitter", False),
]

LANGUAGE_CHANGED = (
    "Boʻldi — bundan buyon *oʻzbekcha* gaplashaman!\n"
    "Boshlash uchun havola yuboring, yoki /help deb yozing."
)

# Shown once, the first time a user ever picks a language - see en.py's
# LANGUAGE_ONBOARDING_PARTS for why this is parts-based (utils/rich_text.py)
# rather than a Markdown string - DYNAMIC/{first_name} is genuinely
# user-controlled, and entity-based bold is immune to that in a way
# Markdown syntax scanning is not.
LANGUAGE_ONBOARDING_PARTS = [
    ("Salom, ", False),
    (DYNAMIC, False),
    ("! 👋 Ajoyib! Bundan buyon ", False),
    ("oʻzbekcha", True),
    (" gaplashaman!\n\nMenga havola yuboring — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — men uni ", False),
    ("yozib olib, tozalayman", True),
    (".\n\n📄 Nusxa kerakmi?\n\n", False),
    ("PDF", True),
    (" yoki matn ", False),
    ("fayli", True),
    (" qilib beraman!\n\nBoshlash uchun havola yuboring, yoki ", False),
    ("/help", True),
    (" deb yozing!", False),
]

# START_TEXT_PARTS - see LANGUAGE_ONBOARDING_PARTS above for why this is
# parts-based rather than a Markdown string.
START_TEXT_PARTS = [
    ("Salom, ", False),
    (DYNAMIC, False),
    ("! 👋 Men ", False),
    ("ScriptlyAI", True),
    ("'man!\n\nMenga video havolasini yuboring — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — aytilganlarni toza va oʻqilishi ", False),
    ("oson matnga", True),
    (" aylantirib beraman.\n\n📄 Nusxa kerakmi?\n\n", False),
    ("PDF", True),
    (" yoki matn ", False),
    ("fayl", True),
    (" formatlarida qilib beraman!\n\nQanday ishlashini "
     "bilmayapsizmi?\n\n", False),
    ("/help", True),
    (" deb yozing!", False),
]
HELP_TEXT = (
    "Menga *YouTube*, *Instagram*, *TikTok*, *Facebook* yoki *X/Twitter* "
    "havolasini yuboring — men uni tinglab, hammasini yozib olib, toza "
    "holda qaytarib beraman.\n"
    "Nusxa kerakmi? PDF yoki matn fayli qilib bera olaman. Nutqli kontent "
    "bilan yaxshiroq ishlayman — qoʻshiqlar bilan sekinroq va aniqligi "
    "pastroq boʻlishi mumkin.\n\n"
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

TRANSCRIBING_UZBEK_FALLBACK = (
    "🇺🇿 Bu oʻzbekcha koʻrinyapti — aniqroq natija uchun *maxsus modelga* "
    "oʻtyapman. Uzunroq videolarda bu bir-ikki daqiqa vaqt olishi mumkin, "
    "sabringiz uchun rahmat!"
)

CLEANING = [
    "✨ Matnni tozalayapman...",
    "✨ Notekisliklarni silliqlayapman...",
    "✨ Matnga oxirgi tafsilotlarni qoʻshyapman...",
]

TRANSCRIPT_HEADER = "Mana *toza va tayyor* toʻliq matn:"
AUDIO_CAPTION = "Mana men ajratib olgan audio 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 Matn fayli"
EXPORT_PROMPT = "Nusxasini saqlab qolmoqchimisiz? Quyidan formatni tanlang:"
EXPORT_FAILED = "Voy, faylni tayyorlay olmadim. Yana urinib koʻramizmi?"
EXPORT_READY_CAPTION = "Mana {label} — *{file_format}* formatida."
EXPORT_LABEL_TRANSCRIPT = "tozalangan matn"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "matn fayli"

NO_LINK_FOUND = "Bu yerda havola koʻrinmayapti — *YouTube*, *Instagram*, *TikTok*, *Facebook* yoki *X/Twitter* havolasini yuboring, boshlaymiz."
UNRECOGNIZED_LINK = (
    "Bu havolani tanimadim. Men *YouTube*, *Instagram*, *TikTok*, "
    "*Facebook* yoki *X/Twitter* havolalari bilan ishlayman — shulardan "
    "birini sinab koʻring."
)

ERROR_PRIVATE = (
    "Bu *yopiq (private)* akkaunt yoki video koʻrinyapti — men faqat ochiq "
    "kontent bilan ishlay olaman. Uni ochiq qilsangiz, havolani qayta yuboring."
)
ERROR_UNAVAILABLE = (
    "Bu videoni topa olmadim — balki *oʻchirilgan*, *yopiq* yoki baʼzi "
    "hududlarda *toʻsilgan* boʻlishi mumkin. Havolani tekshirib, qayta "
    "urinib koʻrasizmi?"
)
ERROR_TIMEOUT = (
    "Bu *juda uzoq* yuklandi — bu sekin internet yoki katta fayl bilan "
    "boʻlishi mumkin. Qayta urinib koʻrasizmi?"
)
ERROR_NETWORK = "*Tarmoqda muammo* boʻldi shekilli. Havolani qayta yuboring, yana urinib koʻramiz."
ERROR_TOO_LARGE = "Bu fayl hozir Telegram orqali yuborish uchun *juda katta*, uzr. Balki qisqaroq video sinab koʻrasiz?"
ERROR_GENERIC = (
    "*Mening tomonimda nimadir xato ketdi* va buni qayta ishlay olmadim. "
    "Havola toʻgʻri va ochiq ekanini tekshirib, yana urinib koʻrasizmi?"
)
ERROR_NO_VIDEO = "Bu postda *video* yoʻqday koʻrinadi — men faqat video boʻlgan postlar bilan ishlayman."
ERROR_NO_AUDIO = "Bu videoda *ovoz* yoʻqday koʻrinadi — men faqat ovozi bor videolar bilan ishlayman."

NO_TRANSCRIPT_SAVED = "Bu matn endi mendan yoʻqoldi — havolani qayta yuboring, yangidan boshlaymiz."
STILL_WORKING = "*Hali oldingi soʻrovingiz* ustida ishlayapman — uni tugatishga biroz vaqt bering!"

LONG_CONTENT_WARNING = (
    "Bu birozroq *uzunroq* koʻrinadi (~{minutes} daqiqa) — matnga aylantirish "
    "bir necha daqiqa vaqt olishi mumkin, qoʻshiqlar uchun natija nutqqa "
    "qaraganda unchalik aniq boʻlmasligi mumkin. Davom etaymi?"
)
CONFIRM_YES_BUTTON = "✅ Ha, davom et"
CONFIRM_NO_BUTTON = "❌ Bekor qilish"
PROCESSING_CANCELLED = "Boʻldi, *bekor qilindi*. Tayyor boʻlganingizda boshqa havola yuboring."

CANCEL_HAD_DATA = (
    "Boʻldi, *tozalandi*! Saqlab turgan narsalarim endi yoʻq. Tayyor "
    "boʻlganingizda yangi havola yuboring.\n\n"
    "_(Bir eslatma: agar orqa fonda hali nimadir ishlanayotgan boʻlsa, "
    "undan xabar kelishi mumkin — shunchaki eʼtibor bermang.)_"
)
CANCEL_NOTHING = "*Hozircha bekor qiladigan narsa yoʻq* — men shunchaki kutyapman. Tayyor boʻlganingizda havola yuboring."

HISTORY_HEADER = "Mana oxirgi matnlaringiz — qayta koʻrish uchun birortasini bosing:"
HISTORY_EMPTY = "Hali hech qanday matningiz yoʻq — *YouTube* yoki *Instagram* havolasini yuboring, keyingi safar shu yerda paydo boʻladi."
HISTORY_NOT_FOUND = "Buni topa olmadim — balki juda eski yoki oʻchirilgan boʻlishi mumkin. /history buyrugʻini yana sinab koʻring."

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
    "facebook": "📘 Facebook",
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

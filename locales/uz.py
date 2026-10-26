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

# See en.py's _FEATURE_LIST_PARTS for what this does and why.
# Translate is deliberately left out here - see TRANSLATION_ENABLED in
# handlers/link_handler.py for why; don't advertise a feature that's
# currently hidden from the button menu.
_FEATURE_LIST_PARTS = [
    ("✍️ ", False), ("Matnga aylantirish", True), (" — aytilganlarni toza, oʻqilishi oson matnga aylantiraman\n", False),
    ("🔍 ", False), ("Qisqartirish", True), (" — qisqacha versiyasi kerak boʻlsa\n", False),
    ("📄 ", False), ("Eksport", True), (" — PDF yoki matn fayli sifatida\n", False),
    ("📋 ", False), ("Nusxalash", True), (" — matnni bir bosishda nusxalang", False),
]

LANGUAGE_CHANGED = (
    "Boʻldi — bundan buyon 🇺🇿 *oʻzbekcha* gaplashaman!\n"
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
    ("! 👋 Ajoyib! Bundan buyon 🇺🇿 ", False),
    ("oʻzbekcha", True),
    (" gaplashaman!\n\nMenga havola yuboring — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — mana men nima qila olaman:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nBoshlash uchun havola yuboring, yoki ", False),
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
    (" — mana men nima qila olaman:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nQanday ishlashini bilmayapsizmi?\n\n", False),
    ("/help", True),
    (" deb yozing!", False),
]
# HELP_TEXT_PARTS - see en.py's HELP_TEXT_PARTS comment for why this is
# parts-based rather than a plain Markdown string.
HELP_TEXT_PARTS = [
    ("Menga havola yuboring — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — mana men nima qila olaman:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nNutqli kontent bilan yaxshiroq ishlayman — qoʻshiqlar bilan "
     "sekinroq va aniqligi pastroq boʻlishi mumkin.\n\n", False),
    ("/history", True),
    (" — oldingi matnlaringizni koʻrish\n", False),
    ("/language", True),
    (" — til sozlamasini oʻzgartirish\n", False),
    ("/cancel", True),
    (" — bekor qilish va boshidan boshlash\n", False),
    ("/privacy", True),
    (" — nimalarni saqlayman va ularni qanday oʻchirish\n", False),
    ("/feedback", True),
    (" — fikr yuborish yoki muammo haqida xabar berish\n", False),
    ("/start", True),
    (" — yana salomlashish", False),
]

# See en.py's DOWNLOADING_TEMPLATES comment for why this is
# templates-with-a-gap rather than a {platform} string substitution.
DOWNLOADING_TEMPLATES = [
    ("📥 ", " havolangizdan audio olyapman..."),
    ("📥 ", "'dan hozir yuklab olyapman..."),
    ("📥 ", " audiosini tortib olyapman, biroz kuting."),
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
    "🇺🇿 Bu oʻzbekcha yoki unga yaqin til boʻlishi mumkin — aniqlik uchun "
    "*maxsus model* bilan tekshiryapman. Uzunroq videolarda bu bir-ikki "
    "daqiqa vaqt olishi mumkin, sabringiz uchun rahmat!"
)

CLEANING = [
    "✨ Matnni tozalayapman...",
    "✨ Notekisliklarni silliqlayapman...",
    "✨ Matnga oxirgi tafsilotlarni qoʻshyapman...",
]

TRANSCRIPT_HEADER_PARTS = [
    ("Mana ", False), ("toza va tayyor", True), (" toʻliq matn:", False),
]
AUDIO_CAPTION = "Mana men ajratib olgan audio 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 Matn fayli"
EXPORT_PROMPT = "Nusxasini saqlab qolmoqchimisiz? Quyidan formatni tanlang:"
EXPORT_FAILED = "📄 Voy, faylni tayyorlay olmadim. _Qayta urinish uchun quyidagi tugmani bosing._"

TRANSLATE_BUTTON = "🌐 Tarjima qilish"
SUMMARIZE_BUTTON = "🔍 Qisqartirish"
TRANSLATE_PICKER_PROMPT = "Qaysi tilga tarjima qilay?"
TRANSLATING = "🌐 Tarjima qilyapman..."
TRANSLATION_HEADER_PARTS = [("Mana tarjima:", False)]
TRANSLATION_FAILED = "🌐 Voy, tarjima chiqmadi. _Qayta urinish uchun quyidan tilni tanlang._"
TRANSLATION_SAME_LANGUAGE = "Bu allaqachon shu tilda-ku!"
# Shown only for a translate button tapped from a keyboard that was
# already on screen before TRANSLATION_ENABLED was turned off - see that
# constant's comment in handlers/link_handler.py.
TRANSLATION_UNAVAILABLE = "🌐 Tarjima hozircha mavjud emas — tez orada qoʻshiladi!"
SUMMARIZING = "🔍 Qisqacha mazmunini tayyorlayapman..."
SUMMARY_HEADER_PARTS = [("Mana qisqacha mazmuni:", False)]
SUMMARY_FAILED = "🔍 Voy, qisqacha mazmunini tayyorlay olmadim. _Qayta urinish uchun quyidagi tugmani bosing._"

# See en.py's NEXT_ACTIONS_PROMPT comment for why this is separate from
# EXPORT_PROMPT below.
NEXT_ACTIONS_PROMPT = "Bu bilan nima qilishni xohlaysiz?"
EXPORT_READY_CAPTION = "Mana {label} — *{file_format}* formatida."
EXPORT_LABEL_TRANSCRIPT = "tozalangan matn"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "matn fayli"

NO_LINK_FOUND_PARTS = [
    ("Bu yerda havola koʻrinmayapti — ", False),
    *_PLATFORM_LIST_PARTS,
    (" havolasini yuboring, boshlaymiz.", False),
]
UNRECOGNIZED_LINK_PARTS = [
    ("Bu havolani tanimadim. Men ", False),
    *_PLATFORM_LIST_PARTS,
    (" havolalari bilan ishlayman — shulardan birini sinab koʻring.", False),
]
UNSUPPORTED_MESSAGE_PARTS = [
    ("Bunday fayl bilan ishlay olmayman. Menga ovozli xabar, audio yoki video fayl (20 MB gacha) yoki ", False),
    *_PLATFORM_LIST_PARTS,
    (" havolasini yuboring.", False),
]

ERROR_PRIVATE = (
    "🔒 Bu *yopiq (private)* akkaunt yoki video koʻrinyapti — men faqat ochiq "
    "kontent bilan ishlay olaman. _Uni ochiq qilsangiz, havolani qayta yuboring._"
)
ERROR_UNAVAILABLE = (
    "🚫 Bu videoni topa olmadim — balki *oʻchirilgan*, *yopiq* yoki baʼzi "
    "hududlarda *toʻsilgan* boʻlishi mumkin. _Havolani tekshirib, menga "
    "qayta yuboring._"
)
ERROR_TIMEOUT = (
    "⏱️ Bu *juda uzoq* yuklandi — bu sekin internet yoki katta fayl bilan "
    "boʻlishi mumkin. _Havolani qayta yuboring, men yana urinib koʻraman._"
)
ERROR_NETWORK = "📡 *Tarmoqda muammo* boʻldi shekilli. _Havolani qayta yuboring, yana urinib koʻramiz._"
ERROR_TOO_LARGE = "📦 Bu fayl hozir Telegram orqali yuborish uchun *juda katta*, uzr. _Qisqaroq video havolasini yuboring._"
ERROR_GENERIC = (
    "⚠️ *Mening tomonimda nimadir xato ketdi* va buni qayta ishlay olmadim. "
    "_Havola toʻgʻri va ochiq ekanini tekshirib, menga qayta yuboring._"
)
ERROR_NO_VIDEO = "🎬 Bu postda *video* yoʻqday koʻrinadi — men faqat video boʻlgan postlar bilan ishlayman."
ERROR_NO_AUDIO = "🔇 Bu videoda *ovoz* yoʻqday koʻrinadi — men faqat ovozi bor videolar bilan ishlayman."
ERROR_RATE_LIMITED = (
    "⏳ Hozir menga *juda koʻp soʻrov* kelyapti va chegaraga yetdim — bu sizning "
    "havolangizga bogʻliq emas. _Bir necha daqiqa kutib, qayta yuboring._"
)

NO_TRANSCRIPT_SAVED = "🗂️ Bu matn endi mendan yoʻqoldi — _havolani qayta yuboring, yangidan boshlaymiz._"
DAILY_LIMIT_REACHED = (
    "📅 Bugungi *foydalanish chegarasiga* yetdingiz — bu botdan foydalanadigan "
    "hammaga adolatli boʻlishi uchun. _Ertaga qaytib keling!_"
)
STILL_WORKING = "⚙️ *Hali oldingi soʻrovingiz* ustida ishlayapman — uni tugatishga biroz vaqt bering!"

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

# --- /privacy ---
PRIVACY_TEXT = (
    "🔒 *Nimalarni saqlayman*\n\n"
    "• Telegram ID, foydalanuvchi nomi va ismingiz — sizni tanish uchun\n"
    "• Tanlangan interfeys tili — keyingi safar eslab qolish uchun\n"
    "• Siz olgan matnlar (platforma, aniqlangan til, sarlavha, sana) — /history ishlashi uchun\n\n"
    "*Nimalarni saqlamayman*\n\n"
    "• Video yoki audio faylning oʻzi — qayta ishlangandan keyin darhol oʻchiriladi (“Matnini olish” tugmasini kutayotgan audio koʻpi bilan bir soatdan keyin oʻchiriladi)\n"
    "• Siz menga yubormagan hech narsa\n\n"
    "*Audiongizni kim qayta ishlaydi*\n\n"
    "• Groq — matnga aylantirish va tozalash\n"
    "• Oʻzbek, qozoq yoki qirgʻiz tiliga oʻxshash audio uchun Google Gemini API ham ishlatiladi — Googleʼning bepul tarifi yuborilgan audiodan oʻz mahsulotlarini yaxshilash uchun foydalanishi mumkin\n\n"
    "Fayl qayta ishlangandan keyin darhol mendan va Googleʼning fayl saqlash joyidan ham oʻchiriladi.\n\n"
    "Maʼlumotlaringiz hech qachon sotilmaydi. Istalgan vaqtda hammasini oʻchirishingiz mumkin."
)
DELETE_DATA_BUTTON = "🗑 Maʼlumotlarimni oʻchirish"
DELETE_DATA_CONFIRM_PROMPT = (
    "⚠️ Bu barcha saqlangan matnlaringizni *butunlay* oʻchiradi va interfeys tilini "
    "qayta tiklaydi. Buni ortga qaytarib boʻlmaydi. Davom etamizmi?"
)
DELETE_DATA_CONFIRM_YES_BUTTON = "🗑 Ha, hammasini oʻchiring"
DELETE_DATA_DONE = "✅ *Tayyor* — maʼlumotlaringiz oʻchirildi. Qaytadan boshlash uchun /start yuboring."
DELETE_DATA_CANCELLED = "Xoʻp, hech narsa oʻchirilmadi."

HISTORY_HEADER = "Mana oxirgi matnlaringiz — qayta koʻrish uchun birortasini bosing:"
# See en.py's _PLATFORM_LIST_PARTS comment for why this is entity-based.
HISTORY_EMPTY_PARTS = [
    ("Hali hech qanday matningiz yoʻq — ", False),
    ("🎥", YOUTUBE), (" YouTube", True),
    (" yoki ", False),
    ("📸", INSTAGRAM), (" Instagram", True),
    (" havolasini yuboring, keyingi safar shu yerda paydo boʻladi.", False),
]
HISTORY_NOT_FOUND = "📜 Buni topa olmadim — balki juda eski yoki oʻchirilgan boʻlishi mumkin. _/history buyrugʻini yana sinab koʻring._"

# Direct file uploads (voice note / audio / video sent straight to the bot).
DOWNLOADING_FILE = "📥 *Faylingizni olyapman…* _bir lahza._"
FILE_TOO_BIG_TO_DOWNLOAD = (
    "📦 Bu fayl *20 MB dan katta*, Telegram menga bunday katta fayllarni yuklab olishga ruxsat bermaydi. "
    "_Kichikroq fayl yoki uning havolasini yuboring._"
)

# Shown with a web-search button when a SHORT non-link text arrives (likely a song name).
LYRICS_HINT = "\n\n🎤 Agar bu qoʻshiq nomi boʻlsa, matnini topish uchun pastdagi tugmani bosing."
LYRICS_BUTTON = "🎤 Qoʻshiq matnini topish"

# Bot profile texts (shown on the bot's page / before /start) and /feedback.
BOT_DESCRIPTION = "Havola yoki fayl yuboring — toza matn oling. 🎬 YouTube, Instagram, TikTok, Facebook yoki X havolasini joylang — yoki ovozli xabar, audio yoki video fayl (20 MB gacha) yuboring. ✍️ Men uni matnga aylantiraman, tartibga solaman va qisqa xulosa, bir bosishda nusxalash yoki PDF/matn fayli beraman. 🌍 English, Русский, العربية va Oʻzbekcha tillarida ishlayman. Boshlash uchun Start tugmasini bosing."
BOT_SHORT_DESCRIPTION = "Video, ovozli xabar va audioni soniyalarda toza matnga aylantiring. Xulosa, PDF eksport, 4 til."
FEEDBACK_USAGE = "💬 Fikringiz bormi yoki xato topdingizmi? Buyruq bilan birga yuboring, masalan:\n/feedback PDF oxirgi qatorni kesib tashladi"
FEEDBACK_THANKS = "🙏 Rahmat — fikringiz menga yetib keldi."
FEEDBACK_TOO_SOON = "⏳ Yana fikr yuborishdan oldin bir daqiqa kuting."

COPY_BUTTON = "📋 Nusxalash"
COPY_HINT = "📋 Nusxalash uchun quyidagi matnga bosing."

LINK_RECEIVED = "👀 *Havolangiz yetib keldi!* _Tekshiryapman…_"

ERROR_NO_SPEECH = "🔇 Bunda hech qanday *nutq* eshitmadim — jim yoki faqat musiqa yoki shovqin boʻlishi mumkin. _Kimdir gapiradigan yozuvni sinab koʻring._"

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
    "facebook": "📘 Facebook",
    "upload": "📎 Fayl",
}

TARGET_LANGUAGE_NAMES = {
    "en": "🇬🇧 Ingliz",
    "ru": "🇷🇺 Rus",
    "ar": "🇸🇦 Arab",
    "uz": "🇺🇿 Oʻzbek",
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
    "privacy": "Nimalarni saqlayman va qanday oʻchirish",
    "feedback": "Fikr yuborish yoki muammo haqida xabar berish",
}

# --- Uzbek alphabet toggle (shown only to Uzbek-interface users on Uzbek results) ---
ALPHABET_TO_NEW_BUTTON = "🔤 Yangi alifbo: ö ğ ş ç"
ALPHABET_TO_OLD_BUTTON = "🔤 Eski alifbo: oʻ gʻ sh ch"
ALPHABET_CHANGED_NEW = "🔤 Yangi alifboga oʻtildi (ö ğ ş ç)"
ALPHABET_CHANGED_OLD = "🔤 Eski alifboga oʻtildi (oʻ gʻ sh ch)"

# --- "Get text" on demand (links: audio first, transcribe only on tap) ---
GET_TEXT_BUTTON = "📝 Matnini olish"
AUDIO_CAPTION_ASK = "Mana men ajratib olgan audio 🎧\n\nMatni ham kerakmi? Quyidagi tugmani bosing 👇"
GET_TEXT_EXPIRED = "⏳ Bu audio endi saqlanmagan (uni faqat bir soat saqlayman). Havolani qayta yuboring."

# --- YouTube refusing the server (expired cookies) ---
YOUTUBE_BLOCKED = "⚠️ YouTube hozir meni bloklayapti, shuning uchun bu havolani yuklab ola olmayapman. Egasiga xabar berdim. Keyinroq urinib koʻring yoki audio yoki videoni fayl sifatida yuboring."

from utils.rich_text import DYNAMIC
from utils.platform_emoji import YOUTUBE, INSTAGRAM, TIKTOK, FACEBOOK, X_TWITTER

NATIVE_NAME = "العربية"

# See en.py's _PLATFORM_LIST_PARTS for what this does and why.
_PLATFORM_LIST_PARTS = [
    ("🎥", YOUTUBE), (" يوتيوب، ", False),
    ("📸", INSTAGRAM), (" إنستغرام، ", False),
    ("🎵", TIKTOK), (" تيك توك، ", False),
    ("📘", FACEBOOK), (" فيسبوك، أو ", False),
    ("✖️", X_TWITTER), (" إكس/تويتر", False),
]

# See en.py's _FEATURE_LIST_PARTS for what this does and why.
# Translate is deliberately left out here - see TRANSLATION_ENABLED in
# handlers/link_handler.py for why; don't advertise a feature that's
# currently hidden from the button menu.
_FEATURE_LIST_PARTS = [
    ("✍️ ", False), ("تفريغ نصي", True), (" — أحوّل ما يُقال إلى نص واضح ومرتب\n", False),
    ("🔍 ", False), ("تلخيص", True), (" — إذا أردت الخلاصة فقط\n", False),
    ("📄 ", False), ("تصدير", True), (" — كملف PDF أو نصي\n", False),
    ("📋 ", False), ("نسخ", True), (" — انسخ النص بنقرة واحدة", False),
]

LANGUAGE_CHANGED = (
    "تمام، من الآن سأتحدث معك 🇸🇦 *بالعربية*!\n"
    "أرسل رابطاً للبدء، أو اكتب /help لمعرفة التفاصيل."
)

# Shown once, the first time a user ever picks a language - see en.py's
# LANGUAGE_ONBOARDING_PARTS for why this is parts-based (utils/rich_text.py)
# rather than a Markdown string - DYNAMIC/{first_name} is genuinely
# user-controlled, and entity-based bold is immune to that in a way
# Markdown syntax scanning is not. Entity offsets work the same
# regardless of RTL - Telegram handles bidi rendering itself.
LANGUAGE_ONBOARDING_PARTS = [
    ("أهلاً ", False),
    (DYNAMIC, False),
    ("! 👋 تمام، من الآن سأتحدث معك 🇸🇦 ", False),
    ("بالعربية", True),
    ("!\n\nأرسل لي رابطاً — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — وإليك ما يمكنني فعله:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nأرسل رابطاً للبدء، أو اكتب ", False),
    ("/help", True),
    (" لمعرفة التفاصيل!", False),
]

# START_TEXT_PARTS - see LANGUAGE_ONBOARDING_PARTS above for why this is
# parts-based rather than a Markdown string.
START_TEXT_PARTS = [
    ("أهلاً ", False),
    (DYNAMIC, False),
    ("! 👋 أنا ", False),
    ("ScriptlyAI", True),
    ("!\n\nأرسل لي رابط فيديو — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — وإليك ما يمكنني فعله:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nلست متأكداً كيف يعمل؟\n\nفقط اكتب ", False),
    ("/help", True),
    ("!", False),
]
# HELP_TEXT_PARTS - see en.py's HELP_TEXT_PARTS comment for why this is
# parts-based rather than a plain Markdown string.
HELP_TEXT_PARTS = [
    ("أرسل لي رابط — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — وإليك ما يمكنني فعله:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nأعمل بشكل أفضل مع الكلام المنطوق — الأغاني قد تستغرق وقتاً "
     "أطول وتكون أقل دقة.\n\n", False),
    ("/history", True),
    (" — لمراجعة النصوص السابقة\n", False),
    ("/language", True),
    (" — لتغيير لغة المحادثة\n", False),
    ("/cancel", True),
    (" — للبدء من جديد\n", False),
    ("/privacy", True),
    (" — ما أخزّنه وكيفية حذفه\n", False),
    ("/feedback", True),
    (" — أرسل ملاحظاتك أو أبلغ عن مشكلة\n", False),
    ("/start", True),
    (" — للترحيب من جديد", False),
]

# See en.py's DOWNLOADING_TEMPLATES comment for why this is
# templates-with-a-gap rather than a {platform} string substitution.
DOWNLOADING_TEMPLATES = [
    ("📥 أجلب الصوت من رابط ", "..."),
    ("📥 جارٍ التحميل من ", " الآن..."),
    ("📥 أحضر صوت ", "، لحظات..."),
]
EXTRACTING_AUDIO = [
    "✂️ أستخرج الصوت الآن...",
    "🎬 أفصل الصوت عن الفيديو...",
    "✂️ أجهّز الصوت للاستماع...",
]
TRANSCRIBING = [
    "👂 أستمع بعناية لكل كلمة...",
    "✍️ أحوّل الصوت إلى جمل...",
    "✍️ أدوّن بالضبط ما قيل...",
]

TRANSCRIBING_UZBEK_FALLBACK = (
    "🇺🇿 قد تكون هذه اللغة الأوزبكية (أو لغة قريبة منها) - أتحقق باستخدام "
    "*نموذج متخصص* لمزيد من الدقة. قد يستغرق هذا دقيقة أو دقيقتين في "
    "المقاطع الأطول، شكراً لصبرك!"
)

CLEANING = [
    "✨ أرتّب النص الآن...",
    "✨ أنعّم الحواف الخشنة في النص...",
    "✨ ألمسة أخيرة على النص...",
]

TRANSCRIPT_HEADER_PARTS = [
    ("إليك النص الكامل، ", False), ("منظّماً وجاهزاً", True), (":", False),
]
AUDIO_CAPTION = "إليك الصوت الذي استخرجته 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 ملف نصي"
EXPORT_PROMPT = "تريد نسخة تحتفظ بها؟ اختر صيغة أدناه:"
EXPORT_FAILED = "📄 للأسف لم أتمكن من تجهيز الملف. _اضغط الزر أدناه لتجربة ذلك مرة أخرى._"

TRANSLATE_BUTTON = "🌐 ترجم"
SUMMARIZE_BUTTON = "🔍 لخّص"
TRANSLATE_PICKER_PROMPT = "إلى أي لغة أترجمه؟"
TRANSLATING = "🌐 أترجم الآن..."
TRANSLATION_HEADER_PARTS = [("إليك الترجمة:", False)]
TRANSLATION_FAILED = "🌐 للأسف لم تنجح الترجمة. _اختر لغة أدناه لتجربة ذلك مرة أخرى._"
TRANSLATION_SAME_LANGUAGE = "هذا أصلاً بهذه اللغة!"
# Shown only for a translate button tapped from a keyboard that was
# already on screen before TRANSLATION_ENABLED was turned off - see that
# constant's comment in handlers/link_handler.py.
TRANSLATION_UNAVAILABLE = "🌐 الترجمة غير متاحة بعد — ستُضاف قريباً!"
SUMMARIZING = "🔍 ألخّص الآن..."
SUMMARY_HEADER_PARTS = [("إليك ملخصاً سريعاً:", False)]
SUMMARY_FAILED = "🔍 للأسف لم أتمكن من تجهيز الملخص. _اضغط الزر أدناه لتجربة ذلك مرة أخرى._"

# See en.py's NEXT_ACTIONS_PROMPT comment for why this is separate from
# EXPORT_PROMPT below.
NEXT_ACTIONS_PROMPT = "ماذا تريد أن تفعل بهذا؟"
EXPORT_READY_CAPTION = "إليك {label} بصيغة *{file_format}*."
EXPORT_LABEL_TRANSCRIPT = "النص المنظّم"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "ملف نصي"

NO_LINK_FOUND_PARTS = [
    ("لا أرى رابطاً هنا — أرسل رابط ", False),
    *_PLATFORM_LIST_PARTS,
    (" وسأبدأ العمل.", False),
]
UNRECOGNIZED_LINK_PARTS = [
    ("لا أتعرّف على هذا الرابط. أعمل مع روابط ", False),
    *_PLATFORM_LIST_PARTS,
    (" — جرّب أحدها.", False),
]
UNSUPPORTED_MESSAGE_PARTS = [
    ("لا أستطيع التعامل مع هذا النوع من الملفات. أرسل لي رسالة صوتية أو ملف صوت أو فيديو (حتى 20 ميجابايت)، أو رابط ", False),
    *_PLATFORM_LIST_PARTS,
    (".", False),
]

ERROR_PRIVATE = (
    "🔒 يبدو أن هذا حساب أو فيديو *خاص* — يمكنني فقط الوصول إلى المحتوى العام. "
    "_إذا جعلته عاماً، أرسل الرابط مرة أخرى._"
)
ERROR_UNAVAILABLE = (
    "🚫 لم أتمكن من العثور على هذا الفيديو — ربما تم *حذفه* أو أنه *خاص* أو "
    "*محظور* في بعض المناطق. _تأكد من الرابط ثم أرسله لي مرة أخرى._"
)
ERROR_TIMEOUT = (
    "⏱️ استغرق هذا *وقتاً طويلاً* للتحميل — يحدث هذا أحياناً مع اتصال بطيء أو "
    "ملف كبير. _أرسل الرابط مرة أخرى وسأحاول من جديد._"
)
ERROR_NETWORK = "📡 يبدو أن هناك *مشكلة في الشبكة*. _أرسل الرابط مرة أخرى ولنجرب مجدداً._"
ERROR_TOO_LARGE = "📦 هذا الملف *كبير جداً* على إرساله عبر تيليجرام الآن، آسف على ذلك. _أرسل رابط مقطع أقصر._"
ERROR_GENERIC = (
    "⚠️ *حدث خطأ ما* من جهتي ولم أتمكن من معالجة هذا. _تأكد أن الرابط صحيح "
    "وعام، ثم أرسله لي مرة أخرى._"
)
ERROR_NO_VIDEO = "🎬 يبدو أن هذا المنشور لا يحتوي على *فيديو* — أعمل فقط مع المنشورات التي تحتوي على واحد."
ERROR_NO_AUDIO = "🔇 يبدو أن هذا الفيديو لا يحتوي على *صوت* — أعمل فقط مع الفيديوهات التي تحتوي على صوت."
ERROR_RATE_LIMITED = (
    "⏳ لدي *طلبات كثيرة جداً* الآن ووصلت إلى الحد الأقصى — الأمر لا علاقة له "
    "برابطك. _الرجاء الانتظار بضع دقائق ثم إرساله مرة أخرى._"
)

NO_TRANSCRIPT_SAVED = "🗂️ لم يعد لدي هذا النص — _أرسل الرابط مرة أخرى ولنبدأ من جديد._"
DAILY_LIMIT_REACHED = (
    "📅 لقد وصلت إلى *الحد اليومي* للاستخدام حتى أبقي الأمر عادلاً لكل من "
    "يستخدم البوت. _عد غداً وسأكون جاهزاً!_"
)
STILL_WORKING = "⚙️ *ما زلت أعمل* على طلبك السابق — امنحني لحظة لإنهائه أولاً!"

LONG_CONTENT_WARNING = (
    "يبدو أن هذا مقطع *أطول* (~{minutes} دقيقة) — قد تستغرق النسخة عدة دقائق، "
    "والنتائج أقل دقة مع الأغاني منها مع الكلام. هل أكمل؟"
)
CONFIRM_YES_BUTTON = "✅ نعم، أكمل"
CONFIRM_NO_BUTTON = "❌ إلغاء"
PROCESSING_CANCELLED = "تمام، *ألغيت الأمر*. أرسل رابطاً آخر متى كنت مستعداً."

CANCEL_HAD_DATA = (
    "تم، كل شيء *ألغيته*! أي شيء كنت أحتفظ به اختفى الآن. أرسل رابطاً "
    "جديداً متى شئت.\n\n"
    "_(ملاحظة سريعة: إذا كان هناك شيء لا يزال يُعالج في الخلفية، فقد "
    "تصلك رسالة منه لاحقاً — تجاهلها فقط.)_"
)
CANCEL_NOTHING = "*لا يوجد شيء لإلغائه* الآن — أنا فقط بالانتظار. أرسل رابطاً متى كنت مستعداً."

# --- /privacy ---
PRIVACY_TEXT = (
    "🔒 *ما أخزّنه*\n\n"
    "• معرّف تيليجرام واسم المستخدم والاسم الأول — لأتعرّف عليك\n"
    "• لغة الواجهة التي اخترتها — لأتذكرها في المرة القادمة\n"
    "• النصوص التي أنشأتها (المنصة، اللغة المكتشفة، العنوان، التاريخ) — ليعمل /history\n\n"
    "*ما لا أخزّنه*\n\n"
    "• ملف الفيديو أو الصوت نفسه — يُحذف فور المعالجة، في كل مرة\n"
    "• أي شيء لم ترسله لي\n\n"
    "*من يعالج صوتك*\n\n"
    "• Groq — التفريغ النصي وتنقيح النص\n"
    "• وللصوت الذي يبدو أوزبكياً أو كازاخياً أو قيرغيزياً، تُستخدم أيضاً واجهة Gemini من Google — وقد تستخدم الطبقة المجانية من Google الصوت المُرسَل لتحسين منتجاتها\n\n"
    "يُحذف الملف من عندي فور المعالجة، ومن مخزن ملفات Google أيضاً.\n\n"
    "بياناتك لا تُباع أبداً. يمكنك حذف كل شيء أدناه، في أي وقت."
)
DELETE_DATA_BUTTON = "🗑 احذف بياناتي"
DELETE_DATA_CONFIRM_PROMPT = (
    "⚠️ سيؤدي هذا إلى حذف *دائم* لجميع نصوصك المحفوظة وإعادة ضبط لغة الواجهة. "
    "لا يمكن التراجع عن هذا. هل تريد المتابعة؟"
)
DELETE_DATA_CONFIRM_YES_BUTTON = "🗑 نعم، احذف كل شيء"
DELETE_DATA_DONE = "✅ *تم* — تم حذف بياناتك. أرسل /start متى أردت البدء من جديد."
DELETE_DATA_CANCELLED = "حسناً، لم يُحذف شيء."

HISTORY_HEADER = "إليك آخر نصوصك — اضغط على أي منها لعرضه مرة أخرى:"
# See en.py's _PLATFORM_LIST_PARTS comment for why this is entity-based.
HISTORY_EMPTY_PARTS = [
    ("ليس لديك أي نصوص بعد — أرسل رابط ", False),
    ("🎥", YOUTUBE), (" يوتيوب", True),
    (" أو ", False),
    ("📸", INSTAGRAM), (" إنستغرام", True),
    (" وسيظهر هنا في المرة القادمة.", False),
]
HISTORY_NOT_FOUND = "📜 لم أتمكن من العثور على هذا بعد الآن — ربما قديم جداً أو تم حذفه. _جرّب /history مرة أخرى._"

# Direct file uploads (voice note / audio / video sent straight to the bot).
DOWNLOADING_FILE = "📥 *جارٍ استلام ملفك…* _لحظات من فضلك._"
FILE_TOO_BIG_TO_DOWNLOAD = (
    "📦 هذا الملف *أكبر من 20 ميجابايت*، ولا يسمح لي تيليجرام بتنزيل ملفات بهذا الحجم. "
    "_أرسل ملفاً أصغر أو أرسل رابطه بدلاً من ذلك._"
)

# Shown with a web-search button when a SHORT non-link text arrives (likely a song name).
LYRICS_HINT = "\n\n🎤 إذا كان هذا اسم أغنية، اضغط أدناه للبحث عن كلماتها."
LYRICS_BUTTON = "🎤 ابحث عن الكلمات"

# Bot profile texts (shown on the bot's page / before /start) and /feedback.
BOT_DESCRIPTION = "أرسل رابطاً أو ملفاً واحصل على نص نظيف. 🎬 الصق رابط YouTube أو Instagram أو TikTok أو Facebook أو X — أو أرسل رسالة صوتية أو ملف صوت أو فيديو (حتى 20 ميجابايت). ✍️ أفرّغه وأرتّبه وأعطيك ملخصاً قصيراً ونسخاً بنقرة واحدة أو ملف PDF أو نصي. 🌍 أتحدث English وРусский والعربية وOʻzbekcha. اضغط Start للبدء."
BOT_SHORT_DESCRIPTION = "حوّل الفيديو والرسائل الصوتية والصوت إلى نص نظيف في ثوانٍ. ملخصات وتصدير PDF وأربع لغات."
FEEDBACK_USAGE = "💬 لديك ملاحظة أو وجدت خطأ؟ أرسلها مع الأمر، مثل:\n/feedback ملف PDF قطع آخر سطر"
FEEDBACK_THANKS = "🙏 شكراً — وصلتني ملاحظتك."
FEEDBACK_TOO_SOON = "⏳ انتظر دقيقة قبل إرسال ملاحظة أخرى."

COPY_BUTTON = "📋 نسخ"
COPY_HINT = "📋 اضغط على النص أدناه لنسخه."

LINK_RECEIVED = "👀 *وصلني رابطك!* _أتحقق منه الآن…_"

ERROR_NO_SPEECH = "🔇 لم أسمع أي *كلام* في هذا — ربما هو صامت أو يحتوي على موسيقى أو ضوضاء فقط. _جرّب مقطعاً يتحدث فيه شخص._"

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
    "facebook": "📘 فيسبوك",
    "upload": "📎 ملف",
}

TARGET_LANGUAGE_NAMES = {
    "en": "🇬🇧 الإنجليزية",
    "ru": "🇷🇺 الروسية",
    "ar": "🇸🇦 العربية",
    "uz": "🇺🇿 الأوزبكية",
}
UNKNOWN_LANGUAGE = "غير معروفة"

MONTH_ABBREVIATIONS = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]

# Labels for the persistent reply-keyboard shortcuts - see en.py for the
# full rationale (friendly text + emoji instead of raw "/help" etc.).
SHORTCUT_HELP = "❓ مساعدة"
SHORTCUT_HISTORY = "📜 السجل"
SHORTCUT_LANGUAGE = "🌍 اللغة"

# Shown in Telegram's chat menu button (the "/" icon next to the text
# input) - order matches the command list everywhere else in the bot.
COMMAND_DESCRIPTIONS = {
    "start": "ابدأ من جديد",
    "help": "ما الذي يمكنني فعله",
    "cancel": "إلغاء والبدء من جديد",
    "history": "مراجعة النصوص السابقة",
    "language": "تغيير لغة المحادثة",
    "privacy": "ما أخزّنه وكيفية حذفه",
    "feedback": "أرسل ملاحظاتك أو أبلغ عن مشكلة",
}

# --- Uzbek alphabet toggle (shown only to Uzbek-interface users on Uzbek results) ---
ALPHABET_TO_NEW_BUTTON = "🔤 الأبجدية الجديدة: ö ğ ş ç"
ALPHABET_TO_OLD_BUTTON = "🔤 الأبجدية القديمة: oʻ gʻ sh ch"
ALPHABET_CHANGED_NEW = "🔤 تم التبديل إلى الأبجدية الجديدة (ö ğ ş ç)"
ALPHABET_CHANGED_OLD = "🔤 تم التبديل إلى الأبجدية القديمة (oʻ gʻ sh ch)"

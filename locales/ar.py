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
_FEATURE_LIST_PARTS = [
    ("✍️ ", False), ("تفريغ نصي", True), (" — أحوّل ما يُقال إلى نص واضح ومرتب\n", False),
    ("🌐 ", False), ("ترجمة", True), (" — بلغة أخرى\n", False),
    ("🔍 ", False), ("تلخيص", True), (" — إذا أردت الخلاصة فقط\n", False),
    ("📄 ", False), ("تصدير", True), (" — كملف PDF أو نصي", False),
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
    "🇺🇿 يبدو أن هذا باللغة الأوزبكية - أنتقل إلى *نموذج متخصص* لدقة أفضل. "
    "قد يستغرق هذا دقيقة أو دقيقتين في المقاطع الأطول، شكراً لصبرك!"
)

CLEANING = [
    "✨ أرتّب النص الآن...",
    "✨ أنعّم الحواف الخشنة في النص...",
    "✨ ألمسة أخيرة على النص...",
]

TRANSCRIPT_HEADER = "إليك النص الكامل، *منظّماً وجاهزاً*:"
AUDIO_CAPTION = "إليك الصوت الذي استخرجته 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 ملف نصي"
EXPORT_PROMPT = "تريد نسخة تحتفظ بها؟ اختر صيغة أدناه:"
EXPORT_FAILED = "للأسف لم أتمكن من تجهيز الملف. اضغط الزر أدناه لتجربة ذلك مرة أخرى."

TRANSLATE_BUTTON = "🌐 ترجم"
SUMMARIZE_BUTTON = "🔍 لخّص"
TRANSLATE_PICKER_PROMPT = "إلى أي لغة أترجمه؟"
TRANSLATING = "🌐 أترجم الآن..."
TRANSLATION_HEADER = "إليك الترجمة:"
TRANSLATION_FAILED = "للأسف لم تنجح الترجمة. اختر لغة أدناه لتجربة ذلك مرة أخرى."
TRANSLATION_SAME_LANGUAGE = "هذا أصلاً بهذه اللغة!"
SUMMARIZING = "🔍 ألخّص الآن..."
SUMMARY_HEADER = "إليك ملخصاً سريعاً:"
SUMMARY_FAILED = "للأسف لم أتمكن من تجهيز الملخص. اضغط الزر أدناه لتجربة ذلك مرة أخرى."

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
    ("أعمل بالروابط، وليس بالملفات المُرسلة مباشرة — أرسل لي رابط ", False),
    *_PLATFORM_LIST_PARTS,
    (" بدلاً من ذلك.", False),
]

ERROR_PRIVATE = (
    "يبدو أن هذا حساب أو فيديو *خاص* — يمكنني فقط الوصول إلى المحتوى العام. "
    "إذا جعلته عاماً، أرسل الرابط مرة أخرى."
)
ERROR_UNAVAILABLE = (
    "لم أتمكن من العثور على هذا الفيديو — ربما تم *حذفه* أو أنه *خاص* أو "
    "*محظور* في بعض المناطق. تأكد من الرابط ثم أرسله لي مرة أخرى."
)
ERROR_TIMEOUT = (
    "استغرق هذا *وقتاً طويلاً* للتحميل — يحدث هذا أحياناً مع اتصال بطيء أو "
    "ملف كبير. أرسل الرابط مرة أخرى وسأحاول من جديد."
)
ERROR_NETWORK = "يبدو أن هناك *مشكلة في الشبكة*. أرسل الرابط مرة أخرى ولنجرب مجدداً."
ERROR_TOO_LARGE = "هذا الملف *كبير جداً* على إرساله عبر تيليجرام الآن، آسف على ذلك. أرسل رابط مقطع أقصر."
ERROR_GENERIC = (
    "*حدث خطأ ما* من جهتي ولم أتمكن من معالجة هذا. تأكد أن الرابط صحيح "
    "وعام، ثم أرسله لي مرة أخرى."
)
ERROR_NO_VIDEO = "يبدو أن هذا المنشور لا يحتوي على *فيديو* — أعمل فقط مع المنشورات التي تحتوي على واحد."
ERROR_NO_AUDIO = "يبدو أن هذا الفيديو لا يحتوي على *صوت* — أعمل فقط مع الفيديوهات التي تحتوي على صوت."

NO_TRANSCRIPT_SAVED = "لم يعد لدي هذا النص — أرسل الرابط مرة أخرى ولنبدأ من جديد."
STILL_WORKING = "*ما زلت أعمل* على طلبك السابق — امنحني لحظة لإنهائه أولاً!"

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

HISTORY_HEADER = "إليك آخر نصوصك — اضغط على أي منها لعرضه مرة أخرى:"
# See en.py's _PLATFORM_LIST_PARTS comment for why this is entity-based.
HISTORY_EMPTY_PARTS = [
    ("ليس لديك أي نصوص بعد — أرسل رابط ", False),
    ("🎥", YOUTUBE), (" يوتيوب", True),
    (" أو ", False),
    ("📸", INSTAGRAM), (" إنستغرام", True),
    (" وسيظهر هنا في المرة القادمة.", False),
]
HISTORY_NOT_FOUND = "لم أتمكن من العثور على هذا بعد الآن — ربما قديم جداً أو تم حذفه. جرّب /history مرة أخرى."

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
    "facebook": "📘 فيسبوك",
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
}

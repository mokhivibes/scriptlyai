NATIVE_NAME = "العربية"

LANGUAGE_CHANGED = (
    "تمام، من الآن سأتحدث معك *بالعربية*!\n"
    "أرسل رابطاً للبدء، أو اكتب /help لمعرفة التفاصيل."
)

# Shown once, the first time a user ever picks a language - a fuller, warm
# greeting rather than the short LANGUAGE_CHANGED confirmation used every
# other time someone switches languages. Deliberately plain text, NOT
# formatted - contains {first_name}, which is genuinely user-controlled
# (a Telegram user can set their name to include a literal * or _), unlike
# every other formatted message in this file, which is 100% developer text.
LANGUAGE_ONBOARDING = (
    "أهلاً {first_name}! 👋 تمام، من الآن سأتحدث معك بالعربية.\n\n"
    "فقط أرسل لي رابطاً — 🎥 يوتيوب، 📸 إنستغرام، 🎵 تيك توك، أو ✖️ "
    "إكس/تويتر — أدوّنه وأنظفه لك ✨. تريد نسخة تحتفظ بها؟ أجهّزها "
    "بصيغة PDF أو ملف نصي. 📄\n\n"
    "أرسل رابطاً للبدء، أو اكتب /help لمعرفة التفاصيل."
)

# START_TEXT also stays plain (no bold/italic) for the same {first_name}
# reason as LANGUAGE_ONBOARDING above.
START_TEXT = (
    "أهلاً {first_name}! 👋 أنا ScriptlyAI.\n\n"
    "أرسل لي رابط فيديو — 🎥 يوتيوب، 📸 إنستغرام، 🎵 تيك توك، أو ✖️ "
    "إكس/تويتر حالياً — وسأحوّل ما يُقال فيه إلى نص واضح ومرتب. ✨ تريد "
    "نسخة؟ أجهّزها لك بصيغة PDF أو ملف نصي. 📄\n\n"
    "لست متأكداً كيف يعمل؟ فقط اكتب /help."
)
HELP_TEXT = (
    "أرسل لي رابط من *يوتيوب* أو *إنستغرام* أو *تيك توك* أو *إكس/تويتر*، "
    "وسأستمع إليه، أدوّن كل ما فيه، ثم أعيده لك نظيفاً وواضحاً.\n"
    "تريد نسخة تحتفظ بها؟ يمكنني تجهيزها بصيغة PDF أو كملف نصي. أعمل بشكل "
    "أفضل مع الكلام المنطوق — الأغاني قد تستغرق وقتاً أطول وتكون أقل دقة.\n\n"
    "_فيسبوك قادم قريباً — كن بالانتظار!_\n\n"
    "/history لمراجعة النصوص السابقة. /language لتغيير لغة المحادثة. "
    "/cancel للبدء من جديد. /start للترحيب من جديد."
)

DOWNLOADING = [
    "📥 أجلب الصوت من رابط *{platform}*...",
    "📥 جارٍ التحميل من *{platform}* الآن...",
    "📥 أحضر صوت *{platform}*، لحظات...",
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
CLEANING = [
    "✨ أرتّب النص الآن...",
    "✨ أنعّم الحواف الخشنة في النص...",
    "✨ ألمسة أخيرة على النص...",
]

TRANSCRIPT_HEADER = "إليك النص الكامل، منظّماً وجاهزاً:"
AUDIO_CAPTION = "إليك الصوت الذي استخرجته 🎧"

EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 ملف نصي"
EXPORT_PROMPT = "تريد نسخة تحتفظ بها؟ اختر صيغة أدناه:"
EXPORT_FAILED = "للأسف لم أتمكن من تجهيز الملف. هل تريد المحاولة مرة أخرى؟"
EXPORT_READY_CAPTION = "إليك {label} بصيغة *{file_format}*."
EXPORT_LABEL_TRANSCRIPT = "النص المنظّم"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "ملف نصي"

NO_LINK_FOUND = "لا أرى رابطاً هنا — أرسل رابط يوتيوب أو إنستغرام أو تيك توك أو إكس/تويتر وسأبدأ العمل."
UNRECOGNIZED_LINK = (
    "لا أتعرّف على هذا الرابط. أعمل مع روابط يوتيوب وإنستغرام وتيك توك "
    "وفيسبوك وإكس/تويتر — جرّب أحدها."
)
FACEBOOK_PLACEHOLDER = "لاحظت أن هذا رابط فيسبوك، لكن لا يمكنني التعامل معه بعد — قريباً إن شاء الله!"

ERROR_PRIVATE = (
    "يبدو أن هذا حساب أو فيديو خاص — يمكنني فقط الوصول إلى المحتوى العام. "
    "إذا جعلته عاماً، أرسل الرابط مرة أخرى."
)
ERROR_UNAVAILABLE = (
    "لم أتمكن من العثور على هذا الفيديو — ربما تم حذفه أو أنه خاص أو "
    "محظور في بعض المناطق. تأكد من الرابط وحاول مرة أخرى؟"
)
ERROR_TIMEOUT = (
    "استغرق هذا وقتاً طويلاً للتحميل — يحدث هذا أحياناً مع اتصال بطيء أو "
    "ملف كبير. هل تريد المحاولة مرة أخرى؟"
)
ERROR_NETWORK = "يبدو أن هناك مشكلة في الشبكة. أرسل الرابط مرة أخرى ولنجرب مجدداً."
ERROR_TOO_LARGE = "هذا الملف كبير جداً على إرساله عبر تيليجرام الآن، آسف على ذلك. ربما تجرّب مقطعاً أقصر؟"
ERROR_GENERIC = (
    "حدث خطأ ما من جهتي ولم أتمكن من معالجة هذا. تأكد أن الرابط صحيح "
    "وعام، ثم حاول مرة أخرى؟"
)
ERROR_NO_VIDEO = "يبدو أن هذا المنشور لا يحتوي على فيديو — أعمل فقط مع المنشورات التي تحتوي على واحد."
ERROR_NO_AUDIO = "يبدو أن هذا الفيديو لا يحتوي على صوت — أعمل فقط مع الفيديوهات التي تحتوي على صوت."

NO_TRANSCRIPT_SAVED = "لم يعد لدي هذا النص — أرسل الرابط مرة أخرى ولنبدأ من جديد."
STILL_WORKING = "ما زلت أعمل على طلبك السابق — امنحني لحظة لإنهائه أولاً!"

LONG_CONTENT_WARNING = (
    "يبدو أن هذا مقطع أطول (~{minutes} دقيقة) — قد تستغرق النسخة عدة دقائق، "
    "والنتائج أقل دقة مع الأغاني منها مع الكلام. هل أكمل؟"
)
CONFIRM_YES_BUTTON = "✅ نعم، أكمل"
CONFIRM_NO_BUTTON = "❌ إلغاء"
PROCESSING_CANCELLED = "تمام، ألغيت الأمر. أرسل رابطاً آخر متى كنت مستعداً."

CANCEL_HAD_DATA = (
    "تم، كل شيء *ألغيته*! أي شيء كنت أحتفظ به اختفى الآن. أرسل رابطاً "
    "جديداً متى شئت.\n\n"
    "_(ملاحظة سريعة: إذا كان هناك شيء لا يزال يُعالج في الخلفية، فقد "
    "تصلك رسالة منه لاحقاً — تجاهلها فقط.)_"
)
CANCEL_NOTHING = "*لا يوجد شيء لإلغائه* الآن — أنا فقط بالانتظار. أرسل رابطاً متى كنت مستعداً."

HISTORY_HEADER = "إليك آخر نصوصك — اضغط على أي منها لعرضه مرة أخرى:"
HISTORY_EMPTY = "ليس لديك أي نصوص بعد — أرسل رابط يوتيوب أو إنستغرام وسيظهر هنا في المرة القادمة."
HISTORY_NOT_FOUND = "لم أتمكن من العثور على هذا بعد الآن — ربما قديم جداً أو تم حذفه. جرّب /history مرة أخرى."

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
}

TARGET_LANGUAGE_NAMES = {
    "en": "الإنجليزية",
    "ru": "الروسية",
    "ar": "العربية",
    "uz": "الأوزبكية",
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

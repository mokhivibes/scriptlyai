from utils.rich_text import DYNAMIC
from utils.platform_emoji import YOUTUBE, INSTAGRAM, TIKTOK, FACEBOOK, X_TWITTER

NATIVE_NAME = "English"

# The branded platform-icon segment shared by both PARTS messages below -
# each icon is its own (placeholder_emoji, custom_emoji_id) part so
# Telegram overlays the real brand icon on top of the plain-emoji
# placeholder (falls back to the placeholder on clients that don't
# support custom emoji, so this degrades gracefully rather than breaking).
_PLATFORM_LIST_PARTS = [
    ("🎥", YOUTUBE), (" YouTube, ", False),
    ("📸", INSTAGRAM), (" Instagram, ", False),
    ("🎵", TIKTOK), (" TikTok, ", False),
    ("📘", FACEBOOK), (" Facebook, or ", False),
    ("✖️", X_TWITTER), (" X/Twitter", False),
]

# One line per capability, each its own bolded label + short description -
# shared across the welcome/onboarding/help messages below so what the
# bot can do is scannable at a glance instead of buried in a paragraph.
# Translate is deliberately left out here - see TRANSLATION_ENABLED in
# handlers/link_handler.py for why; don't advertise a feature that's
# currently hidden from the button menu.
_FEATURE_LIST_PARTS = [
    ("✍️ ", False), ("Transcribe", True), (" — turn what's said into clean, readable text\n", False),
    ("🔍 ", False), ("Summarize", True), (" — get the short version\n", False),
    ("📄 ", False), ("Export", True), (" — save it as a PDF or text file\n", False),
    ("📋 ", False), ("Copy", True), (" — grab the text with one tap", False),
]

LANGUAGE_CHANGED = (
    "Got it — I'll speak 🇬🇧 *English* from now on!\n"
    "Send me a link to get started, or /help for the full picture."
)

# Shown once, the first time a user ever picks a language - a fuller, warm
# greeting rather than the short LANGUAGE_CHANGED confirmation used every
# other time someone switches languages. Built as PARTS (see
# utils/rich_text.py) rather than a Markdown string - {first_name}/DYNAMIC
# is genuinely user-controlled (a Telegram user can set their name to
# include a literal * or _), and entity-based bold is immune to that in a
# way Markdown syntax scanning is not.
LANGUAGE_ONBOARDING_PARTS = [
    ("Hey ", False),
    (DYNAMIC, False),
    ("! 👋 Great, I'll speak 🇬🇧 ", False),
    ("English", True),
    (" with you from now on!\n\nSend me a link — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — and here's what I can do:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nSend a link to get started, or type ", False),
    ("/help", True),
    (" for the full picture!", False),
]

# --- /start and /help ---
# START_TEXT_PARTS - see LANGUAGE_ONBOARDING_PARTS above for why this is
# parts-based rather than a Markdown string.
START_TEXT_PARTS = [
    ("Hey there, ", False),
    (DYNAMIC, False),
    ("! 👋 I'm ", False),
    ("ScriptlyAI", True),
    ("!\n\nSend me a video link — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — and here's what I can do:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nNot sure how it works?\n\nJust type ", False),
    ("/help", True),
    ("!", False),
]
# HELP_TEXT_PARTS - see en.py's LANGUAGE_ONBOARDING_PARTS comment for why
# messages that need custom emoji (via _PLATFORM_LIST_PARTS) are
# parts-based rather than plain Markdown strings - custom emoji require
# MessageEntity, which Markdown syntax cannot express.
HELP_TEXT_PARTS = [
    ("Send me a link — ", False),
    *_PLATFORM_LIST_PARTS,
    (" — and here's what I can do:\n\n", False),
    *_FEATURE_LIST_PARTS,
    ("\n\nWorks best on spoken content — music or singing can take "
     "longer and come out less accurate.\n\n", False),
    ("/history", True),
    (" — revisit past transcripts\n", False),
    ("/language", True),
    (" — change how I talk to you\n", False),
    ("/cancel", True),
    (" — start over\n", False),
    ("/privacy", True),
    (" — see what I store, and delete it\n", False),
    ("/feedback", True),
    (" — send me feedback or report a problem\n", False),
    ("/start", True),
    (" — say hi again", False),
]

# --- Progress messages (randomized so repeat users see some variety) ---
# (prefix, suffix) around the platform mention - see
# utils/messages.py's downloading_message_rich() for why this is
# templates-with-a-gap rather than a {platform} string substitution:
# the branded platform icon needs a custom emoji entity, which can only
# be built structurally (see rich_text.py), not via string formatting.
DOWNLOADING_TEMPLATES = [
    ("📥 Grabbing the audio from your ", " link..."),
    ("📥 On it — pulling this down from ", " now."),
    ("📥 Fetching your ", " audio, hang tight."),
]
EXTRACTING_AUDIO = [
    "✂️ Pulling the audio out now...",
    "🎬 Separating the sound from the video...",
    "✂️ Getting the audio ready for a listen...",
]
TRANSCRIBING = [
    "👂 Listening closely to every word...",
    "✍️ Turning the sound into sentences...",
    "✍️ Writing down exactly what's said...",
]

# Shown only when Groq's detection lands on the Uzbek misdetection cluster
# and the local Uzbek-specific fallback model kicks in (see
# speech_service.py) - that step is real, uninterruptible CPU work that
# can take over a minute on a full song, so this explains the extra wait
# instead of leaving "Transcribing..." on screen with no sign of progress.
TRANSCRIBING_UZBEK_FALLBACK = (
    "🇺🇿 This might be Uzbek (or a closely related language) - "
    "double-checking with our *specialized model* for accuracy. This can "
    "take a minute or two on longer clips, thanks for your patience!"
)

CLEANING = [
    "✨ Tidying up the transcript now...",
    "✨ Smoothing out the rough edges...",
    "✨ Giving this a quick clean-up pass...",
]

# --- Delivery messages ---
# *_HEADER_PARTS (not a parse_mode="Markdown" string) since these now get
# combined with the transcript/translation/summary itself - genuinely
# unpredictable content - into ONE message via entities (see
# handlers/link_handler.py's send_copyable_result). Mixing a
# parse_mode="Markdown" header with appended unsafe content in the same
# message isn't possible; entities are the only safe way to do both.
TRANSCRIPT_HEADER_PARTS = [
    ("Here's the full transcript, ", False), ("cleaned up and ready", True), (":", False),
]
AUDIO_CAPTION = "Here's the audio I pulled out 🎧"

# --- Export options ---
EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 Text file"
EXPORT_PROMPT = "Want a copy to keep? Pick a format below:"
EXPORT_FAILED = "📄 Hmm, I couldn't put that file together. _Tap the button below to try again._"

# --- Translate & Summarize (post-transcript actions, alongside export) ---
TRANSLATE_BUTTON = "🌐 Translate"
SUMMARIZE_BUTTON = "🔍 Summarize"
TRANSLATE_PICKER_PROMPT = "Which language should I translate it into?"
TRANSLATING = "🌐 Translating..."
TRANSLATION_HEADER_PARTS = [("Here's the translation:", False)]
TRANSLATION_FAILED = "🌐 Hmm, that translation didn't go through. _Pick a language below to try again._"
TRANSLATION_SAME_LANGUAGE = "That's already the language this is in!"
# Shown only for a translate button tapped from a keyboard that was
# already on screen before TRANSLATION_ENABLED was turned off - see that
# constant's comment in handlers/link_handler.py.
TRANSLATION_UNAVAILABLE = "🌐 Translation isn't available yet — it's coming soon!"
SUMMARIZING = "🔍 Summarizing..."
SUMMARY_HEADER_PARTS = [("Here's a quick summary:", False)]
SUMMARY_FAILED = "🔍 Hmm, I couldn't put a summary together. _Tap the button below to try again._"

# Shown with the full 4-button menu (export/translate/summarize) right
# after a transcript - deliberately more general than EXPORT_PROMPT
# below, which is reused for the narrower 2-button save-only screen
# shown after a translation or summary (where "pick a format" is
# accurate again, since only export makes sense there).
NEXT_ACTIONS_PROMPT = "What would you like to do with this?"
EXPORT_READY_CAPTION = "Here's your {label} as a *{file_format}*."
EXPORT_LABEL_TRANSCRIPT = "cleaned transcript"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "text file"

# --- Link handling ---
NO_LINK_FOUND_PARTS = [
    ("Hmm, I don't see a link in there — send me a ", False),
    *_PLATFORM_LIST_PARTS,
    (" link and I'll get started.", False),
]
UNRECOGNIZED_LINK_PARTS = [
    ("I don't recognize that link. I work with ", False),
    *_PLATFORM_LIST_PARTS,
    (" links — try one of those.", False),
]
# Shown for a photo, voice note, video file, document, or sticker sent
# directly - the bot works from links only (downloads them itself), not
# uploaded media, so this needs to say that clearly rather than staying
# silent (which is what happened before this existed - a natural mistake
# for a transcription bot's users to make, worth a clear reply).
UNSUPPORTED_MESSAGE_PARTS = [
    ("I can't read that kind of file. Send me a voice message, an audio or video file (up to 20 MB), or a ", False),
    *_PLATFORM_LIST_PARTS,
    (" link.", False),
]
# --- Errors - one leading emoji per message (quick visual "what kind of
# problem" cue at a glance) plus bold for the diagnosis and italic for the
# actionable next step, so the two are visually distinct when scanning.
ERROR_PRIVATE = (
    "🔒 This looks like a *private* account or video — I can only grab stuff "
    "that's public. _If you can make it public, send me the link again._"
)
ERROR_UNAVAILABLE = (
    "🚫 I couldn't find this video — it might be *deleted*, *private*, or "
    "*blocked* in some regions. _Double check the link, then send it to me again._"
)
ERROR_TIMEOUT = (
    "⏱️ This one took *too long* to load — sometimes that happens with a slow "
    "connection or a big file. _Send the link again and I'll give it another shot._"
)
ERROR_NETWORK = "📡 Looks like a *network hiccup* got in the way. _Send the link again and let's try that one more time._"
ERROR_TOO_LARGE = (
    "📦 This file's *too big* for me to send back through Telegram right now, "
    "sorry about that. _Try sending me a shorter clip instead._"
)
ERROR_GENERIC = (
    "⚠️ *Something went wrong* on my end and I couldn't process this one. "
    "_Double check the link's valid and public, then send it to me again._"
)
ERROR_NO_VIDEO = "🎬 This post doesn't seem to have a *video* in it — I can only work with posts that include one."
ERROR_NO_AUDIO = "🔇 This video doesn't seem to have any *sound* in it — I can only work with videos that include audio."
ERROR_RATE_LIMITED = (
    "⏳ I'm getting a *lot of requests* right now and hit my limit — this isn't "
    "about your link. _Please wait a few minutes and send it again._"
)

NO_TRANSCRIPT_SAVED = "🗂️ I don't have that transcript anymore — _send me the link again and we'll start fresh._"
DAILY_LIMIT_REACHED = (
    "📅 You've hit today's *usage limit* so I can keep things fair for everyone "
    "sharing the bot. _Come back tomorrow and I'll be ready to go._"
)
STILL_WORKING = "⚙️ *Still working* on your last one — give me a moment to finish that first!"

# --- Long-content confirmation (duration-based, shown before committing to
# a multi-minute job) ---
LONG_CONTENT_WARNING = (
    "This looks like a *longer one* (~{minutes} min) — transcription can "
    "take several minutes, and results are less reliable for music/singing "
    "than speech. Want me to go ahead?"
)
CONFIRM_YES_BUTTON = "✅ Yes, go ahead"
CONFIRM_NO_BUTTON = "❌ Cancel"
PROCESSING_CANCELLED = "No worries — *cancelled*. Send another link whenever you're ready."

# --- /cancel ---
CANCEL_HAD_DATA = (
    "Okay, *cleared*! Whatever I was holding onto is gone now. Just send me "
    "a new link whenever you're ready.\n\n"
    "_(Quick heads up: if something's still processing in the background, "
    "you might still get a message from it after this — just ignore it.)_"
)
CANCEL_NOTHING = "*Nothing to cancel* right now — I'm just here waiting. Send me a link whenever you're ready."

# --- /privacy ---
PRIVACY_TEXT = (
    "🔒 *What I store*\n\n"
    "• Your Telegram ID, username, and first name — so I know it's you\n"
    "• Your chosen interface language — so I remember it next time\n"
    "• Transcripts you've generated (platform, detected language, title, date) — so /history works\n\n"
    "*What I don't store*\n\n"
    "• The video or audio file itself — deleted right after processing (audio waiting for your “Get the text” tap is removed after an hour at most)\n"
    "• Anything you haven't sent me\n\n"
    "*Who processes your audio*\n\n"
    "• Groq — transcription and clean-up\n"
    "• For audio that sounds like Uzbek, Kazakh or Kyrgyz, also Google's Gemini API — Google's free tier may use submitted audio to improve its products\n\n"
    "The file is deleted from my side right after processing, and from Google's file store too.\n\n"
    "Your data is never sold. You can delete everything below, anytime."
)
DELETE_DATA_BUTTON = "🗑 Delete my data"
DELETE_DATA_CONFIRM_PROMPT = (
    "⚠️ This *permanently* deletes all your saved transcripts and resets your language preference. "
    "This can't be undone. Continue?"
)
DELETE_DATA_CONFIRM_YES_BUTTON = "🗑 Yes, delete everything"
DELETE_DATA_DONE = "✅ *All done* — your data has been deleted. Send /start whenever you'd like to begin again."
DELETE_DATA_CANCELLED = "Okay, nothing was deleted."

# --- /history ---
HISTORY_HEADER = "Here's your last few transcripts — tap one to see it again:"
# See en.py's _PLATFORM_LIST_PARTS comment for why this is entity-based.
HISTORY_EMPTY_PARTS = [
    ("You don't have any transcripts yet — send me a ", False),
    ("🎥", YOUTUBE), (" YouTube", True),
    (" or ", False),
    ("📸", INSTAGRAM), (" Instagram", True),
    (" link and it'll show up here next time.", False),
]
HISTORY_NOT_FOUND = "📜 Hmm, I couldn't find that one anymore — it may be too old or already gone. _Try /history again._"

# Direct file uploads (voice note / audio / video sent straight to the bot).
DOWNLOADING_FILE = "📥 *Getting your file…* _hang tight._"
FILE_TOO_BIG_TO_DOWNLOAD = (
    "📦 That file is *over 20 MB*, and Telegram won't let me download anything that big. "
    "_Send a smaller file, or paste a link to it instead._"
)

# Shown with a web-search button when a SHORT non-link text arrives (likely a song name).
LYRICS_HINT = "\n\n🎤 If that was a song name, tap below to find its lyrics."
LYRICS_BUTTON = "🎤 Find lyrics"

# Bot profile texts (shown on the bot's page / before /start) and /feedback.
BOT_DESCRIPTION = "Send a link or a file, get clean text. 🎬 Paste a YouTube, Instagram, TikTok, Facebook or X link — or send a voice message, audio or video file (up to 20 MB). ✍️ I transcribe it, tidy it up, and give you a short summary, one-tap copy, or a PDF/text file. 🌍 I speak English, Русский, العربية and Oʻzbekcha. Tap Start to begin."
BOT_SHORT_DESCRIPTION = "Turn videos, voice notes & audio into clean text in seconds. Summaries, PDF export, 4 languages."
FEEDBACK_USAGE = "💬 Got feedback or found a bug? Send it along with the command, like:\n/feedback the PDF cut off my last line"
FEEDBACK_THANKS = "🙏 Thanks — your feedback reached me."
FEEDBACK_TOO_SOON = "⏳ Please wait a minute before sending more feedback."

COPY_BUTTON = "📋 Copy"
COPY_HINT = "📋 Tap the text below to copy it."

LINK_RECEIVED = "👀 *Got your link!* _Checking it now…_"

ERROR_NO_SPEECH = "🔇 I couldn't hear any *speech* in this — it may be silent, or just music or noise. _Try one where someone is talking._"

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
    "facebook": "📘 Facebook",
    "upload": "📎 File",
}

# Display names for the video's SPOKEN (detected) language, shown in
# /history entries - independent of the bot's own interface language.
TARGET_LANGUAGE_NAMES = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Russian",
    "ar": "🇸🇦 Arabic",
    "uz": "🇺🇿 Uzbek",
}
UNKNOWN_LANGUAGE = "Unknown"

MONTH_ABBREVIATIONS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Labels for the persistent reply-keyboard shortcuts (always visible below
# the text input). Friendly text + emoji instead of raw "/help" etc., to
# match the bot's warm tone elsewhere - these are matched against incoming
# text in match_shortcut() and routed to the right command manually, since
# Telegram only auto-recognizes a literal "/command" as a command.
SHORTCUT_HELP = "❓ Help"
SHORTCUT_HISTORY = "📜 History"
SHORTCUT_LANGUAGE = "🌍 Language"

# Shown in Telegram's chat menu button (the "/" icon next to the text
# input) - order matches the command list everywhere else in the bot.
COMMAND_DESCRIPTIONS = {
    "start": "Say hi and get started",
    "help": "See what I can do",
    "cancel": "Stop and clear the current job",
    "history": "Revisit past transcripts",
    "language": "Change how I talk to you",
    "privacy": "See what I store, and delete it",
    "feedback": "Send feedback or report a problem",
}

# --- Uzbek alphabet toggle (shown only to Uzbek-interface users on Uzbek results) ---
ALPHABET_TO_NEW_BUTTON = "🔤 New alphabet: ö ğ ş ç"
ALPHABET_TO_OLD_BUTTON = "🔤 Old alphabet: oʻ gʻ sh ch"
ALPHABET_CHANGED_NEW = "🔤 Switched to the new alphabet (ö ğ ş ç)"
ALPHABET_CHANGED_OLD = "🔤 Switched to the old alphabet (oʻ gʻ sh ch)"

# --- "Get text" on demand (links: audio first, transcribe only on tap) ---
GET_TEXT_BUTTON = "📝 Get the text"
AUDIO_CAPTION_ASK = "Here's the audio I pulled out 🎧\n\nWant the text too? Tap the button below 👇"
GET_TEXT_EXPIRED = "⏳ That audio isn't saved anymore (I only keep it for an hour). Please send the link again."

# --- YouTube refusing the server (expired cookies) ---
YOUTUBE_BLOCKED = "⚠️ YouTube is blocking me for the moment, so I can't fetch this link right now. I've let the owner know. Please try again later, or send the audio or video as a file instead."

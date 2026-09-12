NATIVE_NAME = "English"

LANGUAGE_CHANGED = (
    "Got it — I'll speak *English* from now on!\n"
    "Send me a link to get started, or /help for the full picture."
)

# Shown once, the first time a user ever picks a language - a fuller, warm
# greeting rather than the short LANGUAGE_CHANGED confirmation used every
# other time someone switches languages. Deliberately plain text, NOT
# formatted - contains {first_name}, which is genuinely user-controlled
# (a Telegram user can set their name to include a literal * or _), unlike
# every other formatted message in this file, which is 100% developer text.
LANGUAGE_ONBOARDING = (
    "Hey {first_name}! 👋 Great, I'll speak English with you from now on.\n\n"
    "Just send me a link — 🎥 YouTube, 📸 Instagram, 🎵 TikTok, or ✖️ "
    "X/Twitter — and I'll transcribe it and clean it up ✨. Want a copy? "
    "I can export it as a PDF or text file. 📄\n\n"
    "Send a link to get started, or /help for the full picture."
)

# --- /start and /help ---
# START_TEXT also stays plain (no bold/italic) for the same {first_name}
# reason as LANGUAGE_ONBOARDING above.
START_TEXT = (
    "Hey there, {first_name}! 👋 I'm ScriptlyAI.\n\n"
    "Send me a video link — 🎥 YouTube, 📸 Instagram, 🎵 TikTok, or ✖️ "
    "X/Twitter for now — and I'll turn what's said into clean, readable "
    "text. ✨ Want a copy? I can export it as a PDF or text file. 📄\n\n"
    "Not sure how it works? Just type /help."
)
HELP_TEXT = (
    "Send me a *YouTube*, *Instagram*, *TikTok*, or *X/Twitter* link and I'll "
    "listen to it, write it all down, and hand it back to you clean.\n"
    "Want a copy to keep? I can export it as a PDF or text file.\n\n"
    "_Facebook is on the way — hang tight!_\n\n"
    "/history to revisit past transcripts. /language to change how I talk to you. "
    "/cancel to start over. /start to say hi again."
)

# --- Progress messages (randomized so repeat users see some variety) ---
DOWNLOADING = [
    "📥 Grabbing the audio from your *{platform}* link...",
    "📥 On it — pulling this down from *{platform}* now.",
    "📥 Fetching your *{platform}* audio, hang tight.",
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
CLEANING = [
    "✨ Tidying up the transcript now...",
    "✨ Smoothing out the rough edges...",
    "✨ Giving this a quick clean-up pass...",
]

# --- Delivery messages ---
TRANSCRIPT_HEADER = "Here's the full transcript, cleaned up and ready:"
AUDIO_CAPTION = "Here's the audio I pulled out 🎧"

# --- Export options ---
EXPORT_PDF_BUTTON = "📄 PDF"
EXPORT_TXT_BUTTON = "📝 Text file"
EXPORT_PROMPT = "Want a copy to keep? Pick a format below:"
EXPORT_FAILED = "Hmm, I couldn't put that file together. Mind trying again?"
EXPORT_READY_CAPTION = "Here's your {label} as a *{file_format}*."
EXPORT_LABEL_TRANSCRIPT = "cleaned transcript"
FILE_FORMAT_PDF = "PDF"
FILE_FORMAT_TEXT = "text file"

# --- Link handling ---
NO_LINK_FOUND = "Hmm, I don't see a link in there — send me a YouTube, Instagram, TikTok, or X/Twitter link and I'll get started."
UNRECOGNIZED_LINK = (
    "I don't recognize that link. I work with YouTube, Instagram, TikTok, "
    "Facebook, or X/Twitter links — try one of those."
)
FACEBOOK_PLACEHOLDER = "I spotted a Facebook link, but I can't handle those just yet — coming soon though!"

# --- Errors (no emojis - clarity comes first when something's gone wrong) ---
ERROR_PRIVATE = (
    "This looks like a private account or video — I can only grab stuff "
    "that's public. If you can make it public, send me the link again."
)
ERROR_UNAVAILABLE = (
    "I couldn't find this video — it might be deleted, private, or blocked "
    "in some regions. Double check the link and try again?"
)
ERROR_TIMEOUT = (
    "This one took too long to load — sometimes that happens with a slow "
    "connection or a big file. Mind trying again?"
)
ERROR_NETWORK = "Looks like a network hiccup got in the way. Send the link again and let's try that one more time."
ERROR_TOO_LARGE = (
    "This file's too big for me to send back through Telegram right now, "
    "sorry about that. Maybe try a shorter clip?"
)
ERROR_GENERIC = (
    "Something went wrong on my end and I couldn't process this one. "
    "Double check the link's valid and public, then give it another go?"
)
ERROR_NO_VIDEO = "This post doesn't seem to have a video in it — I can only work with posts that include one."
ERROR_NO_AUDIO = "This video doesn't seem to have any sound in it — I can only work with videos that include audio."

NO_TRANSCRIPT_SAVED = "I don't have that transcript anymore — send me the link again and we'll start fresh."
STILL_WORKING = "Still working on your last one — give me a moment to finish that first!"

# --- /cancel ---
CANCEL_HAD_DATA = (
    "Okay, *cleared*! Whatever I was holding onto is gone now. Just send me "
    "a new link whenever you're ready.\n\n"
    "_(Quick heads up: if something's still processing in the background, "
    "you might still get a message from it after this — just ignore it.)_"
)
CANCEL_NOTHING = "*Nothing to cancel* right now — I'm just here waiting. Send me a link whenever you're ready."

# --- /history ---
HISTORY_HEADER = "Here's your last few transcripts — tap one to see it again:"
HISTORY_EMPTY = "You don't have any transcripts yet — send me a YouTube or Instagram link and it'll show up here next time."
HISTORY_NOT_FOUND = "Hmm, I couldn't find that one anymore — it may be too old or already gone. Try /history again."

PLATFORM_LABELS = {
    "youtube": "🎥 YouTube",
    "instagram": "📸 Instagram",
    "twitter": "✖️ X/Twitter",
    "tiktok": "🎵 TikTok",
}

# Display names for the video's SPOKEN (detected) language, shown in
# /history entries - independent of the bot's own interface language.
TARGET_LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Russian",
    "ar": "Arabic",
    "uz": "Uzbek",
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
}

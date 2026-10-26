import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the .env file")

# Used by speech_service.py (Whisper transcription) and ai_cleanup_service.py
# (transcript cleanup) - both moved from local Whisper/Ollama to Groq's
# hosted API so the bot itself no longer needs several GB of RAM, making it
# light enough to run on ordinary free/cheap hosting.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in the .env file")

# Optional - Google AI Studio key for Gemini 3.5 Transcribe, used only for
# audio Groq places in the Uzbek/Kazakh/Kyrgyz cluster (see
# services/speech_service.py). Without it, the slower local models are used.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Relative to the project root, same as bot.db/downloads/logs - resolves
# correctly under both manual `python main.py` and the launchd deployment,
# since WorkingDirectory is set to the project root either way.
LOGO_PATH = "assets/logo.jpg"

# Optional - if set, the bot proactively DMs this Telegram user_id once
# per day when total Groq usage (summed across every user, not just one)
# approaches free-tier capacity - see GROQ_CAPACITY_WARNING_THRESHOLD in
# handlers/link_handler.py. Lets the owner decide when it's time to
# upgrade to a paid Groq tier based on real demand, without needing to
# watch logs. Entirely optional - the bot works normally without it, this
# just goes silent if unset.
OWNER_USER_ID = os.getenv("OWNER_USER_ID")
OWNER_USER_ID = int(OWNER_USER_ID) if OWNER_USER_ID else None

# Appended under everything the bot sends out, so shared results lead back here.
BOT_USERNAME = "@ScriptlyAI_bot"

# Optional Netscape-format cookies.txt for YouTube. YouTube blocks most
# datacenter/server IPs with "Sign in to confirm you're not a bot"; cookies
# from a (throwaway) logged-in account get past that. Not in git - it's a
# login credential. If the file doesn't exist, downloads run without it.
YOUTUBE_COOKIES_PATH = "youtube_cookies.txt"

# YouTube now hides its audio formats behind a JavaScript challenge that
# yt-dlp solves with a JS engine (Deno). On the server Deno is installed into
# the bot's own venv (`pip install deno`, see deploy/README.md) - a folder
# the systemd service doesn't have on its PATH - so point yt-dlp at it
# explicitly. None (yt-dlp's own lookup) when it isn't there, e.g. on the Mac.
_VENV_DENO = os.path.join(os.path.dirname(sys.executable), "deno")
YT_DLP_JS_RUNTIMES = {"deno": {"path": _VENV_DENO}} if os.path.exists(_VENV_DENO) else None

# Show Uzbek results in the revised Uzbek Latin alphabet (oʻ->ö, gʻ->ğ,
# sh->ş, ch->ç; law signed 2026-10-21). False keeps the 1995 orthography.
# See utils/uzbek_script.py.
UZBEK_NEW_ALPHABET = True

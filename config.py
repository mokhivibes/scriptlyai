import os
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

# Relative to the project root, same as bot.db/downloads/logs - resolves
# correctly under both manual `python main.py` and the launchd deployment,
# since WorkingDirectory is set to the project root either way.
LOGO_PATH = "assets/logo.png"

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

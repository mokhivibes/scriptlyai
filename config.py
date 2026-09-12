import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the .env file")

# Relative to the project root, same as bot.db/downloads/logs - resolves
# correctly under both manual `python main.py` and the launchd deployment,
# since WorkingDirectory is set to the project root either way.
LOGO_PATH = "assets/logo.png"
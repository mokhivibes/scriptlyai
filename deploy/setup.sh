#!/bin/bash
# One-time provisioning script for a fresh Ubuntu 24.04 server (e.g. a
# Hetzner CX22). Run as root (or with sudo) via SSH:
#
#   curl -sL https://raw.githubusercontent.com/mokhivibes/scriptlyai/main/deploy/setup.sh | bash
#
# or copy this file to the server and run `bash setup.sh`.
#
# What this does NOT do (deliberately, since these need secrets or
# judgment this script can't have):
#   - Create /home/scriptlyai/telegram-media-bot/.env (BOT_TOKEN,
#     GROQ_API_KEY, OWNER_USER_ID) - create this by hand after running
#     this script, see deploy/README.md.
#   - Copy over models/ (the ~2GB local Uzbek/Kazakh/Kyrgyz ASR models,
#     gitignored) or an existing bot.db - transfer these separately
#     (rsync/scp from wherever the bot ran before), see deploy/README.md.

set -euo pipefail

echo "==> Installing system packages..."
apt-get update
apt-get install -y python3 python3-venv python3-pip ffmpeg git sqlite3

echo "==> Creating dedicated 'scriptlyai' user (no login shell needed beyond running the bot)..."
if ! id -u scriptlyai >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash scriptlyai
fi

echo "==> Cloning the repository..."
sudo -u scriptlyai bash -c '
    cd /home/scriptlyai
    if [ -d telegram-media-bot ]; then
        cd telegram-media-bot && git pull
    else
        git clone https://github.com/mokhivibes/scriptlyai.git telegram-media-bot
    fi
'

echo "==> Creating the Python virtual environment and installing dependencies..."
sudo -u scriptlyai bash -c '
    cd /home/scriptlyai/telegram-media-bot
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
    # JS engine yt-dlp needs to unlock YouTube audio (kept in the venv, not system-wide)
    ./venv/bin/pip install deno
'

echo "==> Creating downloads/ and logs/ directories..."
sudo -u scriptlyai mkdir -p /home/scriptlyai/telegram-media-bot/downloads
sudo -u scriptlyai mkdir -p /home/scriptlyai/telegram-media-bot/logs

echo "==> Installing the systemd service..."
cp /home/scriptlyai/telegram-media-bot/deploy/scriptlyai.service /etc/systemd/system/scriptlyai.service
systemctl daemon-reload

echo ""
echo "=================================================================="
echo "Done. Before starting the bot, you still need to:"
echo "  1. Create /home/scriptlyai/telegram-media-bot/.env (see deploy/README.md)"
echo "  2. Copy models/ (Uzbek/Kazakh/Kyrgyz ASR models) onto this server"
echo "  3. (Optional) Copy over an existing bot.db to keep past user history"
echo ""
echo "Then start it with:"
echo "  systemctl enable --now scriptlyai"
echo "  journalctl -u scriptlyai -f     # watch it start up"
echo "=================================================================="

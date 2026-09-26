# Deploying ScriptlyAI to a fresh server

## 1. Provision the server

SSH into the fresh Ubuntu 24.04 server, then run:

```bash
curl -sL https://raw.githubusercontent.com/mokhivibes/scriptlyai/main/deploy/setup.sh | sudo bash
```

This installs system packages, creates a dedicated `scriptlyai` user, clones the repo, and sets up the Python virtual environment + systemd service. It does **not** start the bot yet - three things need secrets or manual data first.

## 2. Create `.env`

```bash
sudo -u scriptlyai nano /home/scriptlyai/telegram-media-bot/.env
```

Paste in (with your real values):

```
BOT_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
OWNER_USER_ID=960055555
```

## 3. Copy over the local ASR models (~2GB)

From your Mac (not the server), run:

```bash
rsync -avz --progress /Users/mohichehra/telegram-media-bot/models/ root@YOUR_SERVER_IP:/home/scriptlyai/telegram-media-bot/models/
ssh root@YOUR_SERVER_IP "chown -R scriptlyai:scriptlyai /home/scriptlyai/telegram-media-bot/models"
```

This will take a while over the network - it's the biggest single piece of the migration.

## 4. (Optional) Copy over existing user history

If you want to keep transcripts/history from before the migration:

```bash
rsync -avz /Users/mohichehra/telegram-media-bot/bot.db root@YOUR_SERVER_IP:/home/scriptlyai/telegram-media-bot/bot.db
ssh root@YOUR_SERVER_IP "chown scriptlyai:scriptlyai /home/scriptlyai/telegram-media-bot/bot.db"
```

Skip this to start with a clean database instead.

## 5. Start the bot

```bash
sudo systemctl enable --now scriptlyai
sudo journalctl -u scriptlyai -f
```

Watch the log for `Application started` with no errors, same as the local launchd setup.

## Everyday commands (replace `launchctl unload/load` from the Mac)

| Task | Old (launchd) | New (systemd) |
|---|---|---|
| Restart | `launchctl unload` + `launchctl load` | `sudo systemctl restart scriptlyai` |
| Check it's running | `launchctl list \| grep scriptlyai` | `sudo systemctl status scriptlyai` |
| Watch logs | `tail -f logs/launchd.err.log` | `sudo journalctl -u scriptlyai -f` |
| Stop | `launchctl unload` | `sudo systemctl stop scriptlyai` |

## Deploying a code update later

```bash
ssh scriptlyai@YOUR_SERVER_IP
cd telegram-media-bot
git pull
./venv/bin/pip install -r requirements.txt   # only if requirements.txt changed
sudo systemctl restart scriptlyai
```

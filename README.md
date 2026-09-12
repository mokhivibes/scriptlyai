# ScriptlyAI

A Telegram bot that turns a video link into a clean, exportable transcript. Send it a YouTube, Instagram, X/Twitter, or TikTok link; it downloads the audio, transcribes it locally, cleans it up, and hands back a PDF or text file. The whole bot interface (buttons, prompts, errors) is localized into English, Russian, Arabic, and Uzbek.

Runs entirely on local/free tools — no paid APIs. Everything (transcription, cleanup) happens on-device.

## Features

- **Platforms:** YouTube, Instagram, X/Twitter, TikTok (network-permitting — see [Known Limitations](#known-limitations)).
- **Pipeline:** download → extract audio → transcribe (Whisper) → clean up (local LLM) → export (PDF/text).
- **Interface localization:** every bot-facing string (not just the transcript) is available in English, Russian, Arabic, and Uzbek, chosen via `/language` and saved per user.
- **History:** `/history` lists your last 10 transcripts; tap one to reopen it and re-export.
- **Resilient by default:** retry-with-backoff on transient network failures, a per-user busy-guard so concurrent requests can't corrupt each other's state, and a safety net that refuses to let the cleanup step silently drop content.
- **Runs unattended:** deployed via `launchd` on macOS — starts at login, restarts automatically if it crashes.

## Architecture

```
main.py                    Entry point: registers handlers, starts polling
config.py                  Loads BOT_TOKEN from .env
database.py                SQLite (bot.db): users + transcripts, with upsert-safe writes
logging_config.py          Rotating file + console logging (logs/bot.log)

handlers/
  link_handler.py          The core pipeline: link → download → transcribe → clean → export
  command_handler.py       /help, /cancel, /history, /language

services/
  youtube_service.py       yt-dlp wrapper, audio-only download
  twitter_service.py       yt-dlp wrapper for X/Twitter
  tiktok_service.py        yt-dlp wrapper for TikTok (untested from ISP-blocked locations)
  audio_service.py         ffmpeg audio extraction
  speech_service.py        faster-whisper (medium model) transcription
  ai_cleanup_service.py    Local LLM (Ollama, qwen2.5:3b-instruct) cleanup + word-overlap safety net
  export_service.py        PDF (with Arabic RTL shaping) and text export
  translation_service.py   Transcript translation — built but currently unused (see below)

utils/
  messages.py               Locale dispatcher — one function per message type, never crashes on a missing key
  network_retry.py          Retry-with-backoff for Telegram API calls and downloads
  link_detector.py          URL → platform detection
  text_chunker.py           Splits long text across Telegram's 4096-char message limit

locales/
  en.py, ru.py, ar.py, uz.py   One module per language, identical attribute names in each
```

### Why translation isn't in the pipeline

`translation_service.py` (Google Translate via `deep-translator`) is fully implemented but **not called** from the bot. It was removed from the user-facing flow because the free translation backend proved unreliable under real usage (silent rate-limiting causing failures) — PDF/text export of the transcript itself has no such dependency and is fully local, so it was kept as the primary feature and translation was shelved. The file is left in place in case a paid or self-hosted translation backend replaces it later.

### Safety nets worth knowing about

- **Cleanup overlap check** (`ai_cleanup_service.py`): compares word overlap between the raw and cleaned transcript (a global ratio, plus a stricter check on the first/last few words) and falls back to the raw transcript if the LLM appears to have dropped content. It does **not** currently catch the reverse — added/duplicated content (see Known Limitations).
- **Retry logic** (`utils/network_retry.py`): python-telegram-bot retries its own `get_updates` polling loop indefinitely by default, but does **not** retry any outbound call (`reply_text`, `reply_audio`, etc.) — this module fills that gap, distinguishing transient network errors (retry) from permanent ones like `BadRequest` (never retry, since they fail identically every time).
- **Per-user busy-guard** (`link_handler.py`): rejects a second concurrent request from the same user with "still working on your last one" rather than letting two requests race on shared state.

## Setup

### 1. System dependencies (not pip-installable)

- **Python 3.14** (or compatible)
- **ffmpeg / ffprobe** — audio extraction. `brew install ffmpeg` on macOS.
- **Ollama**, running locally with the `qwen2.5:3b-instruct` model pulled:
  ```bash
  brew install ollama
  ollama pull qwen2.5:3b-instruct
  ```
  The model choice is deliberate — `llama3.2:3b` was tried and rejected for poor Arabic support (fabricated output during testing). Ollama must be running (`ollama serve`, or installed as a background service via `brew services start ollama`) before the bot starts.

### 2. Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The first run will also download the Whisper `medium` model (~1.4GB) via `faster-whisper` automatically.

### 3. Configuration

Create a `.env` file in the project root:

```
BOT_TOKEN=your-telegram-bot-token-here
```

Get a token from [@BotFather](https://t.me/BotFather) on Telegram.

### 4. Run it

```bash
python main.py
```

For a bot you don't want to babysit in a terminal, see **Deployment** below.

## Deployment (macOS, via launchd)

The bot is designed to run as a `launchd` LaunchAgent — starts automatically at login, restarts automatically if it crashes.

The agent file lives at `~/Library/LaunchAgents/com.scriptlyai.bot.plist` and points at this project's `venv/bin/python main.py` with `WorkingDirectory` set to the project root (required — the code uses relative paths like `bot.db`, `downloads/`, `logs/`, which would otherwise resolve against `/`).

```bash
# Load it (starts the bot)
launchctl load ~/Library/LaunchAgents/com.scriptlyai.bot.plist

# Check status
launchctl list | grep scriptlyai

# Stop it for real — a plain `kill` or `launchctl stop` gets restarted
# immediately by KeepAlive; unload is what actually stops it
launchctl unload ~/Library/LaunchAgents/com.scriptlyai.bot.plist

# Watch logs
tail -f logs/bot.log
```

This is a **LaunchAgent** (user-level), not a LaunchDaemon (system-level/root) — it starts at login, not at raw power-on before anyone logs in. That's the right tradeoff for a bot that reads `.env` secrets and home-directory files; if you use auto-login, this is effectively invisible.

## Known Limitations

### ASR language misdetection (Uzbek, and some Arabic dialects)

Whisper (`medium` model) has, in real testing, misdetected the *language itself* — not just transcribed poorly:

- A real Uzbek clip was detected as **Kazakh** (confidence 0.59) and transcribed into Kazakh-script gibberish.
- A real Arabic Instagram reel was detected as **Turkish**, also producing garbled output.

Both wrong guesses land on a *linguistically related* language (Uzbek↔Kazakh are both Turkic; the Arabic case↔Turkish) rather than something random — this looks like a systematic pattern in Whisper's language-ID model confusing related languages, not one-off noise. It's possible the larger `large-v3` model would do better (language detection generally improves with model size), but **this is unverified**: a same-day comparison test was time-boxed and stopped when the `large-v3` download stalled (HuggingFace Hub rate-limiting an unauthenticated request), and this machine's available RAM headroom was already borderline even before that, so testing it properly would need both a fix for the download and more free memory than was available at the time.

**Mitigation already in place:** the cleanup safety net (see Architecture) catches the resulting low word-overlap when a misdetection produces nonsense output and falls back to the raw transcript — so a misdetection produces a *visibly wrong-language raw transcript* rather than a confidently-wrong "cleaned" one. This doesn't fix the underlying detection problem, but it prevents the failure mode from being silent or misleadingly polished.

### TikTok — blocked from this development location

TikTok is unreachable from the current dev machine: DNS resolves and a raw TCP handshake to port 443 succeeds, but the actual HTTPS request hangs and times out — consistent with ISP-level deep packet inspection (DPI) filtering, not a code, DNS, or VPN configuration issue. The code path (`services/tiktok_service.py`) mirrors the working X/Twitter implementation and has explicit retry logic, but has never been exercised against a real TikTok URL. Relevant to hosting location if this is deployed elsewhere.

### Facebook — not implemented

Facebook links are detected (`utils/link_detector.py`) but only produce a "coming soon" placeholder — there is no `facebook_service.py`. This is a permanent exclusion for now due to upstream video-extractor reliability issues with Facebook specifically, not a temporary gap like TikTok's network block.

### Cleanup can duplicate repeated/chant-like content — root cause known, not fixed

The AI cleanup step's safety net checks for *dropped* content (via word-overlap ratio) but not *added* content. On a real test, a transcript containing a repeated chant ("USA!" x7) came back from cleanup with extra repetitions (8, then 11 on a re-run) — non-deterministic at first, which pointed at the Ollama call's decoding temperature (unset, defaulting to ~0.8 stochastic decoding).

Setting `temperature=0.2` was tried as a fix (kept in the code — it's harmless and likely helps general run-to-run consistency) but **testing disproved the hypothesis**: at `temperature=0.2` the output became *deterministic* (13 "USA!"s every run) but still *wrong* — not just non-deterministic-wrong, consistently wrong. Testing `temperature=0.0` (fully greedy, zero randomness) against the exact production prompt produced the identical wrong result, ruling out decoding randomness as the cause entirely.

The actual root cause: the prompt's paragraph-organization rules ("divide into 3-5 natural paragraphs... each paragraph 2-4 sentences... insert a blank line between paragraphs") cause the model to redistribute a repeated exclamation/chant across multiple "paragraphs," duplicating it in the process — confirmed by testing a version of the prompt without those rules, which produced the correct count. This is a genuine prompt/model interaction bug in `qwen2.5:3b-instruct`'s handling of repetitive input, not a sampling issue.

**Not fixed.** A real fix would need either an explicit anti-duplication rule in the prompt, softening the paragraph rules for short repetitive segments, or extending the safety net to compare word *counts* (not just overlap/presence) so it catches additions as well as drops. Impact so far has been cosmetic (an extra repeated exclamation) rather than semantic, but the safety net's blind spot to added/duplicated content is the real residual risk here — something could slip through undetected if a future case is less cosmetic than a repeated "USA!".

## Testing

There's no automated test suite (`pytest` et al.) — testing throughout this project has been done via direct, real-condition verification: real downloads against real platform URLs, mocked-but-realistic Telegram `Update`/`CallbackQuery` objects driving the actual handler code for concurrency/retry scenarios, and live spot-checks across all 4 interface languages. See the project's development history for specifics; a from-scratch test suite would be a reasonable next step if this grows beyond single-maintainer use.

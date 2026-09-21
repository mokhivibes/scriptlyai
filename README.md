# ScriptlyAI

A Telegram bot that turns a video link into a clean, exportable transcript. Send it a YouTube, Instagram, X/Twitter, or TikTok link; it downloads the audio, transcribes it, cleans it up, and hands back a PDF or text file. The whole bot interface (buttons, prompts, errors) is localized into English, Russian, Arabic, and Uzbek.

Transcription and cleanup run on [Groq's](https://groq.com) hosted API, on its free tier (no credit card required) — a deliberate switch from an earlier local-only design (faster-whisper + a local Ollama model) made specifically so the bot itself needs almost no RAM/CPU and can run on ordinary free or cheap hosting instead of a dedicated machine. See [Architecture](#why-groq-instead-of-local-inference) for the reasoning and the real tradeoffs that came with it.

## Features

- **Platforms:** YouTube, Instagram, X/Twitter, TikTok (network-permitting — see [Known Limitations](#known-limitations)).
- **Pipeline:** download → extract audio → transcribe (Groq-hosted Whisper) → clean up (Groq-hosted LLM) → export (PDF/text).
- **Interface localization:** every bot-facing string (not just the transcript) is available in English, Russian, Arabic, and Uzbek, chosen via `/language` and saved per user.
- **History:** `/history` lists your last 10 transcripts; tap one to reopen it and re-export.
- **Long-content warning:** before committing to anything over ~90 seconds, the bot checks the duration up front (no download yet) and asks for confirmation, rather than silently making someone wait several minutes for a result — cancelling stops before any download happens.
- **Discoverability:** a logo + greeting on first contact, a persistent shortcuts keyboard (Help/History/Language, localized) always visible below the text input, and a localized command list in Telegram's own chat-menu button.
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
  speech_service.py        Groq-hosted Whisper (large-v3) transcription
  ai_cleanup_service.py    Groq-hosted LLM (openai/gpt-oss-120b) cleanup + word-overlap safety net
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

### Why Groq instead of local inference

This project originally ran faster-whisper (medium model, ~1.4GB) and a local Ollama model entirely on-device — genuinely free, but requiring several GB of RAM to be resident at all times, which ruled out ordinary free/cheap hosting (a $0-7/month VPS, most PaaS free tiers) entirely. Switched to Groq's hosted API (also free, no credit card, rate-limited rather than paid) specifically to remove that requirement.

**Tested before switching, on real content, not assumed:**
- Arabic transcription: as good as local Whisper, slightly better on one real clip (fixed two small grammatical errors local Whisper got wrong).
- Cleanup quality: Groq's `openai/gpt-oss-120b` produced a correct, minimal edit (a single missing comma, no fabrication) on the exact category of content (`qwen2.5:3b-instruct` was chosen for after `llama3.2:3b` was rejected for fabricating Arabic output) — and did it in under a second, versus several seconds to tens of seconds locally.
- Uzbek transcription: **not improved.** See Known Limitations - this was tested across three different Whisper variants (local medium, Groq's turbo, Groq's full large-v3) and all three misdetect the same real Uzbek clip as a different Turkic language. This is a gap in Whisper's own training data, unrelated to local vs. hosted or model size, so the switch doesn't regress anything that wasn't already broken.

One real tradeoff worth naming: this reintroduces an external-service dependency (rate limits, uptime, API changes) for a project that had deliberately avoided that so far, and got burned by exactly this category of risk once already (`translation_service.py` below). Groq's free tier is a clearly-documented, intentional offering rather than a scraped/reverse-engineered one, so it's a different risk profile - but it's not zero.

### Why translation isn't in the pipeline

`translation_service.py` (Google Translate via `deep-translator`) is fully implemented but **not called** from the bot. It was removed from the user-facing flow because the free translation backend proved unreliable under real usage (silent rate-limiting causing failures) — PDF/text export of the transcript itself has no such dependency and is fully local, so it was kept as the primary feature and translation was shelved. The file is left in place in case a paid or self-hosted translation backend replaces it later.

### Safety nets worth knowing about

- **Cleanup overlap check** (`ai_cleanup_service.py`): compares word overlap between the raw and cleaned transcript (a global ratio, plus a stricter check on the first/last few words) and falls back to the raw transcript if the LLM appears to have dropped content. It does **not** currently catch the reverse — added/duplicated content (see Known Limitations).
- **Retry logic** (`utils/network_retry.py`): python-telegram-bot retries its own `get_updates` polling loop indefinitely by default, but does **not** retry any outbound call (`reply_text`, `reply_audio`, etc.) — this module fills that gap, distinguishing transient network errors (retry) from permanent ones like `BadRequest` (never retry, since they fail identically every time).
- **Per-user busy-guard** (`link_handler.py`): rejects a second concurrent request from the same user with "still working on your last one" rather than letting two requests race on shared state.

## Setup

### 1. System dependencies (not pip-installable)

- **Python 3.14** (or compatible)
- **ffmpeg / ffprobe** — audio extraction. `brew install ffmpeg` on macOS, `apt install ffmpeg` on Debian/Ubuntu.

No local ML runtime (Ollama, a Whisper model download) is needed anymore — transcription and cleanup both call Groq's hosted API instead. This is the main reason the bot is light enough to run on ordinary free/cheap hosting; see [Why Groq instead of local inference](#why-groq-instead-of-local-inference).

### 2. Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```
BOT_TOKEN=your-telegram-bot-token-here
GROQ_API_KEY=your-groq-api-key-here
```

Get a Telegram token from [@BotFather](https://t.me/BotFather). Get a free Groq API key at [console.groq.com](https://console.groq.com) → API Keys → Create API Key — no credit card required for the free tier. Treat this key like a password: never commit it, never paste it anywhere public, and rotate it (delete + create a new one) if it's ever exposed in a chat log, screenshot, or shared terminal session.

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

### ASR language misdetection (Arabic dialects, Uzbek)

Whisper (`medium` model) has, in real testing, misdetected the *language itself* — not just transcribed poorly:

- A real Uzbek clip was detected as **Kazakh** (confidence 0.59) and transcribed into Kazakh-script gibberish.
- A second real Uzbek song was detected as **Persian** and transcribed into unreadable Perso-Arabic script nonsense.
- A real Arabic Instagram reel was detected as **Turkish**, also producing garbled output.

These wrong guesses mostly land on *linguistically related* languages (Uzbek↔Kazakh are both Turkic; Uzbek uses a lot of Persian/Arabic loanwords historically; the Arabic case↔Turkish) - though not exclusively, see below - rather than something random, which looked at first like a systematic pattern in Whisper's language-ID model confusing related languages specifically.

**`large-v3` was later tested and confirmed NOT to fix this.** Once the bot switched to Groq's hosted API, testing became trivial: Groq's `whisper-large-v3-turbo` misdetected the same real Uzbek clip as **Turkish** (transcribing almost nothing, apparently deciding it was just background music); Groq's full, non-turbo `whisper-large-v3` misdetected it a third way, as **Azerbaijani**, with a garbled transcript. Separately, two real production requests added a fourth and fifth Whisper failure: misdetected as Kazakh again, and separately as Kyrgyz.

**A completely different ASR provider (AssemblyAI, not Whisper-based) was also tested and also failed - which changes the conclusion.** Auto-detection misdetected the same clip as **Georgian** - not even Turkic, breaking the "always a related language" pattern seen across every Whisper variant. Forcing `language_code="uz"` explicitly produced *consistent* output (byte-identical across repeat runs, unlike Whisper's decoding randomness on this same category of content) - but a native-speaker check of that output confirmed it was still wrong: real Uzbek vocabulary bent into what reads as Azerbaijani orthography and grammar (the schwa letter `ə` and the `-əcək` verb ending aren't part of Uzbek's Latin alphabet at all).

**Eight real failure data points across two independent ASR technologies** (three Whisper variants x multiple runs, plus AssemblyAI auto and forced) confirmed this is a broader gap in mainstream ASR training data for Uzbek, not a Whisper-specific weakness - which is what eventually led to the fix below.

### Uzbek transcription — fixed via a local fallback model

A dedicated Uzbek-specific model (`Kotib/uzbek_stt_v1`, a community Whisper Medium fine-tune, 16.7% WER / 7.0% CER across 8 test sets) turned out to genuinely solve this, once converted to CTranslate2 format and run through `faster-whisper`:

```
ct2-transformers-converter --model Kotib/uzbek_stt_v1 \
  --output_dir models/uzbek_asr \
  --copy_files tokenizer_config.json preprocessor_config.json \
  --quantization float16
```

The raw HuggingFace `transformers` version of this model was unusable on its own - 40-65 minutes to transcribe a 1-minute clip, even with Apple Silicon MPS acceleration. The CTranslate2 conversion runs the identical model at real-time-or-faster speed on CPU alone.

`services/speech_service.py` now routes to this local model automatically, but **not** the same way the earlier reverted fix did. Instead of forcing Uzbek for every Uzbek-interface user (the approach that broke on genuinely English content - see above), the trigger is Groq's own detected language landing in the known misdetection cluster (`kk`, `ky`, `tr`, `fa`, `ka`, `az` - every language every real Uzbek misdetection has ever landed on, across all 8 prior failure points). This is evidence from the audio itself, not a stated preference, so it doesn't touch genuinely non-Uzbek content at all.

Verified against real audio (not simulated): the same "Meni sev" song referenced above, and a separate spoken clip, both now correctly detected as Uzbek with coherent, accurate output, consistent across repeat runs - a real fix, not another false start.

**A same-day fix was tried for Uzbek and then reverted before launch.** Forcing `language="uz"` in `transcribe_audio()` for users whose interface language is Uzbek did produce a dramatic improvement on one real test case (the same "Meni sev" audio went from unreadable Perso-Arabic gibberish to clearly readable, coherent lyrics). But further testing showed the underlying problem is deeper than language selection: **the exact same audio, with the exact same forced language, produced wildly different quality across separate runs** — one clean, one garbled — pointing to genuine randomness in Whisper's own decoding on hard/singing content, not something a language hint reliably fixes. Forcing also carried its own real cost: it measurably tripled processing time on music (~303s forced vs. ~92s auto-detect on the same song), and it would confidently mis-transcribe any genuinely non-Uzbek content a Uzbek-interface user shares, trading one failure mode for another rather than eliminating it. **This was confirmed live**: while the forcing fix was still deployed, a real user with the interface set to Uzbek sent several genuinely English videos, and each was force-transcribed as if it were Uzbek. Given the fix didn't reliably solve the real problem and introduced its own regression, it was reverted — Whisper's plain auto-detection is now used for all 4 interface languages, matching the original behavior.

**What's shipped instead**: the duration-based confirm/cancel warning described above (Features), plus an explicit `/help` disclaimer that music/singing is slower and less reliable than speech. This is honest about the real risk without silently forcing anyone's language or pretending the underlying detection problem is solved.

**Mitigation still in place regardless**: the cleanup safety net (see Architecture) catches the resulting low word-overlap when a misdetection produces nonsense output and falls back to the raw transcript — so a misdetection still produces a *visibly wrong-language raw transcript* rather than a confidently-wrong "cleaned" one.

### TikTok — blocked from this development location

TikTok is unreachable from the current dev machine: DNS resolves and a raw TCP handshake to port 443 succeeds, but the actual HTTPS request hangs and times out — consistent with ISP-level deep packet inspection (DPI) filtering, not a code, DNS, or VPN configuration issue. The code path (`services/tiktok_service.py`) mirrors the working X/Twitter implementation and has explicit retry logic, but has never been exercised against a real TikTok URL. Relevant to hosting location if this is deployed elsewhere.

### Facebook — not implemented

Facebook links are detected (`utils/link_detector.py`) but only produce a "coming soon" placeholder — there is no `facebook_service.py`. This is a permanent exclusion for now due to upstream video-extractor reliability issues with Facebook specifically, not a temporary gap like TikTok's network block.

### Cleanup can duplicate repeated/chant-like content — root cause known, not fixed

**Found on the original local Ollama setup (`qwen2.5:3b-instruct`); not yet retested against Groq's `openai/gpt-oss-120b`** (the replacement model - see [Why Groq instead of local inference](#why-groq-instead-of-local-inference)). The root cause described below is a prompt-structure issue, not a model-specific quirk, so it may well reproduce on any model given the same prompt - but that's an assumption until it's actually tested on a repetitive/chant-like transcript through the new pipeline.

The AI cleanup step's safety net checks for *dropped* content (via word-overlap ratio) but not *added* content. On a real test (on the old local setup), a transcript containing a repeated chant ("USA!" x7) came back from cleanup with extra repetitions (8, then 11 on a re-run) — non-deterministic at first, which pointed at the Ollama call's decoding temperature (unset, defaulting to ~0.8 stochastic decoding).

Setting `temperature=0.2` was tried as a fix (kept in the Groq migration too — it's harmless and likely helps general run-to-run consistency) but **testing disproved the hypothesis**: at `temperature=0.2` the output became *deterministic* (13 "USA!"s every run) but still *wrong* — not just non-deterministic-wrong, consistently wrong. Testing `temperature=0.0` (fully greedy, zero randomness) against the exact production prompt produced the identical wrong result, ruling out decoding randomness as the cause entirely.

The actual root cause: the prompt's paragraph-organization rules ("divide into 3-5 natural paragraphs... each paragraph 2-4 sentences... insert a blank line between paragraphs") cause the model to redistribute a repeated exclamation/chant across multiple "paragraphs," duplicating it in the process — confirmed by testing a version of the prompt without those rules, which produced the correct count. This is a genuine prompt/model interaction bug, not a sampling issue - and since the same prompt now goes to Groq's model unchanged, there's no particular reason to expect it's resolved.

**Not fixed.** A real fix would need either an explicit anti-duplication rule in the prompt, softening the paragraph rules for short repetitive segments, or extending the safety net to compare word *counts* (not just overlap/presence) so it catches additions as well as drops. Impact so far has been cosmetic (an extra repeated exclamation) rather than semantic, but the safety net's blind spot to added/duplicated content is the real residual risk here — something could slip through undetected if a future case is less cosmetic than a repeated "USA!".

## Testing

There's no automated test suite (`pytest` et al.) — testing throughout this project has been done via direct, real-condition verification: real downloads against real platform URLs, mocked-but-realistic Telegram `Update`/`CallbackQuery` objects driving the actual handler code for concurrency/retry scenarios, and live spot-checks across all 4 interface languages. See the project's development history for specifics; a from-scratch test suite would be a reasonable next step if this grows beyond single-maintainer use.

import json
import logging
import os
import re
import subprocess
import threading
import time

import requests

from config import GROQ_API_KEY, GEMINI_API_KEY
from services.audio_service import FFPROBE_PATH
from utils.network_retry import call_sync_with_retry

logger = logging.getLogger(__name__)

# Moved from local faster-whisper (medium model, ~1.4GB, needed several GB
# of RAM to run) to Groq's hosted API - same underlying Whisper architecture,
# but the bot itself no longer needs to load a model at all, which is what
# made it too heavy for ordinary free/cheap hosting. Tested against real
# Arabic and Uzbek content before switching: Arabic held up (slightly
# better than local medium, in fact), Uzbek did not improve - Whisper
# (local medium, Groq's turbo, and Groq's full large-v3 were ALL tested)
# consistently misdetects Uzbek as a different Turkic language (Kazakh,
# Turkish, Azerbaijani, one each) rather than ever identifying it correctly.
# That's a real gap in Whisper's own training data, not something fixed by
# model size or by moving to the cloud - see README Known Limitations. This
# switch doesn't regress that; it was already broken, on every variant.
GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MODEL_NAME = "whisper-large-v3"

# Every real Uzbek misdetection observed across this whole investigation
# (Groq, AssemblyAI, local Whisper - 8+ data points) has landed on one of
# these languages, never anything outside this cluster. Also, separately
# confirmed 2026-09-24: genuinely Kazakh AND genuinely Kyrgyz audio both
# get detected by Groq as "kk" too - Kyrgyz isn't even in Whisper's
# canonical language list, so "ky" here never actually fires; it's kept
# for documentation of the theoretical case. Used below to trigger the
# local Central-Asian-specialist fallbacks ONLY when Groq's own result
# already lands here - unlike the earlier reverted fix (which forced Uzbek
# for every Uzbek-interface user regardless of what the audio actually was,
# and broke on real non-Uzbek content), this is driven by evidence in the
# audio itself, so it doesn't touch genuinely English/Russian/Arabic/etc.
# content at all.
UZBEK_MISDETECTION_CLUSTER = {"kk", "ky", "tr", "fa", "ka", "az"}

# CTranslate2 conversion of Kotib/uzbek_stt_v1 (a community Whisper Medium
# fine-tune on Uzbek speech, 16.7% WER / 7.0% CER across 8 test sets) - the
# raw HuggingFace/transformers version of this model took 40-65 minutes to
# transcribe a 1-minute clip even with MPS acceleration, unusable for a live
# bot. Converted with:
#   ct2-transformers-converter --model Kotib/uzbek_stt_v1 \
#     --output_dir models/uzbek_asr \
#     --copy_files tokenizer_config.json preprocessor_config.json \
#     --quantization float16
# which runs the same model through faster-whisper's CTranslate2 engine
# instead - real-time-or-faster on CPU alone. Verified against real Uzbek
# speech and singing (the "Meni sev" song from README Known Limitations):
# correct language detection both times, coherent accurate Uzbek text,
# consistent across repeat runs.
UZBEK_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "uzbek_asr")

# Lazily loaded - only needed at all when a Groq result lands in the
# misdetection cluster above, so most requests never touch this.
_uzbek_model = None


def _get_uzbek_model():
    global _uzbek_model
    if _uzbek_model is None:
        from faster_whisper import WhisperModel
        _uzbek_model = WhisperModel(UZBEK_MODEL_DIR, device="cpu", compute_type="int8")
    return _uzbek_model


# akuzdeuov/whisper-base.kk (Whisper base fine-tuned on Kazakh) - chosen
# over shyngys879/kazakh-whisper-large-v3-turbo despite the turbo model's
# better training stats, because real testing showed the turbo model
# truncating output and misdetecting language on real audio while this
# smaller base model produced correct, coherent Kazakh consistently (see
# [[keep_digging_past_apparent_fix]] discipline - benchmark numbers alone
# were misleading here). Converted the same way as the Uzbek model:
#   ct2-transformers-converter --model akuzdeuov/whisper-base.kk \
#     --output_dir models/kazakh_asr \
#     --copy_files tokenizer_config.json preprocessor_config.json \
#     --quantization float16
KAZAKH_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "kazakh_asr")

# kyrgyz-ai/AkylAI-STT-small (Whisper small fine-tuned on Kyrgyz). Kyrgyz
# has no code in Whisper's canonical ~99-language list, so this model (and
# Whisper generally) can only be driven via language=None auto-detect,
# where it internally reuses Kazakh's "kk" language-embedding slot - the
# fine-tuning changed the model's output vocabulary even though it didn't
# get its own language token. Converted the same way:
#   ct2-transformers-converter --model kyrgyz-ai/AkylAI-STT-small \
#     --output_dir models/kyrgyz_asr \
#     --copy_files tokenizer_config.json preprocessor_config.json \
#     --quantization float16
KYRGYZ_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "kyrgyz_asr")

_kazakh_model = None
_kyrgyz_model = None


def _get_kazakh_model():
    global _kazakh_model
    if _kazakh_model is None:
        from faster_whisper import WhisperModel
        _kazakh_model = WhisperModel(KAZAKH_MODEL_DIR, device="cpu", compute_type="int8")
    return _kazakh_model


def _get_kyrgyz_model():
    global _kyrgyz_model
    if _kyrgyz_model is None:
        from faster_whisper import WhisperModel
        _kyrgyz_model = WhisperModel(KYRGYZ_MODEL_DIR, device="cpu", compute_type="int8")
    return _kyrgyz_model


# Below this (forced language="uz" decode), the transcript is discarded as
# an unreliable fabrication rather than a real transcription - see
# _try_uzbek_fallback's docstring. Chosen from real measurements: genuine
# Uzbek speech (4 clips, real news audio) scored -0.016 to -0.042; a
# genuinely Kazakh clip and a genuinely Kyrgyz clip - both routed here by
# UZBEK_MISDETECTION_CLUSTER but NOT actually Uzbek - scored -0.378 and
# -0.187. -0.15 sits in the wide gap between those two clusters, closer to
# the false-positive side so a real Uzbek clip has to be unusually noisy
# before this rejects it.
UZBEK_FALLBACK_MIN_AVG_LOGPROB = -0.15

# Shared by all three fallbacks below. Discovered 2026-09-24 testing the
# Kyrgyz fallback: avg_logprob alone is blind to a degenerate decode where
# the model gets stuck repeating one syllable ("Э-э-э-э-э-э-э...") - that
# failure mode scored avg_logprob=-0.014, the single BEST (least negative)
# score across 10 real repeated runs on the same audio, because each
# repeated token is individually "confident" even though the output as a
# whole is garbage. Real good decodes measured compression_ratio 1.7-1.8;
# the repetition-loop failures measured 19.7 - an enormous, unambiguous
# gap. 2.4 matches OpenAI Whisper's own long-established default
# compression_ratio_threshold for exactly this heuristic, and real testing
# here confirms it's nowhere near either cluster.
FALLBACK_MAX_COMPRESSION_RATIO = 2.4


def _try_uzbek_fallback(audio_path: str):
    """
    Runs the local Uzbek-specific model (forced language="uz") and returns
    its transcript - but only if the decode's own average log-probability
    clears UZBEK_FALLBACK_MIN_AVG_LOGPROB, evidence the model is
    confidently transcribing rather than fabricating.

    This model's own free-form language auto-detection turned out to be
    useless as a gate here (tested first, before this): fed genuinely
    Kazakh and Kyrgyz clips - both routed to this fallback by
    UZBEK_MISDETECTION_CLUSTER but not actually Uzbek - it correctly
    refused to call them Uzbek. But fed genuinely correct, clean Uzbek
    news audio, it ALSO refused to call it Uzbek (guessed "zh"/"fr"/"en"
    at 20-40% confidence) - fine-tuning on Uzbek-only data appears to have
    broken this model's free-form language ID entirely, in both
    directions, making it useless as a signal either way.
    forced-decode confidence (avg_logprob) doesn't have that problem: it
    cleanly separated the same two false-positive clips (-0.378, -0.187)
    from four genuine Uzbek segments (-0.016 to -0.042) with a wide,
    unambiguous gap - a forced decode into the wrong language visibly
    struggles even when free-form language ID does not.

    Returns None (keeping Groq's original result) both on any failure
    (missing model directory, load error, etc.) and when confidence is too
    low - either way, this optional quality fallback should never
    override Groq's result with something worse.
    """

    try:
        model = _get_uzbek_model()
        segments, _info = model.transcribe(audio_path, language="uz")
        segments = list(segments)

        if not segments:
            return None

        avg_logprob = sum(segment.avg_logprob for segment in segments) / len(segments)
        if avg_logprob < UZBEK_FALLBACK_MIN_AVG_LOGPROB:
            logger.info(
                f"Uzbek fallback decode confidence too low (avg_logprob={avg_logprob:.3f}) - "
                "discarding, keeping Groq's original result"
            )
            return None

        avg_compression_ratio = sum(segment.compression_ratio for segment in segments) / len(segments)
        if avg_compression_ratio > FALLBACK_MAX_COMPRESSION_RATIO:
            logger.info(
                f"Uzbek fallback decode looks degenerate/repetitive (compression_ratio="
                f"{avg_compression_ratio:.3f}) - discarding, keeping Groq's original result"
            )
            return None

        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text or None
    except Exception:
        logger.exception("Uzbek fallback transcription failed - keeping Groq's result")
        return None


# Real measurements (2026-09-24): genuine Kyrgyz audio, decoded with this
# model via auto-detect (language=None - see KYRGYZ_MODEL_DIR's comment),
# scored -0.134; the same genuine-Kazakh and genuine-Uzbek clips used to
# calibrate the other two fallbacks scored -0.303 and -0.282 through THIS
# model. -0.2 sits in that gap. Unlike the Kazakh threshold below, this
# one separates cleanly - closely related as Kazakh and Kyrgyz are, this
# model's own confidence still tells them apart.
KYRGYZ_FALLBACK_MIN_AVG_LOGPROB = -0.2


def _try_kyrgyz_fallback(audio_path: str):
    """
    Runs the local Kyrgyz-specific model via auto-detect (forcing a
    language isn't possible - see KYRGYZ_MODEL_DIR's comment) and returns
    its transcript if confidence clears KYRGYZ_FALLBACK_MIN_AVG_LOGPROB
    AND it isn't a degenerate repetition loop (FALLBACK_MAX_COMPRESSION_
    RATIO - this is the model where that failure mode was actually caught,
    see that constant's comment). Same reasoning as _try_uzbek_fallback
    otherwise: returns None (keep Groq's result) on any failure or low
    confidence.
    """

    try:
        model = _get_kyrgyz_model()
        segments, info = model.transcribe(audio_path, language=None)
        segments = list(segments)

        if not segments:
            return None

        avg_logprob = sum(segment.avg_logprob for segment in segments) / len(segments)
        if avg_logprob < KYRGYZ_FALLBACK_MIN_AVG_LOGPROB:
            logger.info(
                f"Kyrgyz fallback decode confidence too low (avg_logprob={avg_logprob:.3f}, "
                f"detected={info.language}) - discarding, keeping Groq's original result"
            )
            return None

        avg_compression_ratio = sum(segment.compression_ratio for segment in segments) / len(segments)
        if avg_compression_ratio > FALLBACK_MAX_COMPRESSION_RATIO:
            logger.info(
                f"Kyrgyz fallback decode looks degenerate/repetitive (compression_ratio="
                f"{avg_compression_ratio:.3f}) - discarding, keeping Groq's original result"
            )
            return None

        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text or None
    except Exception:
        logger.exception("Kyrgyz fallback transcription failed - keeping Groq's result")
        return None


# Real measurements (2026-09-24): genuine Kazakh audio, forced language="kk"
# through this model, scored -0.056; a genuine Uzbek clip scored -0.170
# through it (clear gap). BUT a genuine Kyrgyz clip scored -0.072 through
# it - nearly indistinguishable from the true-Kazakh score, because Kazakh
# and Kyrgyz are close enough that forcing "kk" on Kyrgyz speech still
# decodes fluently (just wrong). This threshold can NOT reliably tell
# real Kazakh from real Kyrgyz on its own - see transcribe_audio(), which
# only reaches this fallback after _try_kyrgyz_fallback has already had
# first chance to claim the audio (Kyrgyz's own gate above separates
# cleanly), substantially - but not perfectly - reducing that risk rather
# than eliminating it.
KAZAKH_FALLBACK_MIN_AVG_LOGPROB = -0.12


def _try_kazakh_fallback(audio_path: str):
    """
    Runs the local Kazakh-specific model (forced language="kk") and
    returns its transcript if confidence clears
    KAZAKH_FALLBACK_MIN_AVG_LOGPROB. See that constant's comment for the
    known Kazakh/Kyrgyz confusability this can't fully rule out on its
    own - call this AFTER _try_kyrgyz_fallback has already had a chance,
    not standalone. Same reasoning otherwise as _try_uzbek_fallback:
    returns None (keep Groq's result) on any failure or low confidence.
    """

    try:
        model = _get_kazakh_model()
        segments, _info = model.transcribe(audio_path, language="kk")
        segments = list(segments)

        if not segments:
            return None

        avg_logprob = sum(segment.avg_logprob for segment in segments) / len(segments)
        if avg_logprob < KAZAKH_FALLBACK_MIN_AVG_LOGPROB:
            logger.info(
                f"Kazakh fallback decode confidence too low (avg_logprob={avg_logprob:.3f}) - "
                "discarding, keeping Groq's original result"
            )
            return None

        avg_compression_ratio = sum(segment.compression_ratio for segment in segments) / len(segments)
        if avg_compression_ratio > FALLBACK_MAX_COMPRESSION_RATIO:
            logger.info(
                f"Kazakh fallback decode looks degenerate/repetitive (compression_ratio="
                f"{avg_compression_ratio:.3f}) - discarding, keeping Groq's original result"
            )
            return None

        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text or None
    except Exception:
        logger.exception("Kazakh fallback transcription failed - keeping Groq's result")
        return None

# --- Gemini 3.5 Transcribe (first choice for the Uzbek cluster) ---
#
# Measured 2026-10-26 on a real 2.5-minute Uzbek reel: Gemini returned a
# clean, correct transcript in ~3s, versus ~18 minutes for the three local
# models run one after another on the production VPS (a shared 4-vCPU CPU
# decodes Whisper-medium at ~4.5x slower than real time). Its free tier
# allows only 3 generate requests per minute per project, so calls are
# serialized and spaced below. Auto-detection returns an empty transcript
# (a known Google-side bug), so the three candidate languages are passed
# as hints instead - given all three it picked Uzbek on the Uzbek clip.
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"
GEMINI_MODEL = "gemini-3.5-transcribe"
GEMINI_LANGUAGE_HINTS = ["uz-UZ", "kk-KZ", "ky-KG"]
GEMINI_MIN_SECONDS_BETWEEN_CALLS = 21  # 3 requests/minute on the free tier
GEMINI_MAX_RATE_LIMIT_RETRIES = 2
GEMINI_MAX_AUDIO_SECONDS = 55 * 60  # the model accepts up to 1 hour per request
GEMINI_REQUEST_TIMEOUT = 180
GEMINI_DAILY_QUOTA_PAUSE_SECONDS = 3600

# Without Gemini, the slow local models only run on clips short enough to
# finish in a few minutes - longer ones keep Groq's own result instead.
LOCAL_FALLBACK_MAX_SECONDS = 60

_GEMINI_MIME_TYPES = {
    ".mp3": "audio/mp3", ".wav": "audio/wav", ".ogg": "audio/ogg", ".oga": "audio/ogg",
    ".opus": "audio/ogg", ".m4a": "audio/mp4", ".mp4": "audio/mp4", ".flac": "audio/flac",
    ".aac": "audio/aac",
}

_gemini_lock = threading.Lock()
_gemini_last_call_at = 0.0
_gemini_paused_until = 0.0

# Letters that exist in Kazakh but not Kyrgyz; Kyrgyz shares only ү/ө/ң.
_KAZAKH_ONLY_LETTERS = set("әғқһіӘҒҚҺІ")


# Standard Uzbek Cyrillic -> Latin mapping, used only to tidy stray Cyrillic
# words inside an otherwise-Latin Uzbek transcript (see _try_gemini_fallback).
_CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "s",
    "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "'", "ь": "", "ы": "i", "э": "e", "ю": "yu",
    "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}


def _latinize_stray_cyrillic(text: str) -> str:
    def convert_word(match):
        word = match.group(0)
        out = "".join(_CYRILLIC_TO_LATIN.get(ch.lower(), ch) for ch in word)
        # Keep a leading capital ("Голубика" -> "Golubika"); ALL-CAPS words stay upper.
        if word.isupper() and len(word) > 1:
            return out.upper()
        return out[:1].upper() + out[1:] if word[:1].isupper() else out

    return re.sub(r"[\u0400-\u04ff]+", convert_word, text)


def _get_audio_duration_seconds(audio_path: str):
    try:
        result = subprocess.run(
            [FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, timeout=30,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def _language_from_script(text: str) -> str:
    """Gemini doesn't report which language it chose, so infer a label from
    the script: Latin -> Uzbek, Kazakh-only Cyrillic letters -> Kazakh,
    other Cyrillic -> Kyrgyz. Only a label (history/export), not a decision."""
    cyrillic = sum(1 for ch in text if "\u0400" <= ch <= "\u04ff")
    latin = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if latin >= cyrillic:
        return "uz"
    return "kk" if any(ch in _KAZAKH_ONLY_LETTERS for ch in text) else "ky"


def _gemini_upload(audio_path: str, headers: dict):
    mime = _GEMINI_MIME_TYPES.get(os.path.splitext(audio_path)[1].lower(), "audio/mp3")
    with open(audio_path, "rb") as audio_file:
        data = audio_file.read()

    start = requests.post(
        f"{GEMINI_BASE_URL}/upload/v1beta/files",
        headers={**headers, "X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                 "X-Goog-Upload-Header-Content-Length": str(len(data)),
                 "X-Goog-Upload-Header-Content-Type": mime, "Content-Type": "application/json"},
        json={"file": {"display_name": "audio"}}, timeout=60,
    )
    start.raise_for_status()
    upload = requests.post(
        start.headers["x-goog-upload-url"],
        headers={"Content-Length": str(len(data)), "X-Goog-Upload-Offset": "0",
                 "X-Goog-Upload-Command": "upload, finalize"},
        data=data, timeout=GEMINI_REQUEST_TIMEOUT,
    )
    upload.raise_for_status()
    file_info = upload.json()["file"]

    for _ in range(30):
        if file_info.get("state") != "PROCESSING":
            break
        time.sleep(2)
        file_info = requests.get(f"{GEMINI_BASE_URL}/v1beta/{file_info['name']}", headers=headers, timeout=30).json()

    return file_info, mime


def _try_gemini_fallback(audio_path: str):
    """
    Transcribes with Gemini 3.5 Transcribe, hinting Uzbek/Kazakh/Kyrgyz.
    Returns (text, language_label), or None on ANY failure (no key, quota,
    rate limit exhausted, empty result, network) so the caller carries on to
    the local models / Groq's own result - this must never make things worse.

    The uploaded copy is deleted from Google's side right after use.
    Calls are serialized and spaced to stay under the free tier's
    3 requests/minute; a daily-quota error pauses Gemini for an hour so
    users aren't made to wait on a call that can't succeed.
    """

    global _gemini_last_call_at, _gemini_paused_until

    if not GEMINI_API_KEY or time.time() < _gemini_paused_until:
        return None

    duration = _get_audio_duration_seconds(audio_path)
    if duration is not None and duration > GEMINI_MAX_AUDIO_SECONDS:
        logger.info(f"Audio too long for Gemini ({duration:.0f}s) - skipping")
        return None

    headers = {"x-goog-api-key": GEMINI_API_KEY}
    file_name = None

    try:
        file_info, mime = _gemini_upload(audio_path, headers)
        file_name = file_info.get("name")
        body = {
            "contents": [{"parts": [{"fileData": {"fileUri": file_info["uri"], "mimeType": mime}}]}],
            "generationConfig": {"audioTranscriptionConfig": {"languageCodes": GEMINI_LANGUAGE_HINTS}},
        }

        for attempt in range(GEMINI_MAX_RATE_LIMIT_RETRIES + 1):
            with _gemini_lock:
                wait = GEMINI_MIN_SECONDS_BETWEEN_CALLS - (time.time() - _gemini_last_call_at)
                if wait > 0:
                    time.sleep(wait)
                _gemini_last_call_at = time.time()
                response = requests.post(
                    f"{GEMINI_BASE_URL}/v1beta/models/{GEMINI_MODEL}:generateContent",
                    headers=headers, json=body, timeout=GEMINI_REQUEST_TIMEOUT,
                )

            if response.status_code == 429:
                if "PerDay" in response.text:
                    _gemini_paused_until = time.time() + GEMINI_DAILY_QUOTA_PAUSE_SECONDS
                    logger.warning("Gemini daily free quota exhausted - pausing Gemini for an hour")
                    return None
                logger.info(f"Gemini rate limited (attempt {attempt + 1}) - retrying")
                continue

            response.raise_for_status()
            parts = (response.json().get("candidates") or [{}])[0].get("content", {}).get("parts", [])
            text = " ".join(
                part.get("audioTranscription", {}).get("text", "") for part in parts
            ).strip()

            if not text:
                logger.info("Gemini returned an empty transcript - falling back")
                return None
            language = _language_from_script(text)
            if language == "uz":
                text = _latinize_stray_cyrillic(text)
            return text, language

        logger.warning("Gemini still rate limited after retries - falling back")
        return None
    except Exception:
        logger.exception("Gemini transcription failed - falling back")
        return None
    finally:
        if file_name:
            try:
                requests.delete(f"{GEMINI_BASE_URL}/v1beta/{file_name}", headers=headers, timeout=30)
            except Exception:
                logger.warning("Could not delete the uploaded audio from Gemini's file store")


# Groq's API returns the detected language as a full English name (e.g.
# "English", "Arabic") - local faster-whisper returned a two-letter ISO
# 639-1 code (e.g. "en", "ar"), which the rest of the codebase (export's
# Arabic RTL check, history labels via TARGET_LANGUAGE_NAMES) was built
# around and still expects. This is Whisper's own canonical language list
# (the same ~99 languages every Whisper variant supports, local or hosted),
# so this mapping is stable regardless of which Whisper backend is used.
_LANGUAGE_NAME_TO_CODE = {
    "english": "en", "chinese": "zh", "german": "de", "spanish": "es",
    "russian": "ru", "korean": "ko", "french": "fr", "japanese": "ja",
    "portuguese": "pt", "turkish": "tr", "polish": "pl", "catalan": "ca",
    "dutch": "nl", "arabic": "ar", "swedish": "sv", "italian": "it",
    "indonesian": "id", "hindi": "hi", "finnish": "fi", "vietnamese": "vi",
    "hebrew": "he", "ukrainian": "uk", "greek": "el", "malay": "ms",
    "czech": "cs", "romanian": "ro", "danish": "da", "hungarian": "hu",
    "tamil": "ta", "norwegian": "no", "thai": "th", "urdu": "ur",
    "croatian": "hr", "bulgarian": "bg", "lithuanian": "lt", "latin": "la",
    "maori": "mi", "malayalam": "ml", "welsh": "cy", "slovak": "sk",
    "telugu": "te", "persian": "fa", "latvian": "lv", "bengali": "bn",
    "serbian": "sr", "azerbaijani": "az", "slovenian": "sl", "kannada": "kn",
    "estonian": "et", "macedonian": "mk", "breton": "br", "basque": "eu",
    "icelandic": "is", "armenian": "hy", "nepali": "ne", "mongolian": "mn",
    "bosnian": "bs", "kazakh": "kk", "albanian": "sq", "swahili": "sw",
    "galician": "gl", "marathi": "mr", "punjabi": "pa", "sinhala": "si",
    "khmer": "km", "shona": "sn", "yoruba": "yo", "somali": "so",
    "afrikaans": "af", "occitan": "oc", "georgian": "ka", "belarusian": "be",
    "tajik": "tg", "sindhi": "sd", "gujarati": "gu", "amharic": "am",
    "yiddish": "yi", "lao": "lo", "uzbek": "uz", "faroese": "fo",
    "haitian creole": "ht", "pashto": "ps", "turkmen": "tk", "nynorsk": "nn",
    "maltese": "mt", "sanskrit": "sa", "luxembourgish": "lb", "myanmar": "my",
    "tibetan": "bo", "tagalog": "tl", "malagasy": "mg", "assamese": "as",
    "tatar": "tt", "hawaiian": "haw", "lingala": "ln", "hausa": "ha",
    "bashkir": "ba", "javanese": "jw", "sundanese": "su",
}


def _normalize_language_code(language_name):
    if not language_name:
        return None
    return _LANGUAGE_NAME_TO_CODE.get(language_name.lower(), language_name.lower())


NO_SPEECH_THRESHOLD = 0.6


def _transcribe(audio_path: str, language: str = None):
    with open(audio_path, "rb") as audio_file:
        data = {"model": MODEL_NAME, "response_format": "verbose_json"}
        if language:
            data["language"] = language

        response = requests.post(
            GROQ_TRANSCRIPTION_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            files={"file": audio_file},
            data=data,
            timeout=120,
        )

    response.raise_for_status()
    result = response.json()
    text = result.get("text", "").strip()

    # Whisper hallucinates short filler ("you", ".") on silence/noise/music.
    # Measured on Groq: real speech -> no_speech_prob 0.0, silence 0.7,
    # pure tone 1.0; 0.6 is Whisper's own standard threshold. Return empty
    # text so the caller can tell the user there was nothing to transcribe.
    segments = result.get("segments") or []
    all_no_speech = bool(segments) and all(s.get("no_speech_prob", 0) > NO_SPEECH_THRESHOLD for s in segments)
    if all_no_speech or not any(ch.isalnum() for ch in text):
        text = ""

    return text, _normalize_language_code(result.get("language"))


# Tried in this order when Groq's detection lands in the cluster - Kyrgyz
# first because its own confidence gate is the only one of the three that
# reliably separates true-positive from false-positive (see
# KYRGYZ_FALLBACK_MIN_AVG_LOGPROB's comment); trying it first means
# genuinely Kyrgyz audio gets claimed before ever reaching the Kazakh
# fallback, whose own gate can't fully tell real Kazakh from real Kyrgyz
# apart. First candidate whose confidence clears its own threshold wins;
# if none do, Groq's original result stands.
_FALLBACK_CANDIDATES = (
    ("ky", _try_kyrgyz_fallback),
    ("kk", _try_kazakh_fallback),
    ("uz", _try_uzbek_fallback),
)


def transcribe_audio(audio_path: str, language: str = None, on_uzbek_fallback_start=None):
    """
    Convert an audio file into text using Groq's hosted Whisper API.

    If a language is provided, Whisper uses that language. Otherwise, it
    automatically detects the language.

    When auto-detection lands on a language in UZBEK_MISDETECTION_CLUSTER,
    the local Kyrgyz/Kazakh/Uzbek specialist models each get a turn (see
    _FALLBACK_CANDIDATES) re-transcribing the same audio - see
    UZBEK_MISDETECTION_CLUSTER's comment for why this is safe to do
    unconditionally (it's triggered by the audio's own detected language,
    not by any stated user preference). If every fallback fails or comes
    back low-confidence, Groq's original result is kept rather than
    surfacing an error - this is a quality improvement, not a required
    step.

    on_uzbek_fallback_start, if given, is called (no arguments) right
    before the first local model starts - the caller's chance to update a
    status message, since this step is real CPU work (35s-2min+ per
    candidate tried) with no progress of its own to report in between.
    Any exception it raises is swallowed - a failed status update should
    never break the actual transcription it's trying to describe. Kept
    this name (not renamed to something cluster-generic) since the
    message it triggers already reads correctly for any of the three
    candidates - see locales' TRANSCRIBING_UZBEK_FALLBACK.
    """

    text, detected_language = call_sync_with_retry(_transcribe, audio_path, language=language)

    if language is None and text and detected_language in UZBEK_MISDETECTION_CLUSTER:
        logger.info(f"Groq detected '{detected_language}' (in Uzbek misdetection cluster) - trying local fallbacks")

        if on_uzbek_fallback_start:
            try:
                on_uzbek_fallback_start()
            except Exception:
                logger.exception("on_uzbek_fallback_start callback failed - continuing with transcription")

        gemini_result = _try_gemini_fallback(audio_path)
        if gemini_result:
            return gemini_result

        duration = _get_audio_duration_seconds(audio_path)
        if duration is not None and duration > LOCAL_FALLBACK_MAX_SECONDS:
            logger.info(
                f"Gemini unavailable and audio is {duration:.0f}s - too long for the slow local "
                "models, keeping Groq's result"
            )
            return text, detected_language

        for candidate_language, try_fallback in _FALLBACK_CANDIDATES:
            fallback_text = try_fallback(audio_path)
            if fallback_text:
                return fallback_text, candidate_language

    return text, detected_language

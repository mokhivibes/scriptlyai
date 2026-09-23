import logging
import os

import requests

from config import GROQ_API_KEY
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
# these languages, never anything outside this cluster. Used below to
# trigger a local Uzbek-specific fallback ONLY when Groq's own result
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

        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text or None
    except Exception:
        logger.exception("Uzbek fallback transcription failed - keeping Groq's result")
        return None

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

    return result.get("text", "").strip(), _normalize_language_code(result.get("language"))


def transcribe_audio(audio_path: str, language: str = None, on_uzbek_fallback_start=None):
    """
    Convert an audio file into text using Groq's hosted Whisper API.

    If a language is provided, Whisper uses that language. Otherwise, it
    automatically detects the language.

    When auto-detection lands on a language in UZBEK_MISDETECTION_CLUSTER,
    a local Uzbek-specific model re-transcribes the same audio - see that
    constant's comment for why this is safe to do unconditionally (it's
    triggered by the audio's own detected language, not by any stated user
    preference). If the fallback fails for any reason, Groq's original
    result is kept rather than surfacing an error - this is a quality
    improvement, not a required step.

    on_uzbek_fallback_start, if given, is called (no arguments) right
    before the local model starts - the caller's chance to update a status
    message, since this step is real CPU work (35s-2min+ depending on
    clip length) with no progress of its own to report in between. Any
    exception it raises is swallowed - a failed status update should never
    break the actual transcription it's trying to describe.
    """

    text, detected_language = call_sync_with_retry(_transcribe, audio_path, language=language)

    if language is None and detected_language in UZBEK_MISDETECTION_CLUSTER:
        logger.info(f"Groq detected '{detected_language}' (in Uzbek misdetection cluster) - trying local Uzbek fallback")

        if on_uzbek_fallback_start:
            try:
                on_uzbek_fallback_start()
            except Exception:
                logger.exception("on_uzbek_fallback_start callback failed - continuing with transcription")

        fallback_text = _try_uzbek_fallback(audio_path)
        if fallback_text:
            return fallback_text, "uz"

    return text, detected_language

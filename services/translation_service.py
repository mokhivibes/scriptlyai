import html
import logging
import time

from deep_translator import GoogleTranslator, MyMemoryTranslator
from deep_translator.exceptions import (
    ElementNotFoundInGetRequest,
    RequestError,
    ServerException,
    TooManyRequests,
    TranslationNotFound,
)

from utils.text_chunker import split_into_chunks, join_chunks

logger = logging.getLogger(__name__)


# Exceptions the Google backend can raise that look transient (server-side
# hiccups, formatting quirks on a particular request) rather than a
# permanent problem with the input - worth retrying rather than failing
# the whole transcript over one bad request. Observed live: TranslationNotFound
# on an otherwise valid ~4400 character chunk that succeeded on a later retry.
RETRYABLE_EXCEPTIONS = (
    TranslationNotFound,
    RequestError,
    ServerException,
    TooManyRequests,
    ElementNotFoundInGetRequest,
)


# MyMemoryTranslator (deep-translator's other free, no-API-key backend)
# uses locale-style codes (en-GB, not en) - only the 4 languages this bot
# actually supports need mapping here, not deep-translator's full list.
MYMEMORY_LANGUAGE_CODES = {
    "en": "en-GB",
    "ru": "ru-RU",
    "ar": "ar-SA",
    "uz": "uz-UZ",
}


LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Russian",
    "ar": "Arabic",
    "uz": "Uzbek",
}

# deep-translator's Google backend hard-rejects text at exactly 5000 chars
# (raises NotValidLength). Chunk comfortably under that so a long transcript
# doesn't fail translation entirely.
TRANSLATE_CHUNK_MAX_CHARS = 4500

# The free Google Translate endpoint deep-translator uses can, without
# raising an exception, return an HTML error page's text as if it were a
# real translation (observed live: "Error 500 (Server Error)...That's an
# error..."). Detect that and retry rather than silently embedding it into
# the transcript.
TRANSLATION_ERROR_MARKERS = (
    "error 500 (server error)",
    "that’s an error",
    "that's an error",
)
# This free endpoint has been observed to fail transiently in bursts under
# heavy request volume (the same chunk that failed 3 times in a row
# succeeded seconds later in isolation) - use exponential backoff so a
# short burst of rate-limiting doesn't exhaust all retries too quickly.
MAX_RETRIES = 4
RETRY_DELAY_SECONDS = 3

# MyMemoryTranslator hard-rejects text over 500 chars (raises
# NotValidLength) - a MUCH smaller limit than Google's ~5000. Discovered
# live 2026-09-25: Google's free endpoint hit a real, sustained
# TooManyRequests rate-limit window, and the MyMemory fallback - meant to
# be the safety net for exactly this - turned out to have been silently
# broken the whole time for any chunk longer than 500 chars, because it
# was being handed chunks sized for Google's limit (up to
# TRANSLATE_CHUNK_MAX_CHARS=4500) and immediately raising NotValidLength
# on all of them. 450 leaves a small safety margin under the real 500 cap.
MYMEMORY_CHUNK_MAX_CHARS = 450


def _looks_like_translation_error(result: str) -> bool:
    lowered = result.lower()
    return any(marker in lowered for marker in TRANSLATION_ERROR_MARKERS)


def _looks_like_passthrough_failure(chunk: str, result: str, source_language: str, target_language: str) -> bool:
    """
    Google's endpoint can also fail silently by echoing the source text back
    unchanged instead of translating it (observed live: language
    auto-detection failing on informal/dialectal Arabic speech). Passing an
    explicit source_language (from Whisper) avoids this, but this is a
    second line of defense in case that language is ever wrong or missing.

    Only flags real prose that came back byte-identical between two
    different languages - short fragments, numbers, and same-language
    requests can legitimately be returned unchanged.
    """

    if source_language == target_language:
        return False

    meaningful_chars = sum(1 for ch in chunk if ch.isalpha())
    if meaningful_chars < 15:
        return False

    return result.strip() == chunk.strip()


def _translate_chunk_fallback(chunk: str, source_language: str, target_language: str):
    """
    MyMemoryTranslator as a last resort after GoogleTranslator's own
    retries are exhausted - a different free, no-API-key backend (a
    translation-memory lookup, not full neural MT, so quality can be
    inconsistent on uncommon phrases - real-tested example: "patience"
    came back as the Arabic word for "patents" on one request). Used
    only as a fallback so the common case still gets Google's better
    quality; an imperfect translation beats a hard failure on the rare
    case both matter (this project's real, repeated observation is that
    Google's free endpoint is rate-limit-fragile under sustained use,
    not that it's usually wrong - see README).
    """

    mymemory_source = MYMEMORY_LANGUAGE_CODES.get(source_language)
    mymemory_target = MYMEMORY_LANGUAGE_CODES.get(target_language)

    if not mymemory_source or not mymemory_target:
        return None

    # `chunk` arrives sized for Google (up to TRANSLATE_CHUNK_MAX_CHARS=
    # 4500) - re-split it further for MyMemory's much smaller 500-char
    # limit, translate each piece, then rejoin. Almost every real chunk
    # needs this (4500 >> 500), so skipping it (as the code used to do)
    # meant this fallback was effectively never usable in practice.
    sub_chunks, sub_separators = split_into_chunks(chunk, max_chars=MYMEMORY_CHUNK_MAX_CHARS)
    if not sub_chunks:
        return None

    translator = MyMemoryTranslator(source=mymemory_source, target=mymemory_target)
    translated_sub_chunks = []

    try:
        for i, sub_chunk in enumerate(sub_chunks):
            if i > 0:
                time.sleep(0.5)
            # MyMemory's API has been observed to HTML-encode punctuation
            # in its response (an apostrophe/quote in the source text
            # coming back as literal "&#39;"/"&quot;" - real example, seen
            # 2026-09-25 live) - unescape() is a safe no-op when there's
            # nothing to decode.
            translated_sub_chunks.append(html.unescape(translator.translate(sub_chunk)))
    except Exception:
        logger.exception("MyMemory fallback translation also failed")
        return None

    result = join_chunks(translated_sub_chunks, sub_separators)

    if _looks_like_translation_error(result) or _looks_like_passthrough_failure(
        chunk, result, source_language, target_language
    ):
        return None

    return result


def _translate_chunk(translator: GoogleTranslator, chunk: str, source_language: str, target_language: str) -> str:
    last_result = None
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            result = translator.translate(chunk)
        except RETRYABLE_EXCEPTIONS as error:
            last_exception = error
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS * (2 ** attempt))
            continue

        if not _looks_like_translation_error(result) and not _looks_like_passthrough_failure(
            chunk, result, source_language, target_language
        ):
            return result

        last_result = result
        last_exception = None
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY_SECONDS * (2 ** attempt))

    logger.warning(
        f"GoogleTranslator exhausted {MAX_RETRIES} attempts "
        f"({source_language}->{target_language}) - trying MyMemory fallback"
    )
    fallback_result = _translate_chunk_fallback(chunk, source_language, target_language)
    if fallback_result is not None:
        return fallback_result

    if last_exception is not None:
        raise RuntimeError(
            f"Translation service kept raising {type(last_exception).__name__} "
            f"after {MAX_RETRIES} attempts, and the MyMemory fallback also "
            f"failed: {last_exception}"
        ) from last_exception

    raise RuntimeError(
        f"Translation service failed to translate a chunk after {MAX_RETRIES} "
        f"attempts (error page or untranslated passthrough), and the "
        f"MyMemory fallback also failed: {last_result!r}"
    )


def translate_text(text: str, target_language: str, source_language: str = "auto"):
    """
    Translate text into the selected target language.

    Long text is split into chunks (at paragraph/sentence boundaries where
    possible) to stay under deep-translator's ~5000 character limit per
    request, translated chunk by chunk, then reassembled in order.

    source_language should be the language Whisper already detected
    (e.g. "ar") whenever it's known - Google's own auto-detect ("auto") has
    been observed to fail silently on informal/dialectal Arabic speech,
    returning the untranslated source text with no error at all.
    """

    translator = GoogleTranslator(source=source_language, target=target_language)

    chunks, separators = split_into_chunks(text, max_chars=TRANSLATE_CHUNK_MAX_CHARS)

    if not chunks:
        return ""

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            # A small courtesy delay between requests - back-to-back calls to
            # this free endpoint have been observed to trigger a soft
            # rate-limit that silently returns an HTML error page.
            time.sleep(0.5)
        translated_chunks.append(_translate_chunk(translator, chunk, source_language, target_language))

    return join_chunks(translated_chunks, separators)
import time

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    ElementNotFoundInGetRequest,
    RequestError,
    ServerException,
    TooManyRequests,
    TranslationNotFound,
)

from utils.text_chunker import split_into_chunks, join_chunks


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

    if last_exception is not None:
        raise RuntimeError(
            f"Translation service kept raising {type(last_exception).__name__} "
            f"after {MAX_RETRIES} attempts: {last_exception}"
        ) from last_exception

    raise RuntimeError(
        f"Translation service failed to translate a chunk after {MAX_RETRIES} "
        f"attempts (error page or untranslated passthrough): {last_result!r}"
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
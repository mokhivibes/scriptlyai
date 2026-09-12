import logging
import re
from collections import Counter

import requests

logger = logging.getLogger(__name__)


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b-instruct"

# If the cleaned transcript shares fewer than this fraction of the raw
# transcript's words, treat the cleanup as unreliable (likely fabrication,
# summarization, or dropped content) and fall back to the raw transcript.
MIN_OVERLAP_RATIO = 0.6

# The global ratio above can hide dropped content at the very start/end of
# a transcript, since a couple of missing words barely move the average
# once the transcript is long. Models tend to drop content disproportionately
# at these edges (treating an opening phrase as "throat-clearing" to reword,
# or trailing off near the end), so check the boundaries separately with a
# stricter threshold, regardless of overall transcript length.
BOUNDARY_WINDOW = 5
# Checked with <=, not <: a single word dropped from a 5-word boundary
# window (4/5 = 0.8) must fail too. A raw-transcript fallback is low-cost -
# the user still gets accurate, if less polished, content - while a dropped
# word at an opening/closing is exactly the high-cost failure this check
# exists to catch, so this side is intentionally strict.
BOUNDARY_MIN_OVERLAP = 0.8


# Arabic diacritics (tashkeel) and the tatweel elongation character - these
# carry no word-identity information, so strip them before comparing.
ARABIC_DIACRITICS_PATTERN = re.compile(r"[ً-ْـ]")


def _normalize_arabic(text: str) -> str:
    # Different hamza/alef forms (أ إ آ ٱ) are the same letter for our
    # purposes - a legitimate AI correction (e.g. "اهمية" -> "أهمية") should
    # not look like fabrication just because the hamza was added/fixed.
    text = re.sub(r"[إأآٱ]", "ا", text)
    text = ARABIC_DIACRITICS_PATTERN.sub("", text)

    # Taa marbuta (ة) and haa (ه) sound identical in pausal speech and are
    # frequently interchanged by ASR ("اهميه" vs "اهمية") - taa marbuta only
    # ever appears word-finally in Arabic, so this substitution is safe and
    # doesn't collide with genuine word-final haa letters.
    text = text.replace("ة", "ه")

    # Whisper often transcribes the attached conjunction "و" (and) or "ف"
    # (then) as its own token ("و كيف"), while a correct cleanup attaches it
    # to the next word as proper Arabic orthography requires ("وكيف"). Join
    # them here so both forms normalize identically - otherwise a legitimate
    # attachment fix looks like a dropped/fabricated word.
    text = re.sub(r"\b(و|ف)\s+(?=\S)", r"\1", text)

    return text


# Casual/typed Russian frequently drops the dots on ё in favor of е (the two
# sound different but are treated as interchangeable in everyday writing) -
# a legitimate correction that adds/removes the dots shouldn't look like a
# different word.
def _normalize_russian(text: str) -> str:
    return text.replace("ё", "е")


# Uzbek oʻ/gʻ are typed with many different apostrophe-like characters
# across sources - a plain apostrophe ('), curly quotes (' '), or the
# "correct" modifier letters (ʻ ʼ ʿ) all represent the same sound, and it's
# often omitted by typists entirely. Strip them all so every variant
# ("oʻzbek", "o'zbek", "o'zbek", "ozbek") normalizes identically.
UZBEK_APOSTROPHE_PATTERN = re.compile(r"[ʻʼʿ''`´]")


def _normalize_uzbek(text: str) -> str:
    return UZBEK_APOSTROPHE_PATTERN.sub("", text)


def _normalize_words(text: str):
    text = text.lower()
    text = _normalize_arabic(text)
    text = _normalize_russian(text)
    text = _normalize_uzbek(text)
    text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    return text.split()


def _survival_ratio(word_slice, cleaned_counts: Counter) -> float:
    """
    What fraction of `word_slice` (a list of already-normalized words,
    possibly with duplicates) can be found in `cleaned_counts`.
    """

    if not word_slice:
        return 1.0

    slice_counts = Counter(word_slice)
    matched = sum(min(count, cleaned_counts[word]) for word, count in slice_counts.items())

    return matched / len(word_slice)


def is_cleanup_trustworthy(raw_transcript: str, cleaned_transcript: str, min_overlap: float = MIN_OVERLAP_RATIO) -> bool:
    """
    Compare the raw and cleaned transcript for dropped/fabricated content.

    Even Qwen2.5 3B has occasionally fabricated or dropped content on
    classical Arabic religious text, so this acts as a safety net with two
    independent checks - either one failing falls back to the raw transcript:

    1. Global word overlap: catches wholesale fabrication or summarization.
    2. Boundary overlap: the global ratio barely moves when just a couple of
       words are dropped from a long transcript, which is exactly where
       models tend to drop content (an opening phrase reworded away, or a
       trailing-off ending) - so the first/last few words are checked
       separately with a stricter threshold, regardless of overall length.
    """

    raw_words = _normalize_words(raw_transcript)

    if not raw_words:
        return True

    cleaned_counts = Counter(_normalize_words(cleaned_transcript))

    overlap_ratio = _survival_ratio(raw_words, cleaned_counts)
    if overlap_ratio < min_overlap:
        return False

    window = min(BOUNDARY_WINDOW, len(raw_words))
    opening = raw_words[:window]
    closing = raw_words[-window:]

    if _survival_ratio(opening, cleaned_counts) <= BOUNDARY_MIN_OVERLAP:
        return False

    if _survival_ratio(closing, cleaned_counts) <= BOUNDARY_MIN_OVERLAP:
        return False

    return True


def clean_transcript(transcript: str):
    """
    Clean a Whisper transcript using a local Ollama AI model.

    The AI should correct transcription/grammar errors while
    preserving the original meaning and wording.
    """

    prompt = f"""
You are an expert speech transcript editor.

Clean and organize the transcript below while preserving the speaker's original message.

The transcript was created by automatic speech recognition, so it may contain:
- misspelled words
- incorrect words
- missing punctuation
- repeated words
- incorrect sentence boundaries
- words that sound similar to the intended word

Use the surrounding context to identify and correct obvious transcription errors.

STRICT RULES:

1. Return ONLY the cleaned transcript. Do not return anything else.
2. Do NOT add a heading.
3. Do NOT add an introduction.
4. Do NOT add an explanation.
5. Do NOT say what you corrected.
6. Do NOT summarize the transcript.
7. Do NOT rewrite the transcript in your own style.
8. Do NOT add new ideas or information.
9. Preserve the speaker's original meaning.
10. Preserve the speaker's original wording whenever it is understandable.
11. Correct obvious speech-recognition errors only when the intended word is clearly supported by the existing transcript.
12. NEVER add a sentence, phrase, fact, idea, quotation, interpretation, or information that is not already present in the transcript.
13. NEVER continue, complete, or expand the speaker's message.
14. NEVER guess what the speaker might have said based on general knowledge or context outside the transcript.
15. Before returning the transcript, compare the result with the original transcript and make sure every sentence in the result comes from the original transcript or is a direct correction of an existing sentence.
16. Correct obvious grammar mistakes.
17. Correct spelling mistakes.
18. Fix punctuation.
19. Fix spacing.
20. Fix sentence boundaries.
21. Remove accidental repeated words when they are clearly duplicates.
22. If a word or phrase is genuinely unclear, DO NOT invent a replacement. Keep it as close to the original as possible.
23. Do not change names, religious references, places, numbers, or other specific information unless the correction is clearly obvious.
24. Keep the transcript in the same language as the original transcript.
25. Divide the transcript into 3-5 natural paragraphs when the transcript is long enough.
26. Each paragraph should contain 2-4 related sentences and represent one complete idea or thought.
27. You MUST insert a blank line between paragraphs.
28. Do NOT put the entire transcript into one paragraph when multiple ideas are present.
29. Do NOT create a new paragraph after every sentence.
30. Do NOT use bullet points or numbered lists unless the speaker clearly used a list.
31. Do NOT add quotation marks unless they are present in the original speech.
32. Never output special model-control tokens such as </s>, <s>, or similar tokens.
<TRANSCRIPT>
{transcript}
</TRANSCRIPT>

Return ONLY the cleaned and naturally formatted transcript.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            # Low temperature, not the default (~0.8) stochastic decoding -
            # found via real testing that default decoding lets the model
            # hallucinate extra repetitions on chant-like/repetitive input
            # (a transcript with "USA!" x7 came back with 8, then 11 on a
            # re-run, non-deterministically). This is a correction task, not
            # creative writing, so low temperature costs nothing here.
            "options": {"temperature": 0.2},
        },
        timeout=300,
    )

    response.raise_for_status()

    result = response.json()

    cleaned = result["response"].strip()
    if cleaned.startswith("IMPORTANT:"):
        cleaned = cleaned[len("IMPORTANT:"):].strip()

    # If the model repeats part of the prompt, keep only the answer
    # after the required heading.
    heading_variations = [
        "Here is the cleaned transcript:",
        "Here is the cleaned and edited transcript:",
        "Cleaned transcript:",
        "Clean transcript:",
    ]

    for heading in heading_variations:
        position = cleaned.lower().find(heading.lower())

        if position != -1:
            cleaned = cleaned[position + len(heading):].strip()
            break

    # Remove common AI explanations added after the transcript.
    explanation_markers = [
        "\nI corrected",
        "\nI have corrected",
        "\nI made",
        "\nChanges made:",
        "\nCorrections made:",
    ]

    for marker in explanation_markers:
        position = cleaned.find(marker)

        if position != -1:
            cleaned = cleaned[:position].strip()

   # Create natural paragraphs from the cleaned transcript.
    sentences = cleaned.replace("! ", "!|").replace("? ", "?|").replace(". ", ".|").split("|")
    paragraphs = []
    for i in range(0, len(sentences), 3):
        paragraph = " ".join(sentences[i:i + 3]).strip()
        if paragraph:
            paragraphs.append(paragraph)
    cleaned = "\n\n".join(paragraphs)

    if not is_cleanup_trustworthy(transcript, cleaned):
        logger.warning("Cleanup safety net triggered: word overlap too low, falling back to raw transcript")
        return transcript

    return cleaned



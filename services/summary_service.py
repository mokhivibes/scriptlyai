import logging
import re
from collections import Counter

from utils.network_retry import call_sync_with_retry
from utils.text_chunker import split_into_chunks
from services.groq_chat import chat as groq_chat
from services.speech_service import gemini_generate_text

logger = logging.getLogger(__name__)

# Languages Groq's model summarizes badly (it misreads Uzbek and can get stuck
# repeating one word) - Gemini goes first for these, Groq is the fallback.
GEMINI_FIRST_LANGUAGES = ("uz", "kk", "ky")

# Under this many words a "summary" would only repeat the text.
MIN_WORDS_TO_SUMMARIZE = 30

# Each Groq call must fit its 8,000-tokens-per-minute budget (see
# ai_cleanup_service.py); Gemini has a far larger window, so it takes the
# whole text in one call (fewer calls against its small daily free quota).
SUMMARY_CHUNK_CHARS = 5000
GEMINI_WHOLE_TEXT_CHARS = 60000

SUMMARY_MAX_TOKENS = 1500


class SummaryTooShort(ValueError):
    pass


def _bullet_range(words: int):
    """How many bullets suit a text of this size - a 16-minute talk deserves
    more than a 30-second clip."""
    if words < 120:
        return 2, 3
    if words < 500:
        return 3, 5
    if words < 1500:
        return 5, 7
    return 6, 9


def _language_instruction(language):
    if language == "uz":
        return "the SAME language as the transcript (Uzbek, Latin letters, written with o' and g')"
    return "the SAME language as the transcript"


def _final_prompt(text: str, words: int, language) -> str:
    low, high = _bullet_range(words)
    return f"""
You are summarizing a cleaned speech transcript for someone who has not heard it.

FORMAT (follow exactly):
- First, ONE sentence stating the main point of the whole recording.
- Then a blank line.
- Then {low} to {high} bullet points, each starting with "• ", in the order the topics come up.
- Each bullet is one complete, self-contained point that keeps the concrete details
  (names, numbers, places, steps, advice) rather than vague generalities.

STRICT RULES:
1. Return ONLY the summary - no heading, no introduction, no closing remark.
2. Use ONLY what is in the transcript. Never add facts, opinions or context.
3. Paraphrase concisely; do not copy long passages.
4. Plain text only - no markdown symbols such as ** or #.
5. Write in {_language_instruction(language)}.
6. If the transcript is a song or poem, say what it is about and its mood.
7. Never repeat the same word or phrase over and over.

<TRANSCRIPT>
{text}
</TRANSCRIPT>
"""


def _piece_prompt(text: str, language) -> str:
    """One slice of a long recording: detailed notes, merged later."""
    return f"""
You are taking notes on ONE PART of a longer speech transcript.

Write 4 to 6 bullet points, each starting with "• ", covering the key points of this
part in order, keeping the concrete details (names, numbers, places, steps, advice).

STRICT RULES:
1. Return ONLY the bullets - no heading or commentary.
2. Use ONLY what is in this part. Never add facts or opinions.
3. Plain text only - no markdown symbols such as ** or #.
4. Write in {_language_instruction(language)}.
5. Never repeat the same word or phrase over and over.

<TRANSCRIPT_PART>
{text}
</TRANSCRIPT_PART>
"""


def _is_sane(summary: str, source: str) -> bool:
    """Rejects the failure modes seen in real use: empty output, output as
    long as the source, and a model stuck repeating one word."""

    if not summary or not summary.strip():
        return False
    if len(summary) > max(1000, int(len(source) * 0.8)) or len(summary) > 3500:
        return False

    words = re.findall(r"\w+", summary.lower())
    if not words:
        return False

    # Same word several times in a row ("qo'rqinchli qo'rqinchli ...").
    run = 1
    for previous, current in zip(words, words[1:]):
        run = run + 1 if current == previous and len(current) > 2 else 1
        if run >= 4:
            return False

    # One long word making up a big share of the whole summary.
    long_words = [w for w in words if len(w) >= 5]
    if len(long_words) >= 12:
        top_count = Counter(long_words).most_common(1)[0][1]
        if top_count / len(long_words) > 0.25:
            return False

    return True


def _clean(summary: str, language=None) -> str:
    """Normalizes what the model returned into plain text with "• " bullets."""

    if language == "uz":
        # Models write o‘ g‘ ma’no with curly marks; the rest of the pipeline
        # (and the old/new alphabet conversion) uses the plain apostrophe.
        summary = re.sub("[‘’ʻʼ`´]", "'", summary)

    for heading in ("Summary:", "Here is a summary:", "Here's a summary:"):
        position = summary.lower().find(heading.lower())
        if position != -1 and position < 40:
            summary = summary[position + len(heading):]
            break

    summary = summary.replace("**", "").replace("__", "")
    lines = []
    for line in summary.strip().splitlines():
        line = line.rstrip()
        line = re.sub(r"^\s*(?:[-*–—]|\d+[.)])\s+", "• ", line)
        line = re.sub(r"^#+\s*", "", line)
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _groq(prompt: str, temperature: float = 0.3) -> str:
    return call_sync_with_retry(groq_chat, prompt, temperature, SUMMARY_MAX_TOKENS)


def _gemini(prompt: str):
    return gemini_generate_text(prompt, temperature=0.3, max_tokens=SUMMARY_MAX_TOKENS)


def _generate(prompt: str, source: str, language, gemini_first: bool):
    """Runs the prompt on the preferred model, then the other one, and
    returns the first answer that passes the sanity check."""

    providers = [("gemini", _gemini), ("groq", _groq)] if gemini_first else [("groq", _groq), ("gemini", _gemini)]
    for name, provider in providers:
        try:
            result = provider(prompt)
        except Exception as error:
            logger.warning(f"Summary via {name} failed ({type(error).__name__}) - trying the other model")
            continue
        if result:
            cleaned = _clean(result, language)
            if _is_sane(cleaned, source):
                return cleaned
            logger.warning(f"Summary via {name} rejected by the sanity check - trying the other model")
    raise RuntimeError("No model produced a usable summary")


def summarize_transcript(transcript: str, language=None) -> str:
    """
    Summarizes a transcript of any length, in the transcript's own language:
    a one-sentence main point plus bullets, scaled to how much was said.
    Long ones are summarized piece by piece and the notes merged, so the result
    covers the whole recording, not just its start. Uzbek-type languages go to
    Gemini first (Groq's model misreads them); every call falls back to the
    other model.
    """

    text = transcript.strip()
    words = len(text.split())
    if words < MIN_WORDS_TO_SUMMARIZE:
        raise SummaryTooShort("Too short to summarize")

    gemini_first = language in GEMINI_FIRST_LANGUAGES

    # One call whenever the model can take the whole text.
    limit = GEMINI_WHOLE_TEXT_CHARS if gemini_first else SUMMARY_CHUNK_CHARS
    if len(text) <= limit:
        return _generate(_final_prompt(text, words, language), text, language, gemini_first)

    chunks, _ = split_into_chunks(text, max_chars=SUMMARY_CHUNK_CHARS)
    notes = []
    for chunk in chunks:
        notes.append(_generate(_piece_prompt(chunk, language), chunk, language, gemini_first))
    merged = "\n".join(notes)

    # A very long recording's notes can themselves be long - condense them first.
    for _ in range(3):
        if len(merged) <= SUMMARY_CHUNK_CHARS:
            break
        pieces, _unused = split_into_chunks(merged, max_chars=SUMMARY_CHUNK_CHARS)
        merged = "\n".join(_generate(_piece_prompt(piece, language), piece, language, gemini_first) for piece in pieces)

    # The final bullet count follows the length of the ORIGINAL recording.
    return _generate(_final_prompt(merged, words, language), merged, language, gemini_first)

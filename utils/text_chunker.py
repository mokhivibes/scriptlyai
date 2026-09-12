import re


PARAGRAPH_BREAK = "\n\n"

# Sentence-ending punctuation shared across all languages the bot supports:
# ".", "!", "?" (English/Russian/Uzbek) and "؟" (Arabic question mark).
SENTENCE_END_PATTERN = re.compile(r"(?<=[.!?؟])\s+")


def _split_paragraph_into_sentences(paragraph: str):
    paragraph = paragraph.strip()
    if not paragraph:
        return []
    return [s.strip() for s in SENTENCE_END_PATTERN.split(paragraph) if s.strip()]


def _split_long_sentence(sentence: str, max_chars: int):
    """
    Fallback for a single sentence longer than max_chars (e.g. no punctuation
    for a long stretch): break it on whitespace so no piece exceeds the limit.
    """

    words = sentence.split(" ")
    parts = []
    current = ""

    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) > max_chars and current:
            parts.append(current)
            current = word
        else:
            current = candidate

    if current:
        parts.append(current)

    return parts


def _flatten(text: str, max_chars: int):
    """
    Break text into (piece, join) pairs in order, where `join` says how the
    piece attaches to whatever came before it: "start" (first piece overall),
    "paragraph" (first piece of a new paragraph), or "space" (continues the
    same paragraph/sentence).
    """

    flat = []

    for paragraph in text.split(PARAGRAPH_BREAK):
        sentences = _split_paragraph_into_sentences(paragraph)
        for sentence_index, sentence in enumerate(sentences):
            pieces = (
                [sentence]
                if len(sentence) <= max_chars
                else _split_long_sentence(sentence, max_chars)
            )
            for piece_index, piece in enumerate(pieces):
                if not flat:
                    join = "start"
                elif piece_index == 0 and sentence_index == 0:
                    join = "paragraph"
                else:
                    join = "space"
                flat.append((piece, join))

    return flat


def split_into_chunks(text: str, max_chars: int = 4500):
    """
    Split text into chunks no longer than max_chars, preferring to break at
    paragraph boundaries, then sentence boundaries, and only breaking
    mid-sentence (on whitespace) if a single sentence itself exceeds
    max_chars.

    Returns (chunks, separators): separators[i] is the text that belongs
    between chunks[i] and chunks[i+1] when reassembling ("\\n\\n" if that
    break was a real paragraph break, " " if it was a forced mid-sentence
    split), so a round trip like:

        "".join(chunk + sep for chunk, sep in zip(chunks, separators)) + chunks[-1]

    reconstructs the original text.
    """

    if not text or not text.strip():
        return [], []

    flat = _flatten(text, max_chars)

    chunks = []
    separators = []
    current_pieces = []
    current_len = 0

    def render(pieces):
        out = []
        for i, (piece, join) in enumerate(pieces):
            if i == 0:
                out.append(piece)
            elif join == "paragraph":
                out.append(PARAGRAPH_BREAK + piece)
            else:
                out.append(" " + piece)
        return "".join(out)

    for piece, join in flat:
        extra = 0 if not current_pieces else (len(PARAGRAPH_BREAK) if join == "paragraph" else 1)
        projected = current_len + extra + len(piece)

        if current_pieces and projected > max_chars:
            chunks.append(render(current_pieces))
            separators.append(PARAGRAPH_BREAK if join == "paragraph" else " ")
            current_pieces = [(piece, "start")]
            current_len = len(piece)
        else:
            current_pieces.append((piece, join))
            current_len = projected

    if current_pieces:
        chunks.append(render(current_pieces))

    return chunks, separators


def join_chunks(chunks, separators):
    if not chunks:
        return ""

    parts = [chunks[0]]
    for chunk, separator in zip(chunks[1:], separators):
        parts.append(separator)
        parts.append(chunk)

    return "".join(parts)

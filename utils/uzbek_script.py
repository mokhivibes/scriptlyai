"""
Uzbek script handling.

Inside the pipeline Uzbek text is kept in the long-established Latin
orthography (oʻ gʻ sh ch) - that's what the cleanup LLM, the word-overlap
safety net, Google Translate and the summary model all understand. Only
what the USER sees (result message, Copy, PDF, text file, summaries,
translations into Uzbek) is shown in the revised alphabet signed into law
on 2026-10-21, which replaces those four with single letters:
oʻ -> ö, gʻ -> ğ, sh -> ş, ch -> ç (the law takes effect six months after
publication, but the owner wants the new letters now - flip
UZBEK_NEW_ALPHABET in config.py to go back).

Also converts Cyrillic Uzbek (which Gemini sometimes returns) to Latin.
"""

import re

from config import UZBEK_NEW_ALPHABET

# --- Cyrillic -> Latin (pipeline orthography) ---

_CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "'", "ь": "", "ы": "i", "э": "e", "ю": "yu",
    "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}

# Uzbek writes "е" as "ye" at the start of a word and after a vowel.
_YE_AFTER = set("аеёиоуўэюяыАЕЁИОУЎЭЮЯЫ")

_CYRILLIC_RUN = re.compile(r"[Ѐ-ӿ]+")


def _convert_cyrillic_word(word: str) -> str:
    out = []
    for i, ch in enumerate(word):
        lower = ch.lower()
        if lower == "е" and (i == 0 or word[i - 1] in _YE_AFTER):
            replacement = "ye"
        else:
            replacement = _CYRILLIC_TO_LATIN.get(lower, ch)

        if ch.isupper() and replacement:
            next_is_upper = i + 1 < len(word) and word[i + 1].isupper()
            replacement = replacement.upper() if (next_is_upper or len(word) == 1) else replacement.capitalize()
        out.append(replacement)
    return "".join(out)


def cyrillic_to_latin(text: str) -> str:
    return _CYRILLIC_RUN.sub(lambda m: _convert_cyrillic_word(m.group(0)), text)


# --- Latin (oʻ gʻ sh ch) <-> revised alphabet (ö ğ ş ç) ---

# Apostrophe forms that mean the letter oʻ/gʻ. Deliberately excludes ʼ
# (U+02BC), the proper tutuq/glottal mark, so "ma'no"-style words that use it
# aren't turned into ö/ğ.
_OG_APOSTROPHE = re.compile(r"([oOgG])['`‘’ʻ]")
_DIGRAPH = re.compile(r"sh|ch", re.IGNORECASE)

_OG_TO_NEW = {"o": "ö", "O": "Ö", "g": "ğ", "G": "Ğ"}


def _digraph_to_new(match) -> str:
    chunk = match.group(0)
    letter = "ş" if chunk[0] in "sS" else "ç"
    return letter.upper() if chunk[0].isupper() else letter


def latin_to_new_alphabet(text: str) -> str:
    text = _OG_APOSTROPHE.sub(lambda m: _OG_TO_NEW[m.group(1)], text)
    return _DIGRAPH.sub(_digraph_to_new, text)


_NEW_TO_LATIN = {"ş": "sh", "ç": "ch", "ö": "o'", "ğ": "g'", "Ş": "Sh", "Ç": "Ch", "Ö": "O'", "Ğ": "G'"}
_NEW_LETTERS = re.compile(r"[şçöğŞÇÖĞ]")


def new_alphabet_to_latin(text: str) -> str:
    def convert(match):
        letter = match.group(0)
        replacement = _NEW_TO_LATIN[letter]
        # Inside an ALL-CAPS word keep the whole replacement upper-case.
        before = text[match.start() - 1] if match.start() > 0 else ""
        after = text[match.end()] if match.end() < len(text) else ""
        if letter.isupper() and (before.isupper() or after.isupper()):
            return replacement.upper()
        return replacement

    return _NEW_LETTERS.sub(convert, text)


def display_alphabet(text: str) -> str:
    """Pipeline Latin -> what the user sees."""
    return latin_to_new_alphabet(text) if UZBEK_NEW_ALPHABET else text


def pipeline_alphabet(text: str) -> str:
    """What the user sees -> pipeline Latin (for translating/summarizing it)."""
    return new_alphabet_to_latin(text)

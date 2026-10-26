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


def default_alphabet() -> str:
    return "new" if UZBEK_NEW_ALPHABET else "old"


def user_alphabet(saved) -> str:
    """The user's saved choice ('new'/'old'), or the default if they never chose."""
    return saved if saved in ("new", "old") else default_alphabet()


def render_uzbek(text: str, alphabet: str) -> str:
    """
    Text in EITHER form (stored history may be the old spelling or the new
    one) -> the chosen alphabet. Going through the old Latin first makes this
    safe to apply repeatedly and to text of unknown form.
    """
    latin = new_alphabet_to_latin(text)
    return latin_to_new_alphabet(latin) if alphabet == "new" else latin


def pipeline_alphabet(text: str) -> str:
    """What the user sees -> pipeline Latin (for translating/summarizing it)."""
    return new_alphabet_to_latin(text)


# --- Interface text ---

# Parts of a UI string that must never be converted: format placeholders,
# /commands, @handles, URLs, and English words used inside Uzbek sentences.
_UI_PROTECTED = re.compile(r"(\{[^}]*\}|/[A-Za-z_]+|@\w+|https?://\S+|\bEnglish\b)")


def ui_text(text: str) -> str:
    """One interface string -> the new alphabet, leaving placeholders,
    /commands, @handles and URLs untouched."""
    pieces = _UI_PROTECTED.split(text)
    return "".join(piece if i % 2 else latin_to_new_alphabet(piece) for i, piece in enumerate(pieces))


def convert_ui_value(value):
    """Deep-converts every string inside a locale constant (str, list, tuple,
    dict values); anything else - style flags, sentinels - is left alone."""
    if isinstance(value, str):
        return ui_text(value)
    if isinstance(value, list):
        return [convert_ui_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(convert_ui_value(item) for item in value)
    if isinstance(value, dict):
        return {key: convert_ui_value(item) for key, item in value.items()}
    return value


def apply_new_alphabet_to_locale(module):
    """Converts the Uzbek locale module's constants in place (once). The
    ALPHABET_* button labels are skipped - they deliberately show BOTH
    alphabets side by side."""
    if getattr(module, "_UI_ALPHABET_APPLIED", False):
        return
    for name in dir(module):
        if name.startswith("_") or name.startswith("ALPHABET_") or not name.isupper():
            continue
        setattr(module, name, convert_ui_value(getattr(module, name)))
    module._UI_ALPHABET_APPLIED = True

import os

from config import BOT_USERNAME

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF


# Bundled in the repo (assets/fonts/, SIL Open Font License - free to
# redistribute) rather than relying on a system font path, after
# discovering the previous approach (macOS's Arial Unicode.ttf) doesn't
# exist at all on Linux - would have broken PDF export silently the
# moment this ran anywhere but a Mac. Two separate files/font names
# rather than one "kitchen sink" font: Noto Sans covers Latin + Cyrillic
# well but not Arabic at all, and a dedicated Arabic font (Noto Sans
# Arabic) renders Arabic script better than a single pan-Unicode font
# would anyway. export_to_pdf() switches between them based on
# is_arabic - see there.
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
FONT_PATH_LATIN = os.path.join(FONT_DIR, "NotoSans-Regular.ttf")
FONT_PATH_ARABIC = os.path.join(FONT_DIR, "NotoSansArabic-Regular.ttf")
FONT_NAME_LATIN = "ExportFontLatin"
FONT_NAME_ARABIC = "ExportFontArabic"

EXPORT_DIR = "downloads"

PAGE_MARGIN = 15
LINE_HEIGHT = 8
PARAGRAPH_SPACING = 4


def _wrap_line(pdf: FPDF, text: str, max_width: float):
    """
    Wrap text into lines that fit max_width, measured in the text's
    original (logical) character order and word boundaries. This must
    happen BEFORE any Arabic reshaping/bidi reordering - wrapping
    already-reordered text would break on the wrong boundaries.
    """

    words = text.split(" ")
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else current + " " + word
        if pdf.get_string_width(candidate) > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    return lines


def _for_display(line: str, is_arabic: bool) -> str:
    """
    fpdf2 draws glyphs in logical string order with no shaping of its own.
    Arabic needs contextual letter-shaping (arabic_reshaper) and
    right-to-left reordering (python-bidi) or it renders as backwards,
    disconnected letters.
    """

    if not is_arabic or not line.strip():
        return line

    return get_display(arabic_reshaper.reshape(line))


def export_to_pdf(text: str, filepath: str, language_code: str = "en"):
    is_arabic = language_code == "ar"
    align = "R" if is_arabic else "L"

    pdf = FPDF()
    pdf.set_margins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
    pdf.add_page()
    pdf.add_font(FONT_NAME_LATIN, "", FONT_PATH_LATIN)
    pdf.add_font(FONT_NAME_ARABIC, "", FONT_PATH_ARABIC)
    pdf.set_font(FONT_NAME_ARABIC if is_arabic else FONT_NAME_LATIN, size=13)

    max_width = pdf.w - 2 * PAGE_MARGIN

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        for line in _wrap_line(pdf, paragraph, max_width):
            pdf.cell(0, LINE_HEIGHT, _for_display(line, is_arabic), align=align, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(PARAGRAPH_SPACING)

    pdf.set_font(FONT_NAME_LATIN, size=10)
    pdf.cell(0, LINE_HEIGHT, BOT_USERNAME, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.output(filepath)
    return filepath


def export_to_text(text: str, filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{text}\n\n— {BOT_USERNAME}\n")
    return filepath

import os

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF


# macOS system font covering Latin, Cyrillic, and Arabic in one file - needed
# because the transcript/translation can be in any of the 4 supported
# languages. Not bundled in the repo (it's a licensed system font); if this
# ever runs on a machine without it, swap in a free alternative such as
# Noto Sans + Noto Naskh Arabic.
FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"
FONT_NAME = "ExportFont"

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
    pdf.add_font(FONT_NAME, "", FONT_PATH)
    pdf.set_font(FONT_NAME, size=13)

    max_width = pdf.w - 2 * PAGE_MARGIN

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        for line in _wrap_line(pdf, paragraph, max_width):
            pdf.cell(0, LINE_HEIGHT, _for_display(line, is_arabic), align=align, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(PARAGRAPH_SPACING)

    pdf.output(filepath)
    return filepath


def export_to_text(text: str, filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    return filepath

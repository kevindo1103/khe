"""Detect whether a PDF is scanned (image-based) or digital (has text layer).

DEC-049: Route scanned PDFs through Document AI OCR hybrid pipeline,
digital PDFs through embedded-text extraction (pdftotext, ~0đ).
"""

from __future__ import annotations

import subprocess
import tempfile


def is_scanned_pdf(file_bytes: bytes, *, min_chars_per_page: int = 50) -> bool:
    """Return True if the PDF appears to be a scanned document (no usable text layer).

    Heuristic: run ``pdftotext`` and check if the extracted text has
    fewer than *min_chars_per_page* meaningful characters per page on average.
    Garbled OCR output (common from simple PDF text layers on scans) is counted
    as characters, so a very low threshold is used.

    Falls back to True (assume scanned) if pdftotext is unavailable or fails.
    """
    if file_bytes[:4] != b"%PDF":
        return False

    try:
        text, page_count = _extract_text_pdftotext(file_bytes)
    except (FileNotFoundError, subprocess.SubprocessError):
        return True

    if page_count == 0:
        return True

    meaningful = sum(1 for c in text if c.isalnum())
    avg_chars = meaningful / page_count
    return avg_chars < min_chars_per_page


_VIET_DIACRITICALS = set(
    "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    "ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ"
)

_GARBLE_THRESHOLD = 0.02


def is_garbled_vietnamese(text: str) -> bool:
    """Return True if text looks garbled — pdftotext failed to decode Vietnamese diacritics.

    Normal Vietnamese text has ~8-15% diacritical characters.
    Garbled text (custom font encoding not decoded) has <2%.
    """
    alpha_count = sum(1 for c in text if c.isalpha())
    if alpha_count < 100:
        return False
    diac_count = sum(1 for c in text if c in _VIET_DIACRITICALS)
    return (diac_count / alpha_count) < _GARBLE_THRESHOLD


def extract_embedded_text(file_bytes: bytes) -> str | None:
    """Extract text from a digital PDF using pdftotext.

    Returns None if pdftotext is unavailable or the PDF has no text layer.
    """
    if file_bytes[:4] != b"%PDF":
        return None
    try:
        text, _ = _extract_text_pdftotext(file_bytes)
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if not text or not text.strip():
        return None
    return text


def _extract_text_pdftotext(file_bytes: bytes) -> tuple[str, int]:
    """Run pdftotext on PDF bytes, return (text, page_count)."""
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp.flush()

        result = subprocess.run(
            ["pdftotext", "-layout", tmp.name, "-"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            raise subprocess.SubprocessError(
                f"pdftotext exited with code {result.returncode}"
            )
        text = result.stdout

        info = subprocess.run(
            ["pdfinfo", tmp.name],
            capture_output=True, text=True, timeout=10,
        )
        page_count = 0
        for line in info.stdout.splitlines():
            if line.startswith("Pages:"):
                page_count = int(line.split(":", 1)[1].strip())
                break

    return text, page_count

"""Tests for PDF-specific fallback chain — no claude_haiku for PDFs (#436, QC #435)."""
from modules.extraction.factory import _resolve_chain


def test_pdf_chain_excludes_haiku():
    """prefer='hybrid_ocr' (PDFs) never falls through to claude_haiku."""
    chain = _resolve_chain("hybrid_ocr")
    assert "claude_haiku" not in chain
    assert chain == ("hybrid_ocr", "gemini_flash")


def test_image_chain_keeps_haiku():
    """prefer='gemini_flash' (images) still falls back to claude_haiku."""
    chain = _resolve_chain("gemini_flash")
    assert chain == ("gemini_flash", "claude_haiku")


def test_prefer_claude_haiku_directly_unaffected():
    """Explicitly preferring claude_haiku (e.g. image path) still resolves normally."""
    chain = _resolve_chain("claude_haiku")
    assert "claude_haiku" in chain
    assert chain[0] == "claude_haiku"


def test_unknown_prefer_raises():
    import pytest
    with pytest.raises(ValueError):
        _resolve_chain("not_a_provider")

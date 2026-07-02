"""Tests for MAX_TOKENS truncation handling (#446, mini-sprint #443).

A Gemini MAX_TOKENS truncation must keep the document retryable with a clear
"document too large" message — never advance to another Gemini-backed provider
(ratified trade-off, #443 — accepted even though a different provider/mode is
not guaranteed to hit the same wall) and never silently succeed with
truncated content.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.tenant import Document, Event
from app.services.extraction_runner import run_extraction
from modules.extraction import is_max_tokens_truncation


def _make_doc(db, tenant_id, file_name="contract.pdf", status="pending"):
    doc = Document(
        tenant_id=tenant_id,
        file_name=file_name,
        file_path=f"{tenant_id}/{file_name}",
        status=status,
        is_evidence=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _reload(db, doc_id, tenant_id):
    db.expire_all()
    return db.query(Document).filter(
        Document.id == doc_id, Document.tenant_id == tenant_id
    ).first()


def _make_mock_result():
    from modules.extraction.schemas import TokenUsage
    result = MagicMock()
    result.is_error = False
    result.doc_type = MagicMock()
    result.doc_type.value = "supply"
    result.provider = "mock"
    result.model = "mock-model"
    result.cost_vnd = 0.0
    result.latency_ms = 100.0
    result.warnings = []
    result.usage = TokenUsage(input_tokens=10, output_tokens=5)
    result.fields = {}
    result.clauses = []
    result.parties = []
    result.obligation_schedule = []
    result.defined_terms = []
    result.cross_references = []
    result.has_signature = False
    result.signature_pages = []
    result.ocr_text = None
    return result


# ── Pure unit tests for the shared detection helper ───────────────────────────


def test_detects_max_tokens_in_finish_reason_format():
    assert is_max_tokens_truncation(
        ["hybrid_ocr returned no structured output. finish=MAX_TOKENS | text_len=76538"]
    )


def test_does_not_flag_other_finish_reasons():
    assert not is_max_tokens_truncation(["finish=STOP | text_len=1234"])
    assert not is_max_tokens_truncation(["503 The model is overloaded"])
    assert not is_max_tokens_truncation([])


# ── Integration: run_extraction keeps doc retryable on MAX_TOKENS ─────────────


def test_max_tokens_keeps_doc_pending_with_size_message(test_tenant, db, tmp_path):
    """MAX_TOKENS keeps doc pending with the ratified 'document too large' message."""
    doc = _make_doc(db, test_tenant)

    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_result = _make_mock_result()
    mock_result.is_error = True
    mock_result.warnings = ["hybrid_ocr returned no structured output. finish=MAX_TOKENS | text_len=76538"]

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "pending"
    assert fresh.processing_stage == "retry_needed"
    assert fresh.extraction_warnings is not None
    assert "MAX_TOKENS" in fresh.extraction_warnings

    event = (
        db.query(Event)
        .filter(
            Event.entity_id == doc.id,
            Event.tenant_id == test_tenant,
            Event.event_type == "extraction_transient_failure",
        )
        .first()
    )
    assert event is not None
    import json as _json
    payload = _json.loads(event.payload)
    assert payload["reason"] == "Document quá lớn, đã cắt bớt kết quả."

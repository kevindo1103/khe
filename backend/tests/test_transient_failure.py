"""Tests for 503/UNAVAILABLE transient-outage handling (#436, QC #435).

A Gemini 503 must keep the document retryable (status='pending',
processing_stage='retry_needed'), not land in the terminal 'failed' state —
distinguishes "try again later" from a genuine extraction failure.

processing_stage='retry_needed' (not 'pending') per QC review on PR #458 —
'pending' collides with a freshly-uploaded doc that hasn't started
extraction yet.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.database import get_tenant_session
from app.models.tenant import Document, Event
from app.services.extraction_runner import (
    _is_transient_provider_outage,
    run_extraction,
)


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


# ── Pure unit tests for the detection helper ──────────────────────────────────


def test_detects_503():
    assert _is_transient_provider_outage(["ServiceUnavailable: 503 The model is overloaded."])


def test_detects_unavailable():
    assert _is_transient_provider_outage(["gemini_flash returned no structured output. finish=UNAVAILABLE"])


def test_does_not_flag_other_errors():
    assert not _is_transient_provider_outage(["Extraction exception: KeyError"])
    assert not _is_transient_provider_outage([])


# ── Integration: run_extraction keeps doc retryable on 503 ────────────────────


def test_503_keeps_doc_pending_not_failed(test_tenant, db, tmp_path):
    """A 503 warning keeps status='pending' + processing_stage='retry_needed', not 'failed'."""
    doc = _make_doc(db, test_tenant)

    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_result = _make_mock_result()
    mock_result.is_error = True
    mock_result.warnings = ["gemini_flash extract failed: ServiceUnavailable: 503 The model is overloaded."]

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
    assert fresh.processing_progress == 0
    assert fresh.extraction_warnings is not None
    assert "503" in fresh.extraction_warnings


def test_503_logs_transient_failure_event(test_tenant, db, tmp_path):
    """A 503 outage logs extraction_transient_failure, not extraction_failed."""
    doc = _make_doc(db, test_tenant)

    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_result = _make_mock_result()
    mock_result.is_error = True
    mock_result.warnings = ["503 UNAVAILABLE"]

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    events = db.query(Event).filter(
        Event.entity_id == doc.id, Event.tenant_id == test_tenant,
    ).all()
    event_types = {e.event_type for e in events}
    assert "extraction_transient_failure" in event_types
    assert "extraction_failed" not in event_types


def test_non_transient_error_still_marks_failed(test_tenant, db, tmp_path):
    """A non-503 hard error still lands in the terminal 'failed' state."""
    doc = _make_doc(db, test_tenant)

    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_result = _make_mock_result()
    mock_result.is_error = True
    mock_result.warnings = ["provider_error: malformed response"]

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "failed"
    assert fresh.processing_stage == "failed"

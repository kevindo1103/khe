"""Tests for auto-triggering the two-pass pipeline on MAX_TOKENS (#461, mini-sprint #443).

Mocks `extract_skeleton`/`persist_skeleton`/`run_content_fill` at the
extraction_runner call sites — this suite verifies the WIRING (when to
trigger, how to interpret the outcome, fallback on any failure), not the
two-pass pipeline internals (covered by test_two_pass_runner.py).
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.tenant import Document, Event
from app.services.extraction_runner import run_extraction
from modules.extraction.two_pass import SkeletonClauseResult, SkeletonResult


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


def _make_mock_result(ocr_text=None):
    from modules.extraction.schemas import TokenUsage
    result = MagicMock()
    result.is_error = True
    result.doc_type = MagicMock()
    result.doc_type.value = "supply"
    result.provider = "hybrid_ocr"
    result.model = "mock-model"
    result.cost_vnd = 0.0
    result.latency_ms = 100.0
    result.warnings = ["hybrid_ocr returned no structured output. finish=MAX_TOKENS | text_len=76538"]
    result.usage = TokenUsage(input_tokens=10, output_tokens=5)
    result.fields = {}
    result.clauses = []
    result.parties = []
    result.obligation_schedule = []
    result.defined_terms = []
    result.cross_references = []
    result.has_signature = False
    result.signature_pages = []
    result.ocr_text = ocr_text
    return result


# ── Trigger condition ──────────────────────────────────────────────────────


def test_auto_triggers_two_pass_when_ocr_text_present(test_tenant, db, tmp_path):
    """MAX_TOKENS + ocr_text present → two-pass pipeline is invoked."""
    mock_result = _make_mock_result(ocr_text="Điều 1: Nội dung.")
    fake_skeleton = SkeletonResult(
        clauses=[SkeletonClauseResult(num="Điều 1", title=None, level=1, clause_path="1")],
    )

    doc = _make_doc(db, test_tenant)
    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)
    mock_extract_skeleton = AsyncMock(return_value=fake_skeleton)
    mock_run_content_fill = AsyncMock(return_value={"total": 1, "filled": 1, "truncated": 0})

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("modules.extraction.two_pass.extract_skeleton", new=mock_extract_skeleton), \
         patch("app.services.two_pass_runner.persist_skeleton") as mock_persist, \
         patch("app.services.two_pass_runner.run_content_fill", new=mock_run_content_fill):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    mock_extract_skeleton.assert_called_once_with("Điều 1: Nội dung.")
    mock_persist.assert_called_once()
    mock_run_content_fill.assert_called_once()

    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "extracted"
    assert fresh.processing_stage == "done"


def test_no_auto_trigger_when_ocr_text_absent(test_tenant, db, tmp_path):
    """MAX_TOKENS without ocr_text (e.g. vision-mode gemini_flash) falls back
    to the plain retryable message — no two-pass call attempted."""
    mock_result = _make_mock_result(ocr_text=None)

    doc = _make_doc(db, test_tenant)
    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)
    mock_extract_skeleton = AsyncMock()

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("modules.extraction.two_pass.extract_skeleton", new=mock_extract_skeleton):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    mock_extract_skeleton.assert_not_called()
    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "pending"
    assert fresh.processing_stage == "retry_needed"


# ── Outcome handling ─────────────────────────────────────────────────────────


def test_full_success_marks_extracted_with_scope_gap_warning(test_tenant, db, tmp_path):
    """All clauses filled → status='extracted', but extraction_warnings must
    flag that fields/parties/obligations were NOT extracted (#461 scope gap —
    never silently claim a complete extraction, D-08)."""
    mock_result = _make_mock_result(ocr_text="Điều 1: Nội dung.")
    fake_skeleton = SkeletonResult(
        clauses=[SkeletonClauseResult(num="Điều 1", title=None, level=1, clause_path="1")],
    )

    doc = _make_doc(db, test_tenant)
    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("modules.extraction.two_pass.extract_skeleton", new=AsyncMock(return_value=fake_skeleton)), \
         patch("app.services.two_pass_runner.persist_skeleton"), \
         patch("app.services.two_pass_runner.run_content_fill",
               new=AsyncMock(return_value={"total": 3, "filled": 3, "truncated": 0})):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "extracted"
    assert fresh.processing_stage == "done"
    assert fresh.processing_progress == 100
    assert fresh.extraction_warnings is not None
    warnings = json.loads(fresh.extraction_warnings)
    assert any("CHƯA được trích xuất" in w for w in warnings)

    event = (
        db.query(Event)
        .filter(Event.entity_id == doc.id, Event.event_type == "extraction_two_pass_completed")
        .first()
    )
    assert event is not None
    payload = json.loads(event.payload)
    assert payload["fields_extracted"] is False
    assert payload["parties_extracted"] is False
    assert payload["obligations_extracted"] is False


def test_partial_fill_stays_retryable_not_marked_extracted(test_tenant, db, tmp_path):
    """Some clauses still 'truncated' after Pass 3 → doc stays retryable, NOT
    marked 'extracted' with a partial result."""
    mock_result = _make_mock_result(ocr_text="Điều 1: Nội dung.")
    fake_skeleton = SkeletonResult(
        clauses=[SkeletonClauseResult(num="Điều 1", title=None, level=1, clause_path="1")],
    )

    doc = _make_doc(db, test_tenant)
    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("modules.extraction.two_pass.extract_skeleton", new=AsyncMock(return_value=fake_skeleton)), \
         patch("app.services.two_pass_runner.persist_skeleton"), \
         patch("app.services.two_pass_runner.run_content_fill",
               new=AsyncMock(return_value={"total": 5, "filled": 3, "truncated": 2})):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "pending"
    assert fresh.processing_stage == "retry_needed"


def test_empty_skeleton_falls_back_to_retryable(test_tenant, db, tmp_path):
    """Pass 1 (extract_skeleton) itself returns no clauses → retryable fallback,
    never proceeds to Pass 2 with nothing to fill."""
    mock_result = _make_mock_result(ocr_text="garbled text")
    empty_skeleton = SkeletonResult(clauses=[], warnings=["skeleton call failed"])

    doc = _make_doc(db, test_tenant)
    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)
    mock_run_content_fill = AsyncMock()

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("modules.extraction.two_pass.extract_skeleton", new=AsyncMock(return_value=empty_skeleton)), \
         patch("app.services.two_pass_runner.run_content_fill", new=mock_run_content_fill):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    mock_run_content_fill.assert_not_called()
    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "pending"
    assert fresh.processing_stage == "retry_needed"


def test_skeleton_exception_falls_back_to_retryable(test_tenant, db, tmp_path):
    """extract_skeleton raising (network error, SDK issue) → retryable, not a crash."""
    mock_result = _make_mock_result(ocr_text="some text")

    doc = _make_doc(db, test_tenant)
    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("modules.extraction.two_pass.extract_skeleton", new=AsyncMock(side_effect=RuntimeError("boom"))):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "pending"
    assert fresh.processing_stage == "retry_needed"


def test_content_fill_exception_falls_back_to_retryable(test_tenant, db, tmp_path):
    """run_content_fill raising mid-pipeline → retryable, not a crash, not
    marked 'extracted'."""
    mock_result = _make_mock_result(ocr_text="Điều 1: Nội dung.")
    fake_skeleton = SkeletonResult(
        clauses=[SkeletonClauseResult(num="Điều 1", title=None, level=1, clause_path="1")],
    )

    doc = _make_doc(db, test_tenant)
    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("modules.extraction.two_pass.extract_skeleton", new=AsyncMock(return_value=fake_skeleton)), \
         patch("app.services.two_pass_runner.persist_skeleton"), \
         patch("app.services.two_pass_runner.run_content_fill", new=AsyncMock(side_effect=RuntimeError("boom"))):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "pending"
    assert fresh.processing_stage == "retry_needed"

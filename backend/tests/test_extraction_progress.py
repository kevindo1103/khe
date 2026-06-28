"""Tests for extraction progress bar — processing_stage + processing_progress (#360)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.database import get_tenant_session
from app.models.tenant import Document
from app.services.extraction_runner import _update_progress, _mark_failed, run_extraction


# ── Helpers ───────────────────────────────────────────────────────────────────


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
    """Re-fetch doc from DB (defeats ORM identity cache)."""
    db.expire_all()
    return db.query(Document).filter(
        Document.id == doc_id,
        Document.tenant_id == tenant_id,
    ).first()


# ── Unit tests — _update_progress ─────────────────────────────────────────────


def test_update_progress_writes_stage_and_progress(test_tenant, db):
    """`_update_progress` commits stage+progress visible via a fresh query."""
    doc = _make_doc(db, test_tenant)
    _update_progress(test_tenant, doc.id, "ocr", 30)
    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.processing_stage == "ocr"
    assert fresh.processing_progress == 30


def test_update_progress_overwrites_previous_checkpoint(test_tenant, db):
    """Successive calls to `_update_progress` advance the checkpoint."""
    doc = _make_doc(db, test_tenant)
    _update_progress(test_tenant, doc.id, "ocr", 30)
    _update_progress(test_tenant, doc.id, "llm", 60)
    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.processing_stage == "llm"
    assert fresh.processing_progress == 60


# ── Unit tests — _mark_failed ─────────────────────────────────────────────────


def test_mark_failed_sets_processing_stage_failed(test_tenant, db):
    """`_mark_failed` sets processing_stage='failed' alongside status='failed'."""
    doc = _make_doc(db, test_tenant)
    _mark_failed(db, doc.id, test_tenant, "unit test failure")
    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.status == "failed"
    assert fresh.processing_stage == "failed"


# ── Integration tests — run_extraction checkpoints ────────────────────────────


def _make_mock_result():
    """Build a minimal ExtractionResult-like mock for run_extraction."""
    from modules.extraction.schemas import DocType, TokenUsage
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
    return result


def test_run_extraction_sets_done_on_success(test_tenant, db, tmp_path):
    """After successful extraction, processing_stage='done' and progress=100."""
    doc = _make_doc(db, test_tenant)

    # Create a real file so runner can read bytes.
    # runner does: settings.STORAGE_DIR / doc.file_path = tmp_path / "{tenant}/{file}"
    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_result = _make_mock_result()
    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("app.services.extraction_runner.quota.add_extraction_cost_standalone"), \
         patch("app.services.extraction_runner.tenant_journey.advance_stage_standalone"), \
         patch("app.services.extraction_runner.derive_obligations"), \
         patch("app.services.extraction_runner.resolve_date_anchored_obligations"):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc.id, test_tenant)

    fresh = _reload(db, doc.id, test_tenant)
    assert fresh.processing_stage == "done"
    assert fresh.processing_progress == 100
    assert fresh.status == "extracted"


def test_run_extraction_sets_failed_on_error(test_tenant, db, tmp_path):
    """Failed extraction sets processing_stage='failed'."""
    doc = _make_doc(db, test_tenant)

    fake_file = tmp_path / doc.file_path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_result = _make_mock_result()
    mock_result.is_error = True
    mock_result.warnings = ["provider_error"]

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


# ── API tests — GET /documents/{id} returns new fields ────────────────────────


def test_document_detail_returns_progress_fields(auth_client, test_tenant, db):
    """DocumentDetailOut includes processing_stage and processing_progress."""
    doc = _make_doc(db, test_tenant, status="extracted")
    doc.processing_stage = "done"
    doc.processing_progress = 100
    db.commit()

    r = auth_client.get(f"/documents/{doc.id}")
    assert r.status_code == 200
    data = r.json()
    assert "processing_stage" in data
    assert "processing_progress" in data
    assert data["processing_stage"] == "done"
    assert data["processing_progress"] == 100


def test_document_list_returns_progress_fields(auth_client, test_tenant, db):
    """DocumentListItem includes processing_stage and processing_progress."""
    doc = _make_doc(db, test_tenant, status="pending")
    doc.processing_stage = "ocr"
    doc.processing_progress = 30
    db.commit()

    r = auth_client.get("/documents")
    assert r.status_code == 200
    items = r.json()["items"]
    item = next((i for i in items if i["id"] == doc.id), None)
    assert item is not None
    assert item["processing_stage"] == "ocr"
    assert item["processing_progress"] == 30


def test_document_null_progress_for_legacy_docs(auth_client, test_tenant, db):
    """Docs without progress columns return null (graceful degrade for legacy data)."""
    doc = _make_doc(db, test_tenant, status="extracted")
    # Don't set processing_stage or processing_progress → remain NULL

    r = auth_client.get(f"/documents/{doc.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["processing_stage"] is None
    assert data["processing_progress"] is None

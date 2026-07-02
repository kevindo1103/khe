"""Tests for contract title + number extraction (#363 R1)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.database import get_tenant_session
from app.models.tenant import Document, Event
from app.services.extraction_runner import run_extraction
from modules.extraction.schemas import CANONICAL_FIELDS, V2_UNIVERSAL_FIELDS


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
    db.expire_all()
    return db.query(Document).filter(
        Document.id == doc_id, Document.tenant_id == tenant_id
    ).first()


def _make_mock_result(tieu_de=None, so_hd=None):
    """Build ExtractionResult mock with optional title + number fields."""
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
    result.clauses = []
    result.parties = []
    result.obligation_schedule = []
    result.defined_terms = []
    result.cross_references = []
    result.has_signature = False
    result.signature_pages = []
    result.ocr_text = None

    fields = {}
    if tieu_de is not None:
        f = MagicMock()
        f.value = tieu_de
        f.confidence = 0.95
        f.needs_review = False
        f.bbox = None
        f.ref = None
        f.page_num = None
        fields["tieu_de_hd"] = f
    if so_hd is not None:
        f = MagicMock()
        f.value = so_hd
        f.confidence = 0.9
        f.needs_review = False
        f.bbox = None
        f.ref = None
        f.page_num = None
        fields["so_hop_dong"] = f
    result.fields = fields
    return result


# ── Schema registration tests ─────────────────────────────────────────────────


def test_tieu_de_hd_in_v2_universal_fields():
    """tieu_de_hd is registered in V2_UNIVERSAL_FIELDS."""
    assert "tieu_de_hd" in V2_UNIVERSAL_FIELDS


def test_so_hop_dong_in_v2_universal_fields():
    """so_hop_dong is registered in V2_UNIVERSAL_FIELDS."""
    assert "so_hop_dong" in V2_UNIVERSAL_FIELDS


def test_both_in_canonical_fields():
    """Both fields flow through to CANONICAL_FIELDS."""
    assert "tieu_de_hd" in CANONICAL_FIELDS
    assert "so_hop_dong" in CANONICAL_FIELDS


# ── Model column tests ────────────────────────────────────────────────────────


def test_document_has_title_and_contract_number_columns(test_tenant, db):
    """Document model has title and contract_number columns (nullable)."""
    doc = _make_doc(db, test_tenant)
    assert hasattr(doc, "title")
    assert hasattr(doc, "contract_number")
    assert doc.title is None
    assert doc.contract_number is None


# ── extraction_runner integration tests ───────────────────────────────────────


def _run_mock_extraction(test_tenant, tmp_path, mock_result):
    """Run extraction with a given mock result."""
    from app.db.database import get_tenant_session
    db = get_tenant_session(test_tenant)
    try:
        doc = Document(
            tenant_id=test_tenant,
            file_name="contract.pdf",
            file_path=f"{test_tenant}/contract.pdf",
            status="pending",
            is_evidence=False,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id
    finally:
        db.close()

    fake_file = tmp_path / f"{test_tenant}" / "contract.pdf"
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

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
        run_extraction(doc_id, test_tenant)

    db2 = get_tenant_session(test_tenant)
    try:
        db2.expire_all()
        return db2.query(Document).filter(
            Document.id == doc_id, Document.tenant_id == test_tenant
        ).first()
    finally:
        db2.close()


def test_extraction_populates_title(test_tenant, tmp_path):
    """LLM returns tieu_de_hd → doc.title is populated."""
    result = _make_mock_result(tieu_de="HỢP ĐỒNG CẤP PHÉP VÀ SỬ DỤNG BẢN QUYỀN")
    doc = _run_mock_extraction(test_tenant, tmp_path, result)
    assert doc.title == "HỢP ĐỒNG CẤP PHÉP VÀ SỬ DỤNG BẢN QUYỀN"
    assert doc.contract_number is None


def test_extraction_populates_contract_number(test_tenant, tmp_path):
    """LLM returns so_hop_dong → doc.contract_number is populated."""
    result = _make_mock_result(so_hd="01/2025/HDMB")
    doc = _run_mock_extraction(test_tenant, tmp_path, result)
    assert doc.contract_number == "01/2025/HDMB"


def test_extraction_title_cascade_fallback(test_tenant, tmp_path):
    """No tieu_de_hd but has so_hop_dong → doc.title falls back to contract_number."""
    result = _make_mock_result(tieu_de=None, so_hd="02/2025/HĐ")
    doc = _run_mock_extraction(test_tenant, tmp_path, result)
    assert doc.title == "02/2025/HĐ"
    assert doc.contract_number == "02/2025/HĐ"


def test_extraction_no_title_fields(test_tenant, tmp_path):
    """No title fields → title=None, contract_number=None (FE shows filename)."""
    result = _make_mock_result()
    doc = _run_mock_extraction(test_tenant, tmp_path, result)
    assert doc.title is None
    assert doc.contract_number is None


def test_extraction_both_title_and_number(test_tenant, tmp_path):
    """Both fields → title from tieu_de_hd, contract_number from so_hop_dong."""
    result = _make_mock_result(
        tieu_de="HỢP ĐỒNG THUÊ NHÀ XƯỞNG",
        so_hd="05/2025/HDTN",
    )
    doc = _run_mock_extraction(test_tenant, tmp_path, result)
    assert doc.title == "HỢP ĐỒNG THUÊ NHÀ XƯỞNG"
    assert doc.contract_number == "05/2025/HDTN"


# ── PATCH /{doc_id} endpoint tests ───────────────────────────────────────────


def test_patch_document_updates_title(auth_client, test_tenant, db):
    """PATCH /documents/{id} updates title and returns new value."""
    doc = _make_doc(db, test_tenant, status="extracted")
    r = auth_client.patch(f"/documents/{doc.id}", json={"title": "Hợp đồng mới"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Hợp đồng mới"


def test_patch_document_updates_contract_number(auth_client, test_tenant, db):
    """PATCH /documents/{id} updates contract_number."""
    doc = _make_doc(db, test_tenant, status="extracted")
    r = auth_client.patch(f"/documents/{doc.id}", json={"contract_number": "99/2025/HĐ"})
    assert r.status_code == 200
    assert r.json()["contract_number"] == "99/2025/HĐ"


def test_patch_document_logs_event(auth_client, test_tenant, db):
    """PATCH title → document_field_edited Event is written."""
    doc = _make_doc(db, test_tenant, status="extracted")
    r = auth_client.patch(f"/documents/{doc.id}", json={"title": "Tiêu đề mới"})
    assert r.status_code == 200
    ev = (
        db.query(Event)
        .filter(
            Event.tenant_id == test_tenant,
            Event.entity_id == doc.id,
            Event.event_type == "document_field_edited",
        )
        .first()
    )
    assert ev is not None
    import json
    payload = json.loads(ev.payload)
    assert payload["field"] == "title"
    assert payload["new_value"] == "Tiêu đề mới"


def test_patch_document_404_unknown(auth_client):
    """PATCH on unknown doc → 404."""
    r = auth_client.patch("/documents/99999", json={"title": "X"})
    assert r.status_code == 404


def test_patch_document_tenant_isolation(auth_client, test_tenant, db):
    """PATCH on a doc belonging to another tenant → 404."""
    import uuid
    from fastapi.testclient import TestClient
    from app.core.security import get_password_hash
    from app.db.database import MasterSessionLocal, init_tenant_db, _engine_cache, _cache_lock, TENANTS_DIR
    from app.models.master import Tenant, TenantUser

    other_id = f"qc-other-{uuid.uuid4().hex[:8]}"
    init_tenant_db(other_id)
    mdb = MasterSessionLocal()
    try:
        mdb.add(Tenant(id=other_id, name=f"Other {other_id}", db_path=f"tenants/{other_id}.db"))
        mdb.add(TenantUser(
            tenant_id=other_id,
            username="otheruser",
            hashed_password=get_password_hash("otherpass"),
            role="admin",
        ))
        mdb.commit()
    finally:
        mdb.close()

    other_db = get_tenant_session(other_id)
    try:
        other_doc = Document(
            tenant_id=other_id,
            file_name="other.pdf",
            file_path=f"{other_id}/other.pdf",
            status="extracted",
        )
        other_db.add(other_doc)
        other_db.commit()
        other_db.refresh(other_doc)
        other_doc_id = other_doc.id
    finally:
        other_db.close()

    try:
        r = auth_client.patch(f"/documents/{other_doc_id}", json={"title": "Hack"})
        assert r.status_code == 404
    finally:
        with _cache_lock:
            eng = _engine_cache.pop(other_id, None)
        if eng:
            eng.dispose()
        for suffix in ("", "-wal", "-shm"):
            f = TENANTS_DIR / f"{other_id}.db{suffix}"
            try:
                f.unlink()
            except FileNotFoundError:
                pass
        mdb2 = MasterSessionLocal()
        try:
            mdb2.query(TenantUser).filter(TenantUser.tenant_id == other_id).delete()
            mdb2.query(Tenant).filter(Tenant.id == other_id).delete()
            mdb2.commit()
        finally:
            mdb2.close()


# ── GET /documents list + detail include new fields ───────────────────────────


def test_document_detail_includes_title_fields(auth_client, test_tenant, db):
    """GET /documents/{id} returns title and contract_number."""
    doc = _make_doc(db, test_tenant, status="extracted")
    doc.title = "HỢP ĐỒNG CUNG CẤP DỊCH VỤ"
    doc.contract_number = "10/2025/HDDV"
    db.commit()

    r = auth_client.get(f"/documents/{doc.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "HỢP ĐỒNG CUNG CẤP DỊCH VỤ"
    assert data["contract_number"] == "10/2025/HDDV"


def test_document_list_includes_title_fields(auth_client, test_tenant, db):
    """GET /documents list items include title and contract_number."""
    doc = _make_doc(db, test_tenant, status="extracted")
    doc.title = "HĐ Kinh Tế"
    db.commit()

    r = auth_client.get("/documents")
    assert r.status_code == 200
    item = next((i for i in r.json()["items"] if i["id"] == doc.id), None)
    assert item is not None
    assert item["title"] == "HĐ Kinh Tế"


def test_document_null_title_for_legacy_docs(auth_client, test_tenant, db):
    """Legacy docs without title return null — FE falls back to file_name."""
    doc = _make_doc(db, test_tenant, status="extracted")

    r = auth_client.get(f"/documents/{doc.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["title"] is None
    assert data["contract_number"] is None

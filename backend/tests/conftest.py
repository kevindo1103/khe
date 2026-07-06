"""Shared pytest fixtures for the Khế test suite.

Provides isolated per-test tenant DBs with UUID-based IDs, mock vision
providers, and authenticated TestClient instances. Existing test modules
that define their own module-scoped ``setup_db`` fixtures are unaffected —
these fixtures are opt-in (not autouse).

Architecture:
- ``test_tenant`` — creates a fresh tenant in master.db + runs alembic
  migrations for the per-tenant DB. Teardown disposes the engine, deletes
  the .db file, and removes the tenant row from master.db.
- ``db`` — a Session bound to ``test_tenant``'s per-tenant DB.
- ``auth_client`` — a TestClient logged in as the test tenant's admin user.
- ``tenant_with_legal_name`` — extends ``test_tenant`` with a TenantProfile
  row carrying ``legal_name`` (DEC-030 self-party match).
- ``sample_doc_thuong_mai`` / ``sample_doc_lao_dong`` — pre-seeded Document
  + Term rows for the respective doc_type_group.
- ``mock_vision_provider`` — a FakeProvider implementing the
  VisionExtractionProvider Protocol (no real API calls).
"""
import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.security import get_password_hash
from app.db.database import (
    MasterSessionLocal,
    TENANTS_DIR,
    _cache_lock,
    _engine_cache,
    get_tenant_session,
    init_master_db,
    init_tenant_db,
)
from app.models.master import Tenant, TenantProfile, TenantUser
from app.models.tenant import Document, Obligation, Term
from app.services.consent import record_consent
from modules.extraction import (
    DocType,
    ExtractedField,
    ExtractionResult,
    ObligationScheduleItem,
    PartyItem,
    TokenUsage,
)


# ── Helpers ──────────────────────────────────────────────────────────────

def _reset_tenant_db(tid: str):
    """Dispose cached engine and delete the tenant .db files."""
    with _cache_lock:
        eng = _engine_cache.pop(tid, None)
    if eng is not None:
        eng.dispose()
    for suffix in ("", "-wal", "-shm"):
        f = TENANTS_DIR / f"{tid}.db{suffix}"
        try:
            f.unlink()
        except FileNotFoundError:
            pass


def _cleanup_master(tenant_id: str):
    """Remove tenant + user + profile rows from master.db."""
    db = MasterSessionLocal()
    try:
        db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id).delete()
        db.query(TenantProfile).filter(TenantProfile.tenant_id == tenant_id).delete()
        db.query(Tenant).filter(Tenant.id == tenant_id).delete()
        db.commit()
    finally:
        db.close()


# ── Core fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def test_tenant():
    """Isolated tenant DB per test — teardown after.

    Yields the tenant_id string. The tenant DB is created via alembic
    migrations, a user is registered, and vision_extraction consent is
    recorded. On teardown the engine is disposed, .db files deleted, and
    master.db rows removed.
    """
    tenant_id = f"qc-test-{uuid.uuid4().hex[:8]}"
    init_master_db()
    init_tenant_db(tenant_id)

    db = MasterSessionLocal()
    try:
        db.add(Tenant(id=tenant_id, name=f"QC Test {tenant_id}", db_path=f"tenants/{tenant_id}.db"))
        db.add(TenantUser(
            tenant_id=tenant_id,
            username="qcuser",
            hashed_password=get_password_hash("qcpass"),
            role="admin",
        ))
        db.commit()
    finally:
        db.close()

    tenant_db = get_tenant_session(tenant_id)
    try:
        record_consent(tenant_db, tenant_id, "vision_extraction", actor="qcuser", entity_id=1)
    finally:
        tenant_db.close()

    try:
        yield tenant_id
    finally:
        _reset_tenant_db(tenant_id)
        _cleanup_master(tenant_id)


@pytest.fixture
def db(test_tenant):
    """A Session bound to test_tenant's per-tenant DB. Caller does not close."""
    session = get_tenant_session(test_tenant)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_client(test_tenant):
    """A TestClient logged in as the test tenant's admin user."""
    c = TestClient(__import__("main").app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": test_tenant, "username": "qcuser", "password": "qcpass"},
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return c


# ── Extended tenant fixtures ─────────────────────────────────────────────

@pytest.fixture
def tenant_with_legal_name(test_tenant):
    """Tenant with legal_name set in TenantProfile (DEC-030 self-party)."""
    master_db = MasterSessionLocal()
    try:
        profile = master_db.query(TenantProfile).filter(
            TenantProfile.tenant_id == test_tenant
        ).first()
        if profile is None:
            profile = TenantProfile(tenant_id=test_tenant, legal_name="Công ty TNHH Test ABC")
            master_db.add(profile)
        else:
            profile.legal_name = "Công ty TNHH Test ABC"
        master_db.commit()
    finally:
        master_db.close()
    return test_tenant


# ── Sample document fixtures ─────────────────────────────────────────────

@pytest.fixture
def sample_doc_thuong_mai(test_tenant, db):
    """Document with doc_type_group='thuong_mai', parties, obligations."""
    doc = Document(
        tenant_id=test_tenant,
        file_name="thuong_mai_contract.pdf",
        file_path=f"{test_tenant}/thuong_mai.pdf",
        doc_type="hd_nha_cung_cap",
        status="extracted",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    terms = [
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="doi_tac",
             field_value="Cty XYZ", confidence=0.9, needs_review=False),
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="ngay_hieu_luc",
             field_value="2026-01-01", confidence=0.9, needs_review=False),
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="ngay_het_han",
             field_value="2027-01-01", confidence=0.85, needs_review=False),
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="doc_type_group",
             field_value="thuong_mai", confidence=0.95, needs_review=False),
    ]
    for t in terms:
        db.add(t)
    db.commit()

    return doc


@pytest.fixture
def sample_doc_lao_dong(test_tenant, db):
    """Document with doc_type_group='lao_dong', NSDLĐ/NLĐ parties."""
    doc = Document(
        tenant_id=test_tenant,
        file_name="lao_dong_contract.pdf",
        file_path=f"{test_tenant}/lao_dong.pdf",
        doc_type="hd_lao_dong",
        status="extracted",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    terms = [
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="doi_tac",
             field_value="Công ty TNHH Test ABC", confidence=0.9, needs_review=False),
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="ngay_hieu_luc",
             field_value="2026-01-01", confidence=0.9, needs_review=False),
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="ngay_het_han",
             field_value="2027-01-01", confidence=0.85, needs_review=False),
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="doc_type_group",
             field_value="lao_dong", confidence=0.95, needs_review=False),
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="luong_co_ban",
             field_value="15000000", confidence=0.85, needs_review=False),
        Term(tenant_id=test_tenant, document_id=doc.id, field_name="thoi_gian_thu_viec",
             field_value="60 ngày", confidence=0.8, needs_review=True),
    ]
    for t in terms:
        db.add(t)
    db.commit()

    return doc


# ── Mock vision provider ─────────────────────────────────────────────────

class FakeVisionProvider:
    """Protocol-conforming provider that returns a deterministic ExtractionResult.

    Implements the VisionExtractionProvider Protocol: has ``name`` attribute
    and an async ``extract()`` method. NEVER calls real Gemini/Claude APIs.
    """

    name = "fake_qc_provider"

    def __init__(self, result=None):
        self._result = result or _default_extraction_result()
        self.calls = []

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        self.calls.append((image_bytes, doc_type))
        return self._result


def _default_extraction_result() -> ExtractionResult:
    """A baseline ExtractionResult with all canonical fields populated."""
    return ExtractionResult(
        doc_type=DocType.LEASE,
        doc_type_confidence=0.95,
        fields={
            name: ExtractedField(value="sample", confidence=0.9, needs_review=False)
            for name in (
                "doi_tac", "ngay_hieu_luc", "ngay_het_han", "gia_tri_hd",
                "thoi_han_hd", "dieu_khoan_gia_han", "dieu_khoan_thanh_toan",
                "doc_type_group", "ngay_ky", "tien_dat_coc",
                "thoi_han_bao_hanh", "thoi_han_thong_bao",
                # tenant_021 additions
                "tieu_de_hd", "so_hop_dong",
            )
        },
        provider="fake_qc_provider",
        model="fake-qc-model",
        latency_ms=42.0,
        usage=TokenUsage(input_tokens=500, output_tokens=100),
        cost_vnd=300.0,
    )


def make_extraction_result(
    doc_type=DocType.LEASE,
    doc_type_group="thuong_mai",
    fields=None,
    type_specific=None,
    parties=None,
    obligation_schedule=None,
) -> ExtractionResult:
    """Build an ExtractionResult for tests.

    Args:
        doc_type: DocType enum value.
        doc_type_group: Value for the doc_type_group field (DEC-029).
        fields: Dict of field_name → ExtractedField. Merged with defaults.
        type_specific: Dict of type-specific field_name → ExtractedField.
        parties: List of PartyItem (DEC-030).
        obligation_schedule: List of ObligationScheduleItem (DEC-030 Phase 2).
    """
    base_fields = {
        "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
        "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
        "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
        "gia_tri_hd": ExtractedField(value="100000000", confidence=0.8, needs_review=True),
        "thoi_han_hd": ExtractedField(value="12 tháng", confidence=0.9, needs_review=False),
        "dieu_khoan_gia_han": ExtractedField(value="Tự động gia hạn", confidence=0.7, needs_review=True),
        "dieu_khoan_thanh_toan": ExtractedField(value="Chuyển khoản", confidence=0.9, needs_review=False),
        "doc_type_group": ExtractedField(value=doc_type_group, confidence=0.95, needs_review=False),
        # tenant_021 additions — required by CANONICAL_FIELDS
        "tieu_de_hd": ExtractedField(value="sample", confidence=0.9, needs_review=False),
        "so_hop_dong": ExtractedField(value="sample", confidence=0.9, needs_review=False),
        "ngay_ky": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
        "ngay_khai_truong": ExtractedField(value="sample", confidence=0.8, needs_review=False),
        "tien_dat_coc": ExtractedField(value="sample", confidence=0.8, needs_review=False),
        "thoi_han_bao_hanh": ExtractedField(value="sample", confidence=0.8, needs_review=False),
        "thoi_han_thong_bao": ExtractedField(value="sample", confidence=0.8, needs_review=False),
    }
    if fields:
        base_fields.update(fields)
    if type_specific:
        base_fields.update(type_specific)

    return ExtractionResult(
        doc_type=doc_type,
        doc_type_confidence=0.95,
        fields=base_fields,
        parties=parties or [],
        obligation_schedule=obligation_schedule or [],
        provider="fake_qc_provider",
        model="fake-qc-model",
        latency_ms=42.0,
        usage=TokenUsage(input_tokens=500, output_tokens=100),
        cost_vnd=300.0,
    )


@pytest.fixture
def mock_vision_provider():
    """Return a FakeVisionProvider instance (no real API calls).

    Tests can set ``provider._result`` to a custom ExtractionResult before
    patching it into the extraction runner.
    """
    return FakeVisionProvider()

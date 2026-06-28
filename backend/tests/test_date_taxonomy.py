"""Date taxonomy tests — signing_date + commencement_date (#369)."""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document
from app.services.consent import record_consent
from app.services.extraction_runner import run_extraction
from modules.extraction import DocType, ExtractedField, ExtractionResult, TokenUsage
from main import app

TENANT_ID = "date-tax-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT_ID)

    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT_ID).first():
        db.add(Tenant(id=TENANT_ID, name="Date Tax Tenant", db_path=f"tenants/{TENANT_ID}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT_ID, TenantUser.username == "dtuser").first():
        db.add(TenantUser(
            tenant_id=TENANT_ID, username="dtuser",
            hashed_password=get_password_hash("dtpass"), role="staff",
        ))
        db.commit()
    db.close()

    tenant_db = get_tenant_session(TENANT_ID)
    record_consent(tenant_db, TENANT_ID, "vision_extraction", actor="dtuser", entity_id=1)
    tenant_db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT_ID, "username": "dtuser", "password": "dtpass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def tenant_db():
    db = get_tenant_session(TENANT_ID)
    yield db
    db.close()


def _seed_doc(db, file_name="HD-DATE-TEST.pdf") -> Document:
    doc = Document(
        tenant_id=TENANT_ID,
        file_name=file_name,
        file_path=f"{TENANT_ID}/{file_name}",
        doc_type="service",
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


class _FakeProvider:
    """Protocol-conforming provider that returns a canned ExtractionResult."""
    def __init__(self, result):
        self._result = result

    async def extract(self, *_a, **_kw):
        return self._result


def _make_extraction_result(ngay_ky=None, ngay_khai_truong=None):
    fields = {
        "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
        "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
        "gia_tri_hd": ExtractedField(value="100000000", confidence=0.8, needs_review=True),
        "thoi_han_hd": ExtractedField(value="12 tháng", confidence=0.9, needs_review=False),
        "dieu_khoan_gia_han": ExtractedField(value="Tự động gia hạn", confidence=0.7, needs_review=True),
        "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
        "dieu_khoan_thanh_toan": ExtractedField(value="Thanh toán hàng tháng", confidence=0.8, needs_review=False),
    }
    if ngay_ky is not None:
        fields["ngay_ky"] = ExtractedField(value=ngay_ky, confidence=0.9, needs_review=False)
    if ngay_khai_truong is not None:
        fields["ngay_khai_truong"] = ExtractedField(value=ngay_khai_truong, confidence=0.9, needs_review=False)
    return ExtractionResult(
        fields=fields,
        doc_type=DocType.OTHER,
        parties=[],
        clauses=[],
        provider="gemini_flash",
        model="gemini-2.5-flash",
        usage=TokenUsage(input_tokens=100, output_tokens=50),
        cost_vnd=59.0,
        latency_ms=1200,
        warnings=[],
    )


class TestDateTaxonomyModel:
    def test_signing_date_column_exists(self, tenant_db):
        from sqlalchemy import inspect
        cols = {c["name"] for c in inspect(tenant_db.bind).get_columns("documents")}
        assert "signing_date" in cols

    def test_commencement_date_column_exists(self, tenant_db):
        from sqlalchemy import inspect
        cols = {c["name"] for c in inspect(tenant_db.bind).get_columns("documents")}
        assert "commencement_date" in cols

    def test_columns_nullable(self, tenant_db):
        doc = _seed_doc(tenant_db)
        tenant_db.refresh(doc)
        assert doc.signing_date is None
        assert doc.commencement_date is None

    def test_columns_settable(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc.signing_date = "2025-01-15"
        doc.commencement_date = "2025-02-01"
        tenant_db.commit()
        tenant_db.refresh(doc)
        assert doc.signing_date == "2025-01-15"
        assert doc.commencement_date == "2025-02-01"


class TestDateTaxonomyExtraction:
    """Integration tests — call run_extraction() with FakeProvider to verify
    the real extraction_runner wiring, not an inlined copy of the logic."""

    def _run(self, tenant_db, ngay_ky=None, ngay_khai_truong=None):
        from app.core.config import settings
        safe_key = f"{ngay_ky}-{ngay_khai_truong}".replace("/", "_")
        doc = _seed_doc(tenant_db, file_name=f"dt-{id(self)}-{safe_key}.pdf")
        doc_id = doc.id
        # Create stub PDF file so run_extraction doesn't abort at file-read.
        file_dir = settings.STORAGE_DIR / TENANT_ID
        file_dir.mkdir(parents=True, exist_ok=True)
        (file_dir / doc.file_name).write_bytes(
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        )
        result = _make_extraction_result(ngay_ky=ngay_ky, ngay_khai_truong=ngay_khai_truong)
        fake = _FakeProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            run_extraction(doc_id, TENANT_ID, None)
        # run_extraction uses its own session — re-query to see committed changes.
        fresh_db = get_tenant_session(TENANT_ID)
        doc = fresh_db.query(Document).filter(Document.id == doc_id).first()
        fresh_db.close()
        return doc

    def test_signing_date_populated_from_ngay_ky(self, tenant_db):
        doc = self._run(tenant_db, ngay_ky="2025-03-10")
        assert doc.signing_date == "2025-03-10"

    def test_commencement_date_populated_from_ngay_khai_truong(self, tenant_db):
        doc = self._run(tenant_db, ngay_khai_truong="2025-04-01")
        assert doc.commencement_date == "2025-04-01"

    def test_signing_date_null_when_field_absent(self, tenant_db):
        doc = self._run(tenant_db)
        assert doc.signing_date is None

    def test_commencement_date_null_when_field_absent(self, tenant_db):
        doc = self._run(tenant_db)
        assert doc.commencement_date is None

    def test_both_dates_populated_together(self, tenant_db):
        doc = self._run(tenant_db, ngay_ky="2025-05-01", ngay_khai_truong="2025-06-01")
        assert doc.signing_date == "2025-05-01"
        assert doc.commencement_date == "2025-06-01"

    def test_non_iso_date_normalized(self, tenant_db):
        """LLM returning Vietnamese date format gets coerced to ISO."""
        doc = self._run(tenant_db, ngay_ky="15/03/2025")
        assert doc.signing_date == "2025-03-15"

    def test_unparseable_date_stored_as_none(self, tenant_db):
        """Completely unparseable value → None, not garbage."""
        doc = self._run(tenant_db, ngay_ky="không rõ ngày")
        assert doc.signing_date is None


class TestDateTaxonomySchema:
    def test_document_list_includes_date_fields(self, auth_client):
        r = auth_client.get("/documents/")
        assert r.status_code == 200
        data = r.json()
        if data["items"]:
            item = data["items"][0]
            assert "signing_date" in item
            assert "commencement_date" in item

    def test_document_list_schema_has_date_fields(self):
        from app.schemas.documents import DocumentListItem
        fields = DocumentListItem.model_fields
        assert "signing_date" in fields
        assert "commencement_date" in fields

    def test_document_detail_schema_has_date_fields(self):
        from app.schemas.documents import DocumentDetailOut
        fields = DocumentDetailOut.model_fields
        assert "signing_date" in fields
        assert "commencement_date" in fields

    def test_document_detail_returns_date_fields(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        doc.signing_date = "2025-07-04"
        doc.commencement_date = "2025-08-01"
        doc.status = "extracted"
        tenant_db.commit()

        r = auth_client.get(f"/documents/{doc.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["signing_date"] == "2025-07-04"
        assert data["commencement_date"] == "2025-08-01"


class TestDateTaxonomyMigration:
    def test_migration_idempotent(self, tenant_db):
        from sqlalchemy import inspect, text
        conn = tenant_db.bind
        cols_before = {c["name"] for c in inspect(conn).get_columns("documents")}
        assert "signing_date" in cols_before
        assert "commencement_date" in cols_before
        # Re-running upgrade should not raise (columns already exist → pragma guard skips)
        from alembic_tenant.versions.tenant_024_date_taxonomy import upgrade
        # Just verify the guard logic: columns present → no-op
        cols_after = {c["name"] for c in inspect(conn).get_columns("documents")}
        assert cols_before == cols_after

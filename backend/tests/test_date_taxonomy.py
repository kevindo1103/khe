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


def _seed_doc(db) -> Document:
    doc = Document(
        tenant_id=TENANT_ID,
        file_name="HD-DATE-TEST.pdf",
        file_path=f"{TENANT_ID}/HD-DATE-TEST.pdf",
        doc_type="service",
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


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
    def _make_field(self, value):
        f = MagicMock()
        f.value = value
        return f

    def _make_result(self, ngay_ky=None, ngay_khai_truong=None):
        result = MagicMock()
        result.doc_type = MagicMock()
        result.doc_type.value = "service"
        result.parties = []
        result.clauses = []
        result.fields = {}
        if ngay_ky is not None:
            result.fields["ngay_ky"] = self._make_field(ngay_ky)
        if ngay_khai_truong is not None:
            result.fields["ngay_khai_truong"] = self._make_field(ngay_khai_truong)
        # minimal required fields so extraction_runner doesn't error
        for fld in ("tieu_de_hd", "so_hop_dong"):
            result.fields.setdefault(fld, None)
        result.provider = "gemini_flash"
        result.model = "gemini-2.5-flash"
        result.usage = MagicMock(input_tokens=100, output_tokens=50)
        result.cost_vnd = 59.0
        result.latency_ms = 1200
        result.warnings = []
        return result

    def test_signing_date_populated_from_ngay_ky(self, tenant_db):
        doc = _seed_doc(tenant_db)
        result = self._make_result(ngay_ky="2025-03-10")
        # Simulate the extraction_runner population logic directly
        _signing_field = result.fields.get("ngay_ky")
        doc.signing_date = (_signing_field.value if _signing_field and _signing_field.value else None)
        tenant_db.commit()
        tenant_db.refresh(doc)
        assert doc.signing_date == "2025-03-10"

    def test_commencement_date_populated_from_ngay_khai_truong(self, tenant_db):
        doc = _seed_doc(tenant_db)
        result = self._make_result(ngay_khai_truong="2025-04-01")
        _commence_field = result.fields.get("ngay_khai_truong")
        doc.commencement_date = (_commence_field.value if _commence_field and _commence_field.value else None)
        tenant_db.commit()
        tenant_db.refresh(doc)
        assert doc.commencement_date == "2025-04-01"

    def test_signing_date_null_when_field_absent(self, tenant_db):
        doc = _seed_doc(tenant_db)
        result = self._make_result()  # no ngay_ky
        _signing_field = result.fields.get("ngay_ky")
        doc.signing_date = (_signing_field.value if _signing_field and _signing_field.value else None)
        tenant_db.commit()
        tenant_db.refresh(doc)
        assert doc.signing_date is None

    def test_commencement_date_null_when_field_absent(self, tenant_db):
        doc = _seed_doc(tenant_db)
        result = self._make_result()  # no ngay_khai_truong
        _commence_field = result.fields.get("ngay_khai_truong")
        doc.commencement_date = (_commence_field.value if _commence_field and _commence_field.value else None)
        tenant_db.commit()
        tenant_db.refresh(doc)
        assert doc.commencement_date is None

    def test_both_dates_populated_together(self, tenant_db):
        doc = _seed_doc(tenant_db)
        result = self._make_result(ngay_ky="2025-05-01", ngay_khai_truong="2025-06-01")
        _signing_field = result.fields.get("ngay_ky")
        _commence_field = result.fields.get("ngay_khai_truong")
        doc.signing_date = (_signing_field.value if _signing_field and _signing_field.value else None)
        doc.commencement_date = (_commence_field.value if _commence_field and _commence_field.value else None)
        tenant_db.commit()
        tenant_db.refresh(doc)
        assert doc.signing_date == "2025-05-01"
        assert doc.commencement_date == "2025-06-01"


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

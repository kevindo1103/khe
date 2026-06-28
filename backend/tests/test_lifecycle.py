"""Contract term + lifecycle status tests (#371, R8)."""
import os
import sys
from datetime import date, timedelta

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document
from app.services.lifecycle import EXPIRING_WINDOW_DAYS, derive_lifecycle_status
from main import app

TENANT_ID = "lifecycle-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT_ID)

    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT_ID).first():
        db.add(Tenant(id=TENANT_ID, name="Lifecycle Tenant", db_path=f"tenants/{TENANT_ID}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT_ID, TenantUser.username == "lcuser").first():
        db.add(TenantUser(
            tenant_id=TENANT_ID, username="lcuser",
            hashed_password=get_password_hash("lcpass"), role="staff",
        ))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT_ID, "username": "lcuser", "password": "lcpass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def tenant_db():
    db = get_tenant_session(TENANT_ID)
    yield db
    db.close()


def _future_date(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def _past_date(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _seed_doc(db, **kwargs) -> Document:
    doc = Document(
        tenant_id=TENANT_ID,
        file_name="HD-LIFECYCLE.pdf",
        file_path=f"{TENANT_ID}/HD-LIFECYCLE.pdf",
        doc_type="service",
        status="extracted",
        **kwargs,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ── Pure derivation logic ──

class TestDeriveLifecycleStatus:
    def test_derive_active(self):
        expiry = _future_date(EXPIRING_WINDOW_DAYS + 10)
        assert derive_lifecycle_status(None, None, expiry, None, None) == "active"

    def test_derive_expiring(self):
        expiry = _future_date(EXPIRING_WINDOW_DAYS - 1)
        assert derive_lifecycle_status(None, None, expiry, None, None) == "expiring"

    def test_derive_expiring_at_boundary(self):
        expiry = _future_date(EXPIRING_WINDOW_DAYS)
        assert derive_lifecycle_status(None, None, expiry, None, None) == "expiring"

    def test_derive_expired(self):
        expiry = _past_date(1)
        assert derive_lifecycle_status(None, None, expiry, None, None) == "expired"

    def test_derive_open_ended_contract_term(self):
        result = derive_lifecycle_status(None, None, None, "vô thời hạn", None)
        assert result == "active"

    def test_derive_open_ended_variant(self):
        result = derive_lifecycle_status(None, None, None, "không thời hạn", None)
        assert result == "active"

    def test_derive_no_dates_returns_none(self):
        assert derive_lifecycle_status(None, None, None, None, None) is None

    def test_derive_unparseable_expiry_returns_none(self):
        assert derive_lifecycle_status(None, None, "not-a-date", None, None) is None

    def test_derive_settled_sticky(self):
        expiry = _future_date(200)  # clearly active by dates
        result = derive_lifecycle_status(None, None, expiry, None, "settled")
        assert result == "settled"

    def test_derive_suspended_sticky(self):
        expiry = _future_date(200)
        result = derive_lifecycle_status(None, None, expiry, None, "suspended")
        assert result == "suspended"

    def test_derive_clear_override_auto_derived(self):
        expiry = _future_date(200)
        result = derive_lifecycle_status(None, None, expiry, None, None)
        assert result == "active"

    def test_derive_with_signing_date_ignored_for_status(self):
        expiry = _past_date(5)
        result = derive_lifecycle_status("2024-01-01", "2024-02-01", expiry, None, None)
        assert result == "expired"


# ── Model columns ──

class TestLifecycleModelColumns:
    def test_contract_term_column_exists(self, tenant_db):
        from sqlalchemy import inspect
        cols = {c["name"] for c in inspect(tenant_db.bind).get_columns("documents")}
        assert "contract_term" in cols

    def test_lifecycle_status_column_exists(self, tenant_db):
        from sqlalchemy import inspect
        cols = {c["name"] for c in inspect(tenant_db.bind).get_columns("documents")}
        assert "lifecycle_status" in cols

    def test_columns_nullable_by_default(self, tenant_db):
        doc = _seed_doc(tenant_db)
        assert doc.contract_term is None
        assert doc.lifecycle_status is None

    def test_columns_settable(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc.contract_term = "12 tháng"
        doc.lifecycle_status = "active"
        tenant_db.commit()
        tenant_db.refresh(doc)
        assert doc.contract_term == "12 tháng"
        assert doc.lifecycle_status == "active"


# ── API endpoints ──

class TestLifecycleAPI:
    def test_document_detail_includes_lifecycle_fields(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db, contract_term="24 tháng", lifecycle_status="active")
        r = auth_client.get(f"/documents/{doc.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["contract_term"] == "24 tháng"
        assert data["lifecycle_status"] == "active"

    def test_document_list_includes_lifecycle_fields(self, auth_client):
        r = auth_client.get("/documents/")
        assert r.status_code == 200
        items = r.json()["items"]
        if items:
            assert "contract_term" in items[0]
            assert "lifecycle_status" in items[0]

    def test_patch_lifecycle_settled(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db, lifecycle_status="active")
        r = auth_client.patch(f"/documents/{doc.id}", json={"lifecycle_status": "settled"})
        assert r.status_code == 200
        assert r.json()["lifecycle_status"] == "settled"

    def test_patch_lifecycle_suspended(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        r = auth_client.patch(f"/documents/{doc.id}", json={"lifecycle_status": "suspended"})
        assert r.status_code == 200
        assert r.json()["lifecycle_status"] == "suspended"

    def test_patch_lifecycle_clear_to_none(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db, lifecycle_status="settled")
        r = auth_client.patch(f"/documents/{doc.id}", json={"lifecycle_status": None})
        assert r.status_code == 200
        assert r.json()["lifecycle_status"] is None

    def test_patch_lifecycle_invalid_auto_status_rejected(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        r = auth_client.patch(f"/documents/{doc.id}", json={"lifecycle_status": "active"})
        assert r.status_code == 400

    def test_patch_lifecycle_expired_rejected(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        r = auth_client.patch(f"/documents/{doc.id}", json={"lifecycle_status": "expired"})
        assert r.status_code == 400

    def test_patch_lifecycle_logs_event(self, auth_client, tenant_db):
        from app.models.tenant import Event
        import json as _json
        doc = _seed_doc(tenant_db, lifecycle_status="active")
        auth_client.patch(f"/documents/{doc.id}", json={"lifecycle_status": "settled"})
        ev = (
            tenant_db.query(Event)
            .filter(
                Event.entity_id == doc.id,
                Event.event_type == "document_field_edited",
            )
            .order_by(Event.id.desc())
            .first()
        )
        assert ev is not None
        payload = _json.loads(ev.payload)
        assert payload["field"] == "lifecycle_status"
        assert payload["new_value"] == "settled"


# ── Migration idempotency ──

class TestLifecycleMigration:
    def test_migration_idempotent(self, tenant_db):
        from sqlalchemy import inspect
        cols_before = {c["name"] for c in inspect(tenant_db.bind).get_columns("documents")}
        assert "contract_term" in cols_before
        assert "lifecycle_status" in cols_before
        cols_after = {c["name"] for c in inspect(tenant_db.bind).get_columns("documents")}
        assert cols_before == cols_after

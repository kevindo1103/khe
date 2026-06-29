"""Ingest quota guard (FR-TN-01 / D-11, #63).

- try_consume_quota atomic gate; reset_all_quotas; get_quota_status.
- Single upload → 429 at limit, increments below limit.
- Bulk → per-file accept/quota_exceeded (PM Q4 — never fails the whole batch).
- Monthly reset job.
"""
import io
import os
import sys
from datetime import date

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.services import quota
from app.services.consent import record_consent
from main import app

TENANT = "quota-tenant"


def _pdf():
    return io.BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Quota Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "quser").first():
        db.add(TenantUser(tenant_id=TENANT, username="quser",
                          hashed_password=get_password_hash("qpass"), role="staff"))
        db.commit()
    db.close()
    tdb = get_tenant_session(TENANT)
    record_consent(tdb, TENANT, "vision_extraction", actor="quser", entity_id=1)
    tdb.close()


@pytest.fixture
def master_db():
    d = MasterSessionLocal()
    try:
        yield d
    finally:
        d.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "quser", "password": "qpass"})
    assert r.status_code == 200
    return c


def _set_quota(master_db, doc_quota, used=0):
    t = master_db.query(Tenant).filter(Tenant.id == TENANT).first()
    t.doc_quota = doc_quota
    t.docs_used_month = used
    master_db.commit()


def _used(master_db):
    master_db.expire_all()
    return master_db.query(Tenant).filter(Tenant.id == TENANT).first().docs_used_month


# ── service ──────────────────────────────────────────────────────────────────
def test_consume_until_limit(master_db):
    _set_quota(master_db, doc_quota=3, used=0)
    assert quota.try_consume_quota(master_db, TENANT) is True   # 1
    assert quota.try_consume_quota(master_db, TENANT) is True   # 2
    assert quota.try_consume_quota(master_db, TENANT) is True   # 3
    assert quota.try_consume_quota(master_db, TENANT) is False  # at limit
    assert _used(master_db) == 3                                # never over-consumes


def test_consume_unknown_tenant(master_db):
    assert quota.try_consume_quota(master_db, "nope") is False


def test_get_quota_status(master_db):
    _set_quota(master_db, doc_quota=500, used=47)
    s = quota.get_quota_status(master_db, TENANT)
    assert s["doc_quota"] == 500
    assert s["docs_used_month"] == 47


def test_reset_all_quotas(master_db):
    _set_quota(master_db, doc_quota=500, used=300)
    quota.reset_all_quotas(master_db, today=date(2026, 6, 23))
    master_db.expire_all()
    t = master_db.query(Tenant).filter(Tenant.id == TENANT).first()
    assert t.docs_used_month == 0
    assert t.quota_reset_at == date(2026, 7, 1)


# ── single upload endpoint ───────────────────────────────────────────────────
def test_upload_increments(auth_client, master_db):
    _set_quota(master_db, doc_quota=500, used=0)
    r = auth_client.post("/ingest/upload",
                         files={"file": ("c.pdf", _pdf(), "application/pdf")})
    assert r.status_code == 201
    assert _used(master_db) == 1


def test_upload_429_at_limit(auth_client, master_db):
    _set_quota(master_db, doc_quota=5, used=5)
    r = auth_client.post("/ingest/upload",
                         files={"file": ("c.pdf", _pdf(), "application/pdf")})
    assert r.status_code == 429
    assert "Quota exceeded" in r.json()["detail"]
    assert _used(master_db) == 5  # not incremented past limit


# ── bulk per-file accept/reject ──────────────────────────────────────────────
def test_bulk_partial_quota(auth_client, master_db):
    # 2 slots left, send 3 files → 2 accepted, 1 quota_exceeded.
    _set_quota(master_db, doc_quota=10, used=8)
    files = [("files", (f"d{i}.pdf", _pdf(), "application/pdf")) for i in range(3)]
    r = auth_client.post("/ingest/bulk", files=files)
    assert r.status_code == 201
    data = r.json()
    assert data["count"] == 2  # accepted count
    statuses = [d["status"] for d in data["documents"]]
    assert statuses.count("quota_exceeded") == 1
    assert _used(master_db) == 10  # exactly at limit, no over-consume
    # quota_exceeded rows carry no doc_id
    rejected = [d for d in data["documents"] if d["status"] == "quota_exceeded"]
    assert rejected[0]["doc_id"] is None

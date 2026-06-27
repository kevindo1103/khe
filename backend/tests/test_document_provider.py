"""DocumentDetailOut.provider/model from the extraction Event (#233).

Smoke gate (#175/#230) reads `provider` to decide whether `terms[].page_num`
must be non-null (gemini_flash) or may be null (claude fallback).
"""
import json
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Event
from main import app

TENANT = "provider-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Provider Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "puser").first():
        db.add(TenantUser(tenant_id=TENANT, username="puser",
                          hashed_password=get_password_hash("ppass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "puser", "password": "ppass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _doc(db, status="extracted"):
    d = Document(tenant_id=TENANT, file_name="c.pdf", file_path="x/y.pdf", status=status)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _extract_event(db, doc_id, event_type, payload):
    db.add(Event(tenant_id=TENANT, entity_type="document", entity_id=doc_id,
                 event_type=event_type, actor="system", payload=json.dumps(payload)))
    db.commit()


def test_provider_surfaced(auth_client, db):
    doc = _doc(db)
    _extract_event(db, doc.id, "extraction_performed",
                   {"provider": "gemini_flash", "model": "gemini-2.5-flash", "cost_vnd": 59})
    data = auth_client.get(f"/documents/{doc.id}").json()
    assert data["provider"] == "gemini_flash"
    assert data["model"] == "gemini-2.5-flash"


def test_provider_uses_latest_event(auth_client, db):
    doc = _doc(db)
    _extract_event(db, doc.id, "extraction_performed", {"provider": "gemini_flash", "model": "gemini-2.5-flash"})
    _extract_event(db, doc.id, "extraction_performed", {"provider": "claude_haiku", "model": "claude-haiku-4-5"})
    data = auth_client.get(f"/documents/{doc.id}").json()
    assert data["provider"] == "claude_haiku"   # most recent extraction wins


def test_provider_null_pre_extraction(auth_client, db):
    doc = _doc(db, status="pending")  # no extraction Event yet
    data = auth_client.get(f"/documents/{doc.id}").json()
    assert data["provider"] is None
    assert data["model"] is None


def test_failed_doc_provider_null_reason_kept(auth_client, db):
    doc = _doc(db, status="failed")
    _extract_event(db, doc.id, "extraction_failed", {"reason": "ExtractionUnavailable"})
    data = auth_client.get(f"/documents/{doc.id}").json()
    assert data["failure_reason"] == "ExtractionUnavailable"   # existing behavior intact
    assert data["provider"] is None                            # no extraction_performed

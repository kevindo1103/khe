"""GET /documents/{id} surfaces failure_reason on failed docs (#79 follow-up)."""
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


@pytest.fixture(scope="module", autouse=True)
def setup():
    init_master_db()
    init_tenant_db("fr-tenant")
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == "fr-tenant").first():
        db.add(Tenant(id="fr-tenant", name="FR", db_path="tenants/fr-tenant.db"))
        db.commit()
    if not db.query(TenantUser).filter(
        TenantUser.tenant_id == "fr-tenant", TenantUser.username == "fruser"
    ).first():
        db.add(TenantUser(
            tenant_id="fr-tenant", username="fruser",
            hashed_password=get_password_hash("frpass"), role="admin",
        ))
        db.commit()
    db.close()


def _client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": "fr-tenant", "username": "fruser", "password": "frpass"})
    assert r.status_code == 200
    return c


def _make_doc(status: str, with_fail_reason: str | None = None) -> int:
    s = get_tenant_session("fr-tenant")
    try:
        doc = Document(tenant_id="fr-tenant", file_name=f"{status}.pdf", file_path="x/y.pdf", status=status)
        s.add(doc)
        s.commit()
        s.refresh(doc)
        doc_id = doc.id  # capture before session close (avoid DetachedInstanceError)
        if with_fail_reason is not None:
            s.add(Event(
                tenant_id="fr-tenant",
                entity_type="document", entity_id=doc_id,
                event_type="extraction_failed", actor="system",
                payload=json.dumps({"reason": with_fail_reason}),
            ))
            s.commit()
        return doc_id
    finally:
        s.close()


def test_failed_doc_exposes_reason():
    """A failed doc surfaces the reason from the latest extraction_failed event."""
    doc_id = _make_doc("failed", with_fail_reason="Extraction exception: Request payload exceeds 20MB limit")
    c = _client()
    r = c.get(f"/documents/{doc_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "failed"
    assert data["failure_reason"] == "Extraction exception: Request payload exceeds 20MB limit"


def test_extracted_doc_failure_reason_null():
    """A successfully-extracted doc has failure_reason = None."""
    doc_id = _make_doc("extracted")
    c = _client()
    r = c.get(f"/documents/{doc_id}")
    assert r.json()["failure_reason"] is None


def test_failed_doc_with_no_event_returns_null_reason():
    """Failed doc without an extraction_failed event (shouldn't happen, but be safe)."""
    doc_id = _make_doc("failed")
    c = _client()
    r = c.get(f"/documents/{doc_id}")
    assert r.json()["failure_reason"] is None


def test_failed_doc_picks_latest_reason_on_multiple_events():
    """If a doc was re-extracted and failed twice, the LATEST reason wins."""
    s = get_tenant_session("fr-tenant")
    doc = Document(tenant_id="fr-tenant", file_name="retry.pdf", file_path="x/y.pdf", status="failed")
    s.add(doc); s.commit(); s.refresh(doc)
    s.add(Event(tenant_id="fr-tenant", entity_type="document", entity_id=doc.id,
                event_type="extraction_failed", actor="system",
                payload=json.dumps({"reason": "first failure"})))
    s.commit()
    s.add(Event(tenant_id="fr-tenant", entity_type="document", entity_id=doc.id,
                event_type="extraction_failed", actor="system",
                payload=json.dumps({"reason": "second failure"})))
    s.commit()
    doc_id = doc.id
    s.close()

    c = _client()
    assert c.get(f"/documents/{doc_id}").json()["failure_reason"] == "second failure"

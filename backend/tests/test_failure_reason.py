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


def _make_doc(
    status: str,
    with_fail_reason: str | None = None,
    processing_stage: str | None = None,
    extraction_warnings: list[str] | None = None,
    event_type: str = "extraction_failed",
) -> int:
    s = get_tenant_session("fr-tenant")
    try:
        doc = Document(
            tenant_id="fr-tenant", file_name=f"{status}.pdf", file_path="x/y.pdf", status=status,
            processing_stage=processing_stage,
            extraction_warnings=json.dumps(extraction_warnings) if extraction_warnings else None,
        )
        s.add(doc)
        s.commit()
        s.refresh(doc)
        doc_id = doc.id  # capture before session close (avoid DetachedInstanceError)
        if with_fail_reason is not None:
            s.add(Event(
                tenant_id="fr-tenant",
                entity_type="document", entity_id=doc_id,
                event_type=event_type, actor="system",
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


# ── Transient failures (#436/#446, QC review PR #458) ────────────────────────
# Previously failure_reason/extraction_warnings only surfaced for status=="failed",
# so a doc kept retryable by `_mark_transient_failure` (status stays "pending")
# never showed its reason to the API — the backend recorded the failure correctly
# but the read path silently dropped it. Fixed: also check
# processing_stage=="retry_needed" and expose extraction_warnings directly.


def test_retry_needed_doc_exposes_reason():
    """A doc kept retryable (status='pending', processing_stage='retry_needed')
    surfaces the reason from the latest extraction_transient_failure event —
    not just terminal 'failed' docs."""
    doc_id = _make_doc(
        "pending",
        with_fail_reason="Document quá lớn, đã cắt bớt kết quả.",
        processing_stage="retry_needed",
        event_type="extraction_transient_failure",
    )
    c = _client()
    r = c.get(f"/documents/{doc_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "pending"
    assert data["processing_stage"] == "retry_needed"
    assert data["failure_reason"] == "Document quá lớn, đã cắt bớt kết quả."


def test_retry_needed_doc_exposes_extraction_warnings():
    """extraction_warnings (raw provider warnings) is exposed on the doc row,
    independent of the Event-derived failure_reason."""
    doc_id = _make_doc(
        "pending",
        processing_stage="retry_needed",
        extraction_warnings=["gemini_flash extract failed: 503 The model is overloaded."],
    )
    c = _client()
    data = c.get(f"/documents/{doc_id}").json()
    assert data["extraction_warnings"] == ["gemini_flash extract failed: 503 The model is overloaded."]


def test_plain_pending_doc_has_no_failure_reason():
    """A freshly-uploaded doc (processing_stage=None, not 'retry_needed') has no
    failure_reason — distinguishes 'never started' from 'needs retry'."""
    doc_id = _make_doc("pending")
    c = _client()
    data = c.get(f"/documents/{doc_id}").json()
    assert data["failure_reason"] is None
    assert data["processing_stage"] is None

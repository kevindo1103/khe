"""Tests for GET /documents/{doc_id}/events endpoint (#281)."""
import json
import pytest
from fastapi.testclient import TestClient

from app.db.database import get_tenant_session
from app.models.tenant import Document, Event, Obligation


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_doc(db, tenant_id, file_name="contract.pdf"):
    doc = Document(
        tenant_id=tenant_id,
        file_name=file_name,
        file_path=f"{tenant_id}/{file_name}",
        status="extracted",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _add_event(db, tenant_id, entity_type, entity_id, event_type, actor="system", payload=None):
    ev = Event(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        actor=actor,
        payload=json.dumps(payload) if payload else None,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_empty_events_returns_200(auth_client, test_tenant, db):
    """No events → 200 with empty items list, not 404."""
    doc = _make_doc(db, test_tenant)
    r = auth_client.get(f"/documents/{doc.id}/events")
    assert r.status_code == 200
    data = r.json()
    assert data["document_id"] == doc.id
    assert data["total"] == 0
    assert data["items"] == []


def test_document_events_included(auth_client, test_tenant, db):
    """Events with entity_type='document' for this doc are returned."""
    doc = _make_doc(db, test_tenant)
    _add_event(db, test_tenant, "document", doc.id, "extraction_performed")
    _add_event(db, test_tenant, "document", doc.id, "updated", actor="qcuser")

    r = auth_client.get(f"/documents/{doc.id}/events")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    event_types = {ev["event_type"] for ev in data["items"]}
    assert "extraction_performed" in event_types
    assert "updated" in event_types


def test_obligation_events_included(auth_client, test_tenant, db):
    """Events for obligations belonging to this document are included."""
    doc = _make_doc(db, test_tenant)
    ob = Obligation(
        tenant_id=test_tenant,
        document_id=doc.id,
        description="Test obligation",
        obligation_type="payment",
        recurrence="once",
        status="done",
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)

    _add_event(db, test_tenant, "document", doc.id, "extraction_performed")
    _add_event(db, test_tenant, "obligation", ob.id, "obligation_fulfilled", actor="qcuser")

    r = auth_client.get(f"/documents/{doc.id}/events")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    entity_types = {ev["entity_type"] for ev in data["items"]}
    assert "document" in entity_types
    assert "obligation" in entity_types


def test_other_doc_events_excluded(auth_client, test_tenant, db):
    """Events for a different document's obligations do not leak in."""
    doc1 = _make_doc(db, test_tenant, "contract1.pdf")
    doc2 = _make_doc(db, test_tenant, "contract2.pdf")

    _add_event(db, test_tenant, "document", doc1.id, "extraction_performed")
    _add_event(db, test_tenant, "document", doc2.id, "extraction_performed")

    r = auth_client.get(f"/documents/{doc1.id}/events")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert all(ev["entity_id"] == doc1.id for ev in data["items"])


def test_events_ordered_newest_first(auth_client, test_tenant, db):
    """Events are returned in descending created_at order."""
    doc = _make_doc(db, test_tenant)
    ev1 = _add_event(db, test_tenant, "document", doc.id, "created")
    ev2 = _add_event(db, test_tenant, "document", doc.id, "extraction_performed")
    ev3 = _add_event(db, test_tenant, "document", doc.id, "updated")

    r = auth_client.get(f"/documents/{doc.id}/events")
    assert r.status_code == 200
    ids = [ev["id"] for ev in r.json()["items"]]
    # newest (highest id) first when same timestamp
    assert ids[0] >= ids[-1]


def test_pagination_limit(auth_client, test_tenant, db):
    """limit= query param is honoured."""
    doc = _make_doc(db, test_tenant)
    for i in range(10):
        _add_event(db, test_tenant, "document", doc.id, f"event_{i}")

    r = auth_client.get(f"/documents/{doc.id}/events?limit=3")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 10
    assert len(data["items"]) == 3
    assert data["limit"] == 3
    assert data["offset"] == 0


def test_pagination_offset(auth_client, test_tenant, db):
    """offset= query param skips events correctly."""
    doc = _make_doc(db, test_tenant)
    for i in range(5):
        _add_event(db, test_tenant, "document", doc.id, f"event_{i}")

    r_all = auth_client.get(f"/documents/{doc.id}/events?limit=5&offset=0")
    r_offset = auth_client.get(f"/documents/{doc.id}/events?limit=5&offset=2")

    all_ids = [ev["id"] for ev in r_all.json()["items"]]
    offset_ids = [ev["id"] for ev in r_offset.json()["items"]]
    assert offset_ids == all_ids[2:]


def test_payload_deserialized_as_dict(auth_client, test_tenant, db):
    """JSON payload is returned as a dict, not a raw string."""
    doc = _make_doc(db, test_tenant)
    _add_event(db, test_tenant, "document", doc.id, "extraction_performed",
               payload={"provider": "gemini_flash", "cost_vnd": 59.5})

    r = auth_client.get(f"/documents/{doc.id}/events")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert isinstance(item["payload"], dict)
    assert item["payload"]["provider"] == "gemini_flash"


def test_404_for_unknown_doc(auth_client, test_tenant):
    """GET events for a non-existent doc returns 404."""
    r = auth_client.get("/documents/99999/events")
    assert r.status_code == 404


def test_tenant_isolation(test_tenant, db):
    """Events from another tenant's document are not visible."""
    import uuid
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
        other_doc = _make_doc(other_db, other_id, "other_contract.pdf")
        _add_event(other_db, other_id, "document", other_doc.id, "extraction_performed")
        other_doc_id = other_doc.id
    finally:
        other_db.close()

    try:
        # Log in as main tenant and try to access the other tenant's doc
        c = TestClient(__import__("main").app)
        r = c.post("/auth/login", json={"tenant_id": test_tenant, "username": "qcuser", "password": "qcpass"})
        assert r.status_code == 200

        r = c.get(f"/documents/{other_doc_id}/events")
        assert r.status_code == 404, "Cross-tenant doc should not be visible"
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


def test_no_obligation_events_bleed_when_no_obligations(auth_client, test_tenant, db):
    """Doc with no obligations: only document-scoped events returned, no crash."""
    doc = _make_doc(db, test_tenant)
    _add_event(db, test_tenant, "document", doc.id, "created")

    r = auth_client.get(f"/documents/{doc.id}/events")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["entity_type"] == "document"

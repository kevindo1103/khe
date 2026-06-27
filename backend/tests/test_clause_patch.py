"""Tests for PATCH /documents/{doc_id}/clauses/{clause_id} (#324, Task 1)."""
import pytest

from app.db.database import get_tenant_session
from app.models.tenant import Clause, Document, Event


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _make_clause(db, tenant_id, doc_id, content="Original AI text.", clause_num="Điều 1"):
    clause = Clause(
        tenant_id=tenant_id,
        document_id=doc_id,
        clause_num=clause_num,
        title="Test clause",
        content=content,
        page_num=1,
    )
    db.add(clause)
    db.commit()
    db.refresh(clause)
    return clause


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_happy_path_edit(auth_client, test_tenant, db):
    """Successful first edit updates content and returns ClausePatchOut."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, content="AI extracted text.")

    r = auth_client.patch(
        f"/documents/{doc.id}/clauses/{clause.id}",
        json={"content": "User corrected text."},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == clause.id
    assert data["content"] == "User corrected text."
    assert data["edited_by_user"] == "qcuser"
    assert data["edited_at"] is not None


def test_first_edit_snapshots_original_content(auth_client, test_tenant, db):
    """First edit snapshots original_content from AI extraction (D-07)."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, content="Original AI text.")

    r = auth_client.patch(
        f"/documents/{doc.id}/clauses/{clause.id}",
        json={"content": "User corrected text."},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["original_content"] == "Original AI text."
    assert data["content"] == "User corrected text."


def test_second_edit_preserves_original_content(auth_client, test_tenant, db):
    """Subsequent edits update content but do NOT overwrite original_content."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, content="Original AI text.")

    auth_client.patch(
        f"/documents/{doc.id}/clauses/{clause.id}",
        json={"content": "First user edit."},
    )
    r2 = auth_client.patch(
        f"/documents/{doc.id}/clauses/{clause.id}",
        json={"content": "Second user edit."},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["original_content"] == "Original AI text."
    assert data["content"] == "Second user edit."


def test_clause_edited_event_logged(auth_client, test_tenant, db):
    """clause_edited Event is written on each edit (D-07 audit)."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, content="AI text.")

    r = auth_client.patch(
        f"/documents/{doc.id}/clauses/{clause.id}",
        json={"content": "Edited text."},
    )
    assert r.status_code == 200

    db.expire_all()
    event = (
        db.query(Event)
        .filter(Event.entity_type == "document", Event.event_type == "clause_edited")
        .first()
    )
    assert event is not None
    assert event.actor == "qcuser"
    assert event.entity_id == doc.id


def test_event_payload_pii_safe(auth_client, test_tenant, db):
    """Event payload contains lengths, NOT raw content (D-12 spirit)."""
    import json
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, content="AI text.")

    auth_client.patch(
        f"/documents/{doc.id}/clauses/{clause.id}",
        json={"content": "Edited."},
    )

    db.expire_all()
    event = (
        db.query(Event)
        .filter(Event.event_type == "clause_edited")
        .first()
    )
    payload = json.loads(event.payload)
    assert "old_value_length" in payload
    assert "new_value_length" in payload
    assert "content" not in payload  # raw content must NOT be logged


def test_404_wrong_clause_id(auth_client, test_tenant, db):
    """Non-existent clause returns 404."""
    doc = _make_doc(db, test_tenant)
    r = auth_client.patch(
        f"/documents/{doc.id}/clauses/99999",
        json={"content": "Edited."},
    )
    assert r.status_code == 404


def test_404_wrong_doc_id(auth_client, test_tenant, db):
    """Clause from a different doc returns 404."""
    doc1 = _make_doc(db, test_tenant, "contract1.pdf")
    doc2 = _make_doc(db, test_tenant, "contract2.pdf")
    clause = _make_clause(db, test_tenant, doc2.id, content="Text.")

    r = auth_client.patch(
        f"/documents/{doc1.id}/clauses/{clause.id}",
        json={"content": "Edited."},
    )
    assert r.status_code == 404


def test_tenant_isolation(db, test_tenant):
    """Clause belonging to another tenant returns 404."""
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
        other_doc = _make_doc(other_db, other_id, "other.pdf")
        other_clause = _make_clause(other_db, other_id, other_doc.id)
        other_clause_id = other_clause.id
        other_doc_id = other_doc.id
    finally:
        other_db.close()

    try:
        c = TestClient(__import__("main").app)
        r = c.post("/auth/login", json={"tenant_id": test_tenant, "username": "qcuser", "password": "qcpass"})
        assert r.status_code == 200

        r = c.patch(
            f"/documents/{other_doc_id}/clauses/{other_clause_id}",
            json={"content": "Injected edit."},
        )
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


def test_existing_clauses_tests_still_pass(auth_client, test_tenant, db):
    """Smoke: clause list still works after model changes."""
    doc = _make_doc(db, test_tenant)
    _make_clause(db, test_tenant, doc.id)

    r = auth_client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200
    data = r.json()
    assert data["clause_count"] == 1
    # ClauseOut.id is present (added in PR #323)
    assert "id" in data["clauses"][0]

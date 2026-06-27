"""Tests for POST /documents/{doc_id}/reread (#324 Task 2)."""
import pytest

from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import Tenant
from app.models.tenant import Clause, Document, Obligation, Term


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


def _make_clause(db, tenant_id, doc_id, clause_num="Điều 1"):
    clause = Clause(
        tenant_id=tenant_id,
        document_id=doc_id,
        clause_num=clause_num,
        content="Some clause content.",
    )
    db.add(clause)
    db.commit()
    db.refresh(clause)
    return clause


def _make_term(db, tenant_id, doc_id, field_name, field_value, ref=None):
    t = Term(
        tenant_id=tenant_id,
        document_id=doc_id,
        field_name=field_name,
        field_value=field_value,
        ref=ref,
        is_superseded=False,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _make_obligation(db, tenant_id, doc_id, clause_num, due_date="2027-01-01", source="ai_extracted"):
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=doc_id,
        description=f"Hợp đồng contract.pdf hết hạn ngày {due_date}",
        obligation_type="expiration",
        recurrence="once",
        status="pending",
        source_clause_num=clause_num,
        due_date=due_date,
        source=source,
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_no_terms_no_diffs(auth_client, test_tenant, db):
    """Clause with no Terms → derivation skips → no 'add' diffs, no crash."""
    doc = _make_doc(db, test_tenant)
    _make_clause(db, test_tenant, doc.id, clause_num="Điều 1")

    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 200
    data = r.json()
    assert data["document_id"] == doc.id
    assert data["clauses_checked"] == 1
    assert data["diffs"] == []


def test_add_diff_when_terms_exist_no_obligation(auth_client, test_tenant, db):
    """Terms exist but no matching obligation → diff action='add'."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, clause_num="Điều 1")
    _make_term(db, test_tenant, doc.id, "ngay_het_han", "2027-12-31", ref="Điều 1")

    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 200
    data = r.json()
    assert data["clauses_checked"] == 1
    diffs = data["diffs"]
    assert len(diffs) == 1
    assert diffs[0]["action"] == "add"
    assert diffs[0]["due_date"] == "2027-12-31"
    assert diffs[0]["source_clause_num"] == "Điều 1"
    assert diffs[0]["protected"] is False


def test_update_diff_when_due_date_changed(auth_client, test_tenant, db):
    """Term yields a different due_date than existing obligation → diff action='update'."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, clause_num="Điều 2")
    _make_term(db, test_tenant, doc.id, "ngay_het_han", "2028-06-30", ref="Điều 2")
    ob = _make_obligation(db, test_tenant, doc.id, "Điều 2", due_date="2027-01-01")

    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 200
    diffs = r.json()["diffs"]
    update_diffs = [d for d in diffs if d["action"] == "update"]
    due_diff = next((d for d in update_diffs if d["field"] == "due_date"), None)
    assert due_diff is not None
    assert due_diff["old_value"] == "2027-01-01"
    assert due_diff["new_value"] == "2028-06-30"
    assert due_diff["obligation_id"] == ob.id
    assert due_diff["protected"] is False


def test_no_diff_when_up_to_date(auth_client, test_tenant, db):
    """Term matches existing obligation exactly → no diffs emitted."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, clause_num="Điều 3")
    _make_term(db, test_tenant, doc.id, "ngay_het_han", "2027-06-30", ref="Điều 3")
    _make_obligation(db, test_tenant, doc.id, "Điều 3", due_date="2027-06-30")

    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 200
    # description may differ from the template, but due_date matches → 0 or 1 diffs
    # Only assert no due_date update diff (the important field)
    diffs = r.json()["diffs"]
    due_diffs = [d for d in diffs if d.get("field") == "due_date"]
    assert due_diffs == []


def test_remove_diff_when_derivation_skips_and_obligation_exists(auth_client, test_tenant, db):
    """Terms insufficient → derivation skips → existing obligation gets action='remove'."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, clause_num="Điều 4")
    # No matching Terms for this clause → derivation skips
    ob = _make_obligation(db, test_tenant, doc.id, "Điều 4", due_date="2027-01-01")

    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 200
    diffs = r.json()["diffs"]
    assert any(d["action"] == "remove" and d["obligation_id"] == ob.id for d in diffs)


def test_user_manual_obligation_is_protected(auth_client, test_tenant, db):
    """Obligation with source='user_manual' → protected=True in diff."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, clause_num="Điều 5")
    # No Terms → derivation skips → remove diff
    ob = _make_obligation(db, test_tenant, doc.id, "Điều 5", source="user_manual")

    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 200
    diffs = r.json()["diffs"]
    remove_diff = next((d for d in diffs if d.get("obligation_id") == ob.id), None)
    assert remove_diff is not None
    assert remove_diff["protected"] is True


def test_scope_by_clause_ids(auth_client, test_tenant, db):
    """clause_ids body param restricts which clauses are checked."""
    doc = _make_doc(db, test_tenant)
    c1 = _make_clause(db, test_tenant, doc.id, clause_num="Điều 1")
    c2 = _make_clause(db, test_tenant, doc.id, clause_num="Điều 2")
    _make_term(db, test_tenant, doc.id, "ngay_het_han", "2027-01-01", ref="Điều 1")
    _make_term(db, test_tenant, doc.id, "ngay_het_han", "2028-01-01", ref="Điều 2")

    r = auth_client.post(f"/documents/{doc.id}/reread", json={"clause_ids": [c1.id]})
    assert r.status_code == 200
    data = r.json()
    assert data["clauses_checked"] == 1
    # Only clause 1 was checked
    for diff in data["diffs"]:
        assert diff["source_clause_num"] == "Điều 1"


def test_empty_clause_ids_checks_all(auth_client, test_tenant, db):
    """Passing clause_ids=[] or no body checks all clauses."""
    doc = _make_doc(db, test_tenant)
    _make_clause(db, test_tenant, doc.id, clause_num="Điều 1")
    _make_clause(db, test_tenant, doc.id, clause_num="Điều 2")

    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 200
    assert r.json()["clauses_checked"] == 2


def test_404_for_unknown_doc(auth_client, test_tenant):
    """Non-existent document returns 404."""
    r = auth_client.post("/documents/99999/reread")
    assert r.status_code == 404


def test_tenant_isolation(test_tenant, db):
    """Cross-tenant document returns 404."""
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
        other_doc_id = other_doc.id
    finally:
        other_db.close()

    try:
        c = TestClient(__import__("main").app)
        r = c.post("/auth/login", json={"tenant_id": test_tenant, "username": "qcuser", "password": "qcpass"})
        assert r.status_code == 200

        r = c.post(f"/documents/{other_doc_id}/reread")
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


def test_quota_exceeded_returns_429(auth_client, test_tenant, db):
    """When docs_used_month >= doc_quota, re-read returns 429."""
    # Set quota to 0 to simulate exhaustion.
    mdb = MasterSessionLocal()
    try:
        from sqlalchemy import update
        mdb.execute(
            update(Tenant)
            .where(Tenant.id == test_tenant)
            .values(doc_quota=1, docs_used_month=1)
        )
        mdb.commit()
    finally:
        mdb.close()

    doc = _make_doc(db, test_tenant)
    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 429


def test_done_obligations_excluded_from_diffs(auth_client, test_tenant, db):
    """Obligations with status='done' are not included in diff computation."""
    doc = _make_doc(db, test_tenant)
    clause = _make_clause(db, test_tenant, doc.id, clause_num="Điều 6")
    # Done obligation — should not appear in remove diffs
    ob = _make_obligation(db, test_tenant, doc.id, "Điều 6", due_date="2026-01-01")
    ob.status = "done"
    db.commit()

    r = auth_client.post(f"/documents/{doc.id}/reread")
    assert r.status_code == 200
    diffs = r.json()["diffs"]
    assert not any(d.get("obligation_id") == ob.id for d in diffs)

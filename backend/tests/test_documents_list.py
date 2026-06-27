"""Tests for GET /documents/ list — 6 new obligation-centric fields (#287 / #279).

Covers:
  - primary_party: first non-self party; NULL when no non-self parties
  - next_due_date: nearest active dated obligation; NULL for standing-only / empty
  - direction split: nghia_vu + quyen_loi + direction_null == active obligation total
  - terminal-status obligations excluded from all direction tallies
  - q search by party name returns doc; miss returns empty
  - regression: existing fields (term_count / obligation_count / clause_count / needs_review) unchanged
"""
import uuid

import pytest
from fastapi.testclient import TestClient

import main as _main_mod
from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import TenantProfile, TenantUser, Tenant
from app.models.tenant import Clause, Document, Obligation, Party, Term
from app.core.security import get_password_hash
from app.db.database import init_master_db, init_tenant_db, _engine_cache, _cache_lock, TENANTS_DIR
from app.services.consent import record_consent


# ── fixtures ──────────────────────────────────────────────────────────────────

def _reset_tenant_db(tid: str):
    with _cache_lock:
        eng = _engine_cache.pop(tid, None)
    if eng is not None:
        eng.dispose()
    for suffix in ("", "-wal", "-shm"):
        f = TENANTS_DIR / f"{tid}.db{suffix}"
        try:
            f.unlink()
        except FileNotFoundError:
            pass


def _cleanup_master(tenant_id: str):
    db = MasterSessionLocal()
    try:
        from app.models.master import TenantUser, TenantProfile, Tenant
        db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id).delete()
        db.query(TenantProfile).filter(TenantProfile.tenant_id == tenant_id).delete()
        db.query(Tenant).filter(Tenant.id == tenant_id).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def tenant_id():
    tid = f"doclist-{uuid.uuid4().hex[:8]}"
    init_master_db()
    init_tenant_db(tid)

    mdb = MasterSessionLocal()
    try:
        mdb.add(Tenant(id=tid, name=f"DocList Test {tid}", db_path=f"tenants/{tid}.db"))
        mdb.add(TenantUser(
            tenant_id=tid,
            username="tuser",
            hashed_password=get_password_hash("tpass"),
            role="admin",
        ))
        mdb.commit()
    finally:
        mdb.close()

    tdb = get_tenant_session(tid)
    try:
        record_consent(tdb, tid, "vision_extraction", actor="tuser", entity_id=1)
    finally:
        tdb.close()

    yield tid

    _reset_tenant_db(tid)
    _cleanup_master(tid)


@pytest.fixture
def client(tenant_id):
    c = TestClient(_main_mod.app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": tenant_id, "username": "tuser", "password": "tpass"},
    )
    assert r.status_code == 200, f"Login failed: {r.text}"
    # Cookie is stored automatically by TestClient — no manual header needed.
    return c


@pytest.fixture
def tdb(tenant_id):
    s = get_tenant_session(tenant_id)
    try:
        yield s
    finally:
        s.close()


def _make_doc(db, tid, file_name="contract.pdf", status="done"):
    doc = Document(tenant_id=tid, file_name=file_name, file_path=f"{tid}/{file_name}", status=status)
    db.add(doc)
    db.flush()
    return doc


# ── tests ─────────────────────────────────────────────────────────────────────

def test_primary_party_first_non_self(client, tdb, tenant_id):
    """primary_party = first non-self party (by id ASC); self-party excluded."""
    # Set legal_name so self-match works.
    mdb = MasterSessionLocal()
    try:
        mdb.add(TenantProfile(tenant_id=tenant_id, legal_name="Công ty TNHH ABC"))
        mdb.commit()
    finally:
        mdb.close()

    doc = _make_doc(tdb, tenant_id)
    # self party first (id lowest)
    tdb.add(Party(tenant_id=tenant_id, document_id=doc.id, name="Công ty TNHH ABC", role_label="bên_a"))
    # counterparty second
    tdb.add(Party(tenant_id=tenant_id, document_id=doc.id, name="Công ty XYZ", role_label="bên_b"))
    tdb.commit()

    r = client.get("/documents/")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["primary_party"] == "Công ty XYZ"


def test_primary_party_null_when_no_non_self(client, tdb, tenant_id):
    """primary_party = None when document has only self-party."""
    mdb = MasterSessionLocal()
    try:
        mdb.add(TenantProfile(tenant_id=tenant_id, legal_name="Công ty TNHH ABC"))
        mdb.commit()
    finally:
        mdb.close()

    doc = _make_doc(tdb, tenant_id)
    tdb.add(Party(tenant_id=tenant_id, document_id=doc.id, name="Công ty TNHH ABC", role_label="bên_a"))
    tdb.commit()

    r = client.get("/documents/")
    assert r.status_code == 200
    assert r.json()["items"][0]["primary_party"] is None


def test_next_due_date_nearest_active(client, tdb, tenant_id):
    """next_due_date = nearest active dated obligation; done/cancelled excluded."""
    doc = _make_doc(tdb, tenant_id)
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="pay rent", due_date="2025-03-01", status="pending"))
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="renew", due_date="2025-01-15", status="pending"))
    # terminal — should not affect next_due_date
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="old", due_date="2024-01-01", status="done"))
    tdb.commit()

    r = client.get("/documents/")
    assert r.status_code == 200
    assert r.json()["items"][0]["next_due_date"] == "2025-01-15"


def test_next_due_date_null_for_standing_only(client, tdb, tenant_id):
    """next_due_date = None when only standing obligations (due_date NULL) exist."""
    doc = _make_doc(tdb, tenant_id)
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="keep secret", due_date=None, status="pending"))
    tdb.commit()

    r = client.get("/documents/")
    assert r.status_code == 200
    assert r.json()["items"][0]["next_due_date"] is None


def test_direction_counts_sum_to_active_total(client, tdb, tenant_id):
    """nghia_vu + quyen_loi + direction_null == active obligation count; terminal excluded."""
    doc = _make_doc(tdb, tenant_id)
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="a", due_date="2025-06-01", status="pending", direction="nghĩa_vụ"))
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="b", due_date=None, status="pending", direction="quyền_lợi"))
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="c", due_date="2025-07-01", status="pending", direction=None))
    # terminal — excluded from all tallies
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="done", due_date="2024-01-01", status="cancelled", direction="nghĩa_vụ"))
    tdb.commit()

    r = client.get("/documents/")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["nghia_vu_count"] == 1
    assert item["quyen_loi_count"] == 1
    assert item["direction_null_count"] == 1
    assert item["nghia_vu_count"] + item["quyen_loi_count"] + item["direction_null_count"] == 3


def test_search_by_party_name(client, tdb, tenant_id):
    """q= searches party name; returns matching doc, excludes non-matching doc."""
    doc1 = _make_doc(tdb, tenant_id, file_name="lease.pdf")
    doc2 = _make_doc(tdb, tenant_id, file_name="labor.pdf")
    tdb.add(Party(tenant_id=tenant_id, document_id=doc1.id, name="Công ty Mùa Vàng", role_label="bên_b"))
    tdb.commit()

    r = client.get("/documents/?q=Mùa+Vàng")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == doc1.id

    r_miss = client.get("/documents/?q=NonExistentCo")
    assert r_miss.status_code == 200
    assert r_miss.json()["total"] == 0


def test_existing_fields_regression(client, tdb, tenant_id):
    """term_count / obligation_count / clause_count / needs_review unchanged."""
    doc = _make_doc(tdb, tenant_id)
    tdb.add(Term(tenant_id=tenant_id, document_id=doc.id, field_name="effective_date",
                  field_value="2025-01-01", needs_review=True))
    tdb.add(Term(tenant_id=tenant_id, document_id=doc.id, field_name="expiry_date",
                  field_value="2026-01-01", needs_review=False))
    tdb.add(Obligation(tenant_id=tenant_id, document_id=doc.id,
                        description="pay", due_date="2025-06-01", status="pending"))
    tdb.add(Clause(tenant_id=tenant_id, document_id=doc.id,
                    clause_num="1", title="Điều 1", content="..."))
    tdb.commit()

    r = client.get("/documents/")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["term_count"] == 2
    assert item["obligation_count"] == 1
    assert item["clause_count"] == 1
    assert item["needs_review"] is True
    assert item["may_have_unextracted_obligations"] is None

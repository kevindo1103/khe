"""Tests for GET /documents/{id}/clauses (#284).

Covers:
  - AC: returns ClauseListOut with clauses ordered by page_num → id
  - AC: empty clauses → 200 with clause_count=0, NOT 404
  - AC: tenant isolation — doc from other tenant → 404
  - AC: page_min/page_max computed correctly (null when all page_num are null)
  - AC: 404 for non-existent doc
"""
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

import main as _main_mod
from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import TenantUser, Tenant
from app.models.tenant import Clause, Document
from app.core.security import get_password_hash
from app.db.database import init_master_db, init_tenant_db, _engine_cache, _cache_lock, TENANTS_DIR
from app.services.consent import record_consent


# ── helpers ────────────────────────────────────────────────────────────────────

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
        db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id).delete()
        db.query(Tenant).filter(Tenant.id == tenant_id).delete()
        db.commit()
    finally:
        db.close()


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def tenant_id():
    tid = f"clauses-{uuid.uuid4().hex[:8]}"
    init_master_db()
    init_tenant_db(tid)

    mdb = MasterSessionLocal()
    try:
        mdb.add(Tenant(id=tid, name=f"Clauses Test {tid}", db_path=f"tenants/{tid}.db"))
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
def other_tenant_id():
    tid = f"clauses-other-{uuid.uuid4().hex[:8]}"
    init_master_db()
    init_tenant_db(tid)

    mdb = MasterSessionLocal()
    try:
        mdb.add(Tenant(id=tid, name=f"Other {tid}", db_path=f"tenants/{tid}.db"))
        mdb.add(TenantUser(
            tenant_id=tid,
            username="other",
            hashed_password=get_password_hash("otherpass"),
            role="admin",
        ))
        mdb.commit()
    finally:
        mdb.close()

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
    return c


@pytest.fixture
def tdb(tenant_id):
    s = get_tenant_session(tenant_id)
    try:
        yield s
    finally:
        s.close()


def _make_doc(db, tid):
    doc = Document(
        tenant_id=tid,
        file_name="contract.pdf",
        file_path=f"{tid}/contract.pdf",
        status="done",
        confirmed_by_user_at=datetime.utcnow(),
    )
    db.add(doc)
    db.flush()
    return doc


def _make_clause(db, tid, doc_id, clause_num=None, title=None, content="Nội dung điều khoản.", page_num=None):
    c = Clause(
        tenant_id=tid,
        document_id=doc_id,
        clause_num=clause_num,
        title=title,
        content=content,
        page_num=page_num,
    )
    db.add(c)
    db.flush()
    return c


# ── AC: basic response structure ──────────────────────────────────────────────

def test_clauses_returns_clause_list(client, tdb, tenant_id):
    """GET /documents/{id}/clauses returns ClauseListOut with all clauses."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, clause_num="Điều 1", title="Định nghĩa", content="Các định nghĩa.", page_num=1)
    _make_clause(tdb, tenant_id, doc.id, clause_num="Điều 2", title="Phạm vi", content="Phạm vi áp dụng.", page_num=2)
    tdb.commit()

    r = client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["document_id"] == doc.id
    assert body["clause_count"] == 2
    assert len(body["clauses"]) == 2
    assert body["clauses"][0]["clause_num"] == "Điều 1"
    assert body["clauses"][1]["clause_num"] == "Điều 2"


# ── AC: empty clauses → 200 (not 404) ────────────────────────────────────────

def test_empty_clauses_returns_200(client, tdb, tenant_id):
    """Doc with no clauses returns 200 with clause_count=0, not 404."""
    doc = _make_doc(tdb, tenant_id)
    tdb.commit()

    r = client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["clause_count"] == 0
    assert body["clauses"] == []
    assert body["page_min"] is None
    assert body["page_max"] is None


# ── AC: ordering page_num ASC NULLS LAST → id ASC ────────────────────────────

def test_clauses_ordered_by_page_then_id(client, tdb, tenant_id):
    """Clauses ordered: page_num ASC NULLS LAST, then id ASC."""
    doc = _make_doc(tdb, tenant_id)
    c3 = _make_clause(tdb, tenant_id, doc.id, clause_num="Điều 3", page_num=3)
    c1 = _make_clause(tdb, tenant_id, doc.id, clause_num="Điều 1", page_num=1)
    cnull = _make_clause(tdb, tenant_id, doc.id, clause_num="Phụ lục", page_num=None)
    c2 = _make_clause(tdb, tenant_id, doc.id, clause_num="Điều 2", page_num=2)
    tdb.commit()

    r = client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200, r.text
    nums = [c["clause_num"] for c in r.json()["clauses"]]
    assert nums == ["Điều 1", "Điều 2", "Điều 3", "Phụ lục"]


# ── AC: page_min / page_max ────────────────────────────────────────────────────

def test_page_min_max_computed(client, tdb, tenant_id):
    """page_min and page_max reflect actual page_num range."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, page_num=3)
    _make_clause(tdb, tenant_id, doc.id, page_num=1)
    _make_clause(tdb, tenant_id, doc.id, page_num=None)
    _make_clause(tdb, tenant_id, doc.id, page_num=7)
    tdb.commit()

    r = client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200
    body = r.json()
    assert body["page_min"] == 1
    assert body["page_max"] == 7


def test_page_min_max_null_when_all_null(client, tdb, tenant_id):
    """page_min/page_max are null when all clause page_num are null."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, page_num=None)
    _make_clause(tdb, tenant_id, doc.id, page_num=None)
    tdb.commit()

    r = client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200
    body = r.json()
    assert body["page_min"] is None
    assert body["page_max"] is None
    assert body["clause_count"] == 2


# ── AC: tenant isolation ──────────────────────────────────────────────────────

def test_other_tenant_doc_returns_404(client, tdb, tenant_id, other_tenant_id):
    """Doc belonging to another tenant → 404 (tenant isolation)."""
    other_db = get_tenant_session(other_tenant_id)
    try:
        other_doc = _make_doc(other_db, other_tenant_id)
        _make_clause(other_db, other_tenant_id, other_doc.id, clause_num="Điều 1", page_num=1)
        other_db.commit()
        other_doc_id = other_doc.id
    finally:
        other_db.close()

    r = client.get(f"/documents/{other_doc_id}/clauses")
    assert r.status_code == 404


# ── AC: non-existent doc → 404 ───────────────────────────────────────────────

def test_nonexistent_doc_returns_404(client, tenant_id):
    """Non-existent doc_id → 404."""
    r = client.get("/documents/99999/clauses")
    assert r.status_code == 404


# ── AC: clause fields present ─────────────────────────────────────────────────

def test_clause_fields_all_present(client, tdb, tenant_id):
    """ClauseOut includes clause_num, title, content, page_num."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(
        tdb, tenant_id, doc.id,
        clause_num="Điều 5",
        title="Thanh toán",
        content="Bên A thanh toán trong 30 ngày.",
        page_num=4,
    )
    tdb.commit()

    r = client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200
    c = r.json()["clauses"][0]
    assert c["clause_num"] == "Điều 5"
    assert c["title"] == "Thanh toán"
    assert c["content"] == "Bên A thanh toán trong 30 ngày."
    assert c["page_num"] == 4


def test_clause_optional_fields_null(client, tdb, tenant_id):
    """clause_num and title may be null (Claude-fallback clauses)."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, clause_num=None, title=None, content="Toàn bộ hợp đồng.", page_num=None)
    tdb.commit()

    r = client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200
    c = r.json()["clauses"][0]
    assert c["clause_num"] is None
    assert c["title"] is None
    assert c["page_num"] is None
    assert c["content"] == "Toàn bộ hợp đồng."

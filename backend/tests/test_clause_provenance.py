"""Tests for clause provenance + clause-scoped re-derive (#303, DEC-048 §13).

Covers:
  - AC1: derive_obligations() populates source_clause_num from winning Term's ref
  - AC2: re-derive-clause endpoint changes only obligations for that clause
  - AC3: user_manual / done / fulfilled_at obligations protected from re-derive
  - AC4: derived_from distinguishes "original" vs "user_edit"
  - endpoint: 404 on missing clause_num
  - endpoint: no_clauses / no doc_type_group → skips remap, still re-derives from Terms
"""
import json
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

import main as _main_mod
from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import TenantUser, Tenant
from app.models.tenant import Clause, Document, Event, Obligation, Term
from app.core.security import get_password_hash
from app.db.database import init_master_db, init_tenant_db, _engine_cache, _cache_lock, TENANTS_DIR
from app.services.consent import record_consent
from app.services.obligation_engine import derive_obligation_from_clause, derive_obligations


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
    tid = f"clause-{uuid.uuid4().hex[:8]}"
    init_master_db()
    init_tenant_db(tid)

    mdb = MasterSessionLocal()
    try:
        mdb.add(Tenant(id=tid, name=f"Clause Test {tid}", db_path=f"tenants/{tid}.db"))
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
    return c


@pytest.fixture
def tdb(tenant_id):
    s = get_tenant_session(tenant_id)
    try:
        yield s
    finally:
        s.close()


def _make_doc(db, tid, confirmed=True):
    doc = Document(
        tenant_id=tid,
        file_name="contract.pdf",
        file_path=f"{tid}/contract.pdf",
        status="done",
        confirmed_by_user_at=datetime.utcnow() if confirmed else None,
    )
    db.add(doc)
    db.flush()
    return doc


def _make_term(db, tid, doc_id, field_name, value, ref=None):
    t = Term(
        tenant_id=tid,
        document_id=doc_id,
        field_name=field_name,
        field_value=value,
        ref=ref,
        is_superseded=False,
    )
    db.add(t)
    db.flush()
    return t


def _make_clause(db, tid, doc_id, clause_num, content="điều khoản nội dung"):
    c = Clause(
        tenant_id=tid,
        document_id=doc_id,
        clause_num=clause_num,
        title=f"Tiêu đề {clause_num}",
        content=content,
    )
    db.add(c)
    db.flush()
    return c


def _make_obligation(db, tid, doc_id, source_clause_num=None, source="ai_extracted",
                     status="pending", fulfilled_at=None):
    ob = Obligation(
        tenant_id=tid,
        document_id=doc_id,
        description="test obligation",
        due_date="2026-12-01",
        status=status,
        source=source,
        source_clause_num=source_clause_num,
        derived_from="original",
        fulfilled_at=fulfilled_at,
    )
    db.add(ob)
    db.flush()
    return ob


# ── AC1: source_clause_num populated by derive_obligations ────────────────────

def test_derive_obligations_sets_source_clause_num(tdb, tenant_id):
    """derive_obligations() captures winning term's ref → source_clause_num."""
    doc = _make_doc(tdb, tenant_id)
    _make_term(tdb, tenant_id, doc.id, "ngay_het_han", "2026-12-31", ref="Điều 8")
    tdb.commit()

    result = derive_obligations(tdb, tenant_id, doc.id)
    assert result["created"] == 1

    tdb.expire_all()
    ob = tdb.query(Obligation).filter(Obligation.document_id == doc.id).first()
    assert ob is not None
    assert ob.source_clause_num == "Điều 8"
    assert ob.derived_from == "original"


def test_derive_obligations_source_clause_num_none_when_no_ref(tdb, tenant_id):
    """If winning term has no ref, source_clause_num is NULL (graceful degrade)."""
    doc = _make_doc(tdb, tenant_id)
    _make_term(tdb, tenant_id, doc.id, "ngay_het_han", "2026-12-31", ref=None)
    tdb.commit()

    derive_obligations(tdb, tenant_id, doc.id)
    tdb.expire_all()
    ob = tdb.query(Obligation).filter(Obligation.document_id == doc.id).first()
    assert ob.source_clause_num is None
    assert ob.derived_from == "original"


def test_derive_obligations_start_field_ref_fallback(tdb, tenant_id):
    """If no ngay_het_han ref, use ngay_hieu_luc's ref for source_clause_num."""
    doc = _make_doc(tdb, tenant_id)
    _make_term(tdb, tenant_id, doc.id, "ngay_hieu_luc", "2026-01-01", ref="Điều 3")
    _make_term(tdb, tenant_id, doc.id, "thoi_han_hd", "12", ref="Điều 3")
    tdb.commit()

    result = derive_obligations(tdb, tenant_id, doc.id)
    assert result["created"] == 1

    tdb.expire_all()
    ob = tdb.query(Obligation).filter(Obligation.document_id == doc.id).first()
    assert ob.source_clause_num == "Điều 3"


# ── AC4: derived_from distinguishes original vs user_edit ────────────────────

def test_derived_from_original_on_ai_derivation(tdb, tenant_id):
    """AI-derived obligations get derived_from='original'."""
    doc = _make_doc(tdb, tenant_id)
    _make_term(tdb, tenant_id, doc.id, "ngay_het_han", "2026-06-30", ref="Điều 2")
    tdb.commit()

    derive_obligations(tdb, tenant_id, doc.id)
    tdb.expire_all()
    ob = tdb.query(Obligation).filter(Obligation.document_id == doc.id).first()
    assert ob.derived_from == "original"


# ── derive_obligation_from_clause unit tests ──────────────────────────────────

def test_derive_obligation_from_clause_creates_with_provenance(tdb, tenant_id):
    """derive_obligation_from_clause creates obligation tagged to clause."""
    doc = _make_doc(tdb, tenant_id)
    _make_term(tdb, tenant_id, doc.id, "ngay_het_han", "2026-09-30", ref="Điều 5")
    _make_term(tdb, tenant_id, doc.id, "ngay_het_han", "2027-01-01", ref="Điều 9")  # other clause
    tdb.commit()

    result = derive_obligation_from_clause(tdb, tenant_id, doc.id, "Điều 5")
    assert result["created"] == 1
    assert not result["skipped"]

    tdb.expire_all()
    ob = tdb.query(Obligation).filter(
        Obligation.document_id == doc.id,
        Obligation.source_clause_num == "Điều 5",
    ).first()
    assert ob is not None
    assert ob.due_date == "2026-09-30"
    assert ob.derived_from == "original"


def test_derive_obligation_from_clause_skips_without_date_terms(tdb, tenant_id):
    """Clause with no date Terms → skipped, no obligation created."""
    doc = _make_doc(tdb, tenant_id)
    _make_term(tdb, tenant_id, doc.id, "so_hop_dong", "HĐ-001", ref="Điều 1")
    tdb.commit()

    result = derive_obligation_from_clause(tdb, tenant_id, doc.id, "Điều 1")
    assert result["created"] == 0
    assert result["skipped"]


def test_derive_obligation_from_clause_ignores_other_clause_terms(tdb, tenant_id):
    """Only Terms with ref == clause_num are used — other clauses not touched."""
    doc = _make_doc(tdb, tenant_id)
    _make_term(tdb, tenant_id, doc.id, "ngay_het_han", "2026-12-31", ref="Điều 9")
    tdb.commit()

    # Re-derive for "Điều 5" which has no terms → skipped.
    result = derive_obligation_from_clause(tdb, tenant_id, doc.id, "Điều 5")
    assert result["created"] == 0
    assert result["skipped"]


# ── AC2: endpoint changes only obligations for the given clause ───────────────

def test_re_derive_clause_404_on_missing_clause(client, tdb, tenant_id):
    """POST re-derive-clause with non-existent clause_num → 404."""
    doc = _make_doc(tdb, tenant_id)
    tdb.commit()

    r = client.post(f"/documents/{doc.id}/re-derive-clause", json={"clause_num": "Điều 99"})
    assert r.status_code == 404
    assert "Điều 99" in r.json()["detail"]


def test_re_derive_clause_404_on_missing_doc(client, tdb, tenant_id):
    """POST re-derive-clause for non-existent doc → 404."""
    r = client.post("/documents/99999/re-derive-clause", json={"clause_num": "Điều 1"})
    assert r.status_code == 404


def test_re_derive_clause_no_churn_other_clauses(client, tdb, tenant_id):
    """Re-derive clause A → clause B obligation is untouched (AC2)."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, "Điều 1", "hết hạn 2026-12-31")
    _make_clause(tdb, tenant_id, doc.id, "Điều 2", "thanh toán 2026-06-01")
    ob_a = _make_obligation(tdb, tenant_id, doc.id, source_clause_num="Điều 1")
    ob_b = _make_obligation(tdb, tenant_id, doc.id, source_clause_num="Điều 2")
    tdb.commit()

    # Re-derive clause 1 only — clause 2 obligation must survive.
    r = client.post(f"/documents/{doc.id}/re-derive-clause", json={"clause_num": "Điều 1"})
    assert r.status_code == 200
    body = r.json()
    assert body["deleted"] == 1   # ob_a deleted
    assert body["protected_manual"] == 0

    tdb.expire_all()
    # ob_b still alive.
    assert tdb.query(Obligation).filter(Obligation.id == ob_b.id).first() is not None


# ── AC3: protected obligations survive re-derive ──────────────────────────────

def test_re_derive_clause_protects_user_manual(client, tdb, tenant_id):
    """source=user_manual obligation is preserved, not deleted (AC3)."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, "Điều 3")
    ob = _make_obligation(tdb, tenant_id, doc.id, source_clause_num="Điều 3",
                          source="user_manual")
    tdb.commit()

    r = client.post(f"/documents/{doc.id}/re-derive-clause", json={"clause_num": "Điều 3"})
    assert r.status_code == 200
    body = r.json()
    assert body["protected_manual"] == 1
    assert body["deleted"] == 0

    tdb.expire_all()
    assert tdb.query(Obligation).filter(Obligation.id == ob.id).first() is not None


def test_re_derive_clause_protects_done_obligation(client, tdb, tenant_id):
    """status=done obligation is preserved (AC3)."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, "Điều 4")
    ob = _make_obligation(tdb, tenant_id, doc.id, source_clause_num="Điều 4",
                          source="ai_extracted", status="done")
    tdb.commit()

    r = client.post(f"/documents/{doc.id}/re-derive-clause", json={"clause_num": "Điều 4"})
    assert r.status_code == 200
    assert r.json()["protected_manual"] == 1

    tdb.expire_all()
    assert tdb.query(Obligation).filter(Obligation.id == ob.id).first() is not None


def test_re_derive_clause_protects_fulfilled_obligation(client, tdb, tenant_id):
    """fulfilled_at IS NOT NULL obligation is protected from re-derive (AC3)."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, "Điều 5")
    ob = _make_obligation(tdb, tenant_id, doc.id, source_clause_num="Điều 5",
                          fulfilled_at=datetime(2026, 3, 1))
    tdb.commit()

    r = client.post(f"/documents/{doc.id}/re-derive-clause", json={"clause_num": "Điều 5"})
    assert r.status_code == 200
    assert r.json()["protected_manual"] == 1

    tdb.expire_all()
    assert tdb.query(Obligation).filter(Obligation.id == ob.id).first() is not None


# ── AC4: derived_from="user_edit" via endpoint ──────────────────────────────

def test_re_derive_clause_sets_derived_from_user_edit(client, tdb, tenant_id):
    """Re-derive via endpoint → obligation.derived_from='user_edit' (AC4)."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, "Điều 7", "hết hạn 2027-06-30")
    _make_term(tdb, tenant_id, doc.id, "ngay_het_han", "2027-06-30", ref="Điều 7")
    tdb.commit()

    r = client.post(f"/documents/{doc.id}/re-derive-clause", json={"clause_num": "Điều 7"})
    assert r.status_code == 200

    tdb.expire_all()
    ob = tdb.query(Obligation).filter(
        Obligation.document_id == doc.id,
        Obligation.source_clause_num == "Điều 7",
    ).first()
    assert ob is not None
    assert ob.derived_from == "user_edit"


# ── audit event logged ────────────────────────────────────────────────────────

def test_re_derive_clause_logs_event(client, tdb, tenant_id):
    """Re-derive clause → clause_re_derived Event logged in DB."""
    doc = _make_doc(tdb, tenant_id)
    _make_clause(tdb, tenant_id, doc.id, "Điều 6")
    tdb.commit()

    client.post(f"/documents/{doc.id}/re-derive-clause", json={"clause_num": "Điều 6"})

    tdb.expire_all()
    ev = (
        tdb.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.entity_type == "document",
            Event.entity_id == doc.id,
            Event.event_type == "clause_re_derived",
        )
        .first()
    )
    assert ev is not None
    payload = json.loads(ev.payload)
    assert payload["clause_num"] == "Điều 6"

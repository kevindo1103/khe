"""Tests for cascade-past obligation → awaiting_confirmation (#313, DEC-048 Option B).

Covers:
  - AC: propagate_obligation_done with past anchor → child gets awaiting_confirmation
  - AC: propagate_obligation_done with future anchor → child stays pending (normal path)
  - AC: awaiting_confirmation child excluded from _flip_overdue_status (0 false-overdue)
  - AC: awaiting_confirmation child excluded from compute_due_window (0 reminder)
  - backfill scenario: 3 past parents done → all children awaiting_confirmation, no spam
  - same-day edge: anchor+delay == today → pending (not past)
  - operator confirm: PATCH awaiting_confirmation → pending (transition allowed)
"""
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import main as _main_mod
from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import TenantUser, Tenant
from app.models.tenant import Document, Obligation
from app.core.security import get_password_hash
from app.db.database import init_master_db, init_tenant_db, _engine_cache, _cache_lock, TENANTS_DIR
from app.services.consent import record_consent
from app.services.obligation_chain import propagate_obligation_done
from app.services.reminders import _flip_overdue_status, compute_due_window


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
    tid = f"cascade-{uuid.uuid4().hex[:8]}"
    init_master_db()
    init_tenant_db(tid)

    mdb = MasterSessionLocal()
    try:
        mdb.add(Tenant(id=tid, name=f"Cascade Test {tid}", db_path=f"tenants/{tid}.db"))
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


def _make_parent(db, tid, doc_id):
    ob = Obligation(
        tenant_id=tid,
        document_id=doc_id,
        description="parent milestone",
        due_date="2020-01-01",
        status="pending",
    )
    db.add(ob)
    db.flush()
    return ob


def _make_child(db, tid, doc_id, parent_id, delay_days=30):
    ob = Obligation(
        tenant_id=tid,
        document_id=doc_id,
        description="child milestone",
        due_date=None,
        status="waiting_trigger",
        trigger_obligation_id=parent_id,
        trigger_delay_days=delay_days,
        milestone_trigger="event",
    )
    db.add(ob)
    db.flush()
    return ob


# ── AC: cascade-past → awaiting_confirmation ─────────────────────────────────

def test_propagate_past_anchor_sets_awaiting_confirmation(tdb, tenant_id):
    """Child with due_date in past gets awaiting_confirmation (Option B)."""
    doc = _make_doc(tdb, tenant_id)
    parent = _make_parent(tdb, tenant_id, doc.id)
    child = _make_child(tdb, tenant_id, doc.id, parent.id, delay_days=10)
    tdb.commit()

    # Backfill: parent done 2 years ago → child due 2 years ago + 10 days = still past.
    past_anchor = datetime(2024, 1, 1)
    count = propagate_obligation_done(parent.id, tdb, fulfilled_at=past_anchor)
    assert count == 1
    tdb.commit()

    tdb.expire_all()
    child_row = tdb.query(Obligation).filter(Obligation.id == child.id).first()
    assert child_row.status == "awaiting_confirmation"
    assert child_row.due_date == "2024-01-11"    # anchor + 10 days — exact date preserved
    assert child_row.milestone_trigger == "date"


def test_propagate_future_anchor_sets_pending(tdb, tenant_id):
    """Child with due_date in the future gets pending (normal path unchanged)."""
    doc = _make_doc(tdb, tenant_id)
    parent = _make_parent(tdb, tenant_id, doc.id)
    child = _make_child(tdb, tenant_id, doc.id, parent.id, delay_days=60)
    tdb.commit()

    # Parent done today → child due 60 days from now = future.
    future_anchor = datetime.utcnow()
    propagate_obligation_done(parent.id, tdb, fulfilled_at=future_anchor)
    tdb.commit()

    tdb.expire_all()
    child_row = tdb.query(Obligation).filter(Obligation.id == child.id).first()
    assert child_row.status == "pending"


def test_propagate_no_delay_past_anchor_sets_awaiting_confirmation(tdb, tenant_id):
    """Child with no trigger_delay_days and past anchor → awaiting_confirmation."""
    doc = _make_doc(tdb, tenant_id)
    parent = _make_parent(tdb, tenant_id, doc.id)
    child = _make_child(tdb, tenant_id, doc.id, parent.id, delay_days=None)
    tdb.commit()

    past_anchor = datetime(2023, 6, 1)
    propagate_obligation_done(parent.id, tdb, fulfilled_at=past_anchor)
    tdb.commit()

    tdb.expire_all()
    child_row = tdb.query(Obligation).filter(Obligation.id == child.id).first()
    assert child_row.status == "awaiting_confirmation"
    assert child_row.due_date == "2023-06-01"


def test_propagate_today_anchor_sets_pending(tdb, tenant_id):
    """Child due exactly today → pending (today is NOT in the past)."""
    doc = _make_doc(tdb, tenant_id)
    parent = _make_parent(tdb, tenant_id, doc.id)
    # delay_days=0 → due = anchor = today
    child = _make_child(tdb, tenant_id, doc.id, parent.id, delay_days=0)
    tdb.commit()

    today_anchor = datetime.combine(date.today(), datetime.min.time())
    propagate_obligation_done(parent.id, tdb, fulfilled_at=today_anchor)
    tdb.commit()

    tdb.expire_all()
    child_row = tdb.query(Obligation).filter(Obligation.id == child.id).first()
    assert child_row.status == "pending"


# ── AC: 0 false-overdue from _flip_overdue_status ────────────────────────────

def test_awaiting_confirmation_not_flipped_to_overdue(tdb, tenant_id):
    """awaiting_confirmation child with past due_date → not flipped to overdue."""
    doc = _make_doc(tdb, tenant_id, confirmed=True)
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=doc.id,
        description="cascade past child",
        due_date="2020-01-01",
        status="awaiting_confirmation",
    )
    tdb.add(ob)
    tdb.commit()

    flipped = _flip_overdue_status(tdb, tenant_id, reference_date=date(2026, 1, 1))
    assert flipped == 0

    tdb.expire_all()
    assert tdb.query(Obligation).filter(Obligation.id == ob.id).first().status == "awaiting_confirmation"


# ── AC: 0 reminder from compute_due_window ───────────────────────────────────

def test_awaiting_confirmation_excluded_from_reminder_window(tdb, tenant_id):
    """awaiting_confirmation obligation not surfaced in compute_due_window."""
    doc = _make_doc(tdb, tenant_id, confirmed=True)
    today_str = date.today().isoformat()
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=doc.id,
        description="cascade past — might remind",
        due_date=today_str,
        status="awaiting_confirmation",
        remind_before_days=30,
    )
    tdb.add(ob)
    tdb.commit()

    due_obs = compute_due_window(tdb, tenant_id)
    assert ob.id not in [o.id for o in due_obs]


# ── backfill scenario ─────────────────────────────────────────────────────────

def test_backfill_cascade_past_children_no_false_overdue(tdb, tenant_id):
    """3 past parents done → 3 cascade-past children → 0 overdue flipped."""
    doc = _make_doc(tdb, tenant_id, confirmed=True)

    for i in range(3):
        parent = _make_parent(tdb, tenant_id, doc.id)
        child = _make_child(tdb, tenant_id, doc.id, parent.id, delay_days=30)
        tdb.commit()

        past_anchor = datetime(2022 + i, 1, 1)
        # Mirror real router flow: mark parent done BEFORE propagating.
        parent.status = "done"
        parent.fulfilled_at = past_anchor
        propagate_obligation_done(parent.id, tdb, fulfilled_at=past_anchor)
        tdb.commit()

    tdb.expire_all()
    children = (
        tdb.query(Obligation)
        .filter(
            Obligation.tenant_id == tenant_id,
            Obligation.trigger_obligation_id.isnot(None),  # cascade children only
        )
        .all()
    )
    assert len(children) == 3
    assert all(c.status == "awaiting_confirmation" for c in children)

    flipped = _flip_overdue_status(tdb, tenant_id, reference_date=date(2026, 6, 1))
    assert flipped == 0


# ── operator confirm: PATCH awaiting_confirmation → pending ───────────────────

def test_patch_awaiting_confirmation_to_pending(client, tdb, tenant_id):
    """Operator can advance awaiting_confirmation → pending (D-02 confirm flow)."""
    doc = _make_doc(tdb, tenant_id)
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=doc.id,
        description="needs SME confirm",
        due_date="2024-01-01",
        status="awaiting_confirmation",
    )
    tdb.add(ob)
    tdb.commit()

    r = client.patch(f"/obligations/{ob.id}", json={"status": "pending"})
    assert r.status_code == 200
    assert r.json()["obligation"]["status"] == "pending"


def test_patch_awaiting_confirmation_to_done(client, tdb, tenant_id):
    """Operator can mark awaiting_confirmation → done (confirmed it happened)."""
    doc = _make_doc(tdb, tenant_id)
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=doc.id,
        description="needs SME confirm",
        due_date="2024-01-01",
        status="awaiting_confirmation",
    )
    tdb.add(ob)
    tdb.commit()

    r = client.patch(f"/obligations/{ob.id}", json={
        "status": "done",
        "fulfilled_at": "2024-01-05T00:00:00",
    })
    assert r.status_code == 200
    body = r.json()["obligation"]
    assert body["status"] == "done"
    assert body["fulfilled_at"] is not None

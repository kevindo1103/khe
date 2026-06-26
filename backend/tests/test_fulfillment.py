"""Tests for fulfillment capture + chain resolver fix (#302, DEC-048 G1/G2/P2/P3/P5).

Covers:
  - G2: mark-done persists fulfilled_at + fulfilled_by + evidence_doc_ids, Event logged
  - G2: mark-done without fulfilled_at → 400
  - G1: chain resolver anchors child due-date on fulfilled_at (NOT today)
  - P2: is_evidence doc upload → status="done", no extraction event
  - P3: actor attribution — fulfilled_by defaults to username
  - P5: overdue flip excluded for fulfilled_at-set obligations
  - P5: reminder suppressed for fulfilled_at-set obligations
  - backfill: 5 historical obligations → 0 false-overdue when fulfilled_at is set
"""
import io
import json
import uuid
from datetime import datetime, date, timedelta

import pytest
from fastapi.testclient import TestClient

import main as _main_mod
from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import TenantUser, Tenant
from app.models.tenant import Document, Event, Obligation
from app.core.security import get_password_hash
from app.db.database import init_master_db, init_tenant_db, _engine_cache, _cache_lock, TENANTS_DIR
from app.services.consent import record_consent
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
    tid = f"fulfil-{uuid.uuid4().hex[:8]}"
    init_master_db()
    init_tenant_db(tid)

    mdb = MasterSessionLocal()
    try:
        mdb.add(Tenant(id=tid, name=f"Fulfil Test {tid}", db_path=f"tenants/{tid}.db"))
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


def _make_doc(db, tid, file_name="contract.pdf", status="done", confirmed=True):
    doc = Document(
        tenant_id=tid,
        file_name=file_name,
        file_path=f"{tid}/{file_name}",
        status=status,
        confirmed_by_user_at=datetime.utcnow() if confirmed else None,
    )
    db.add(doc)
    db.flush()
    return doc


def _make_obligation(db, tid, doc_id, description="pay rent", due_date="2025-06-01",
                     status="pending", direction=None, trigger_obligation_id=None,
                     trigger_delay_days=None):
    ob = Obligation(
        tenant_id=tid,
        document_id=doc_id,
        description=description,
        due_date=due_date,
        status=status,
        direction=direction,
        trigger_obligation_id=trigger_obligation_id,
        trigger_delay_days=trigger_delay_days,
        milestone_trigger="event" if trigger_obligation_id else "date",
    )
    db.add(ob)
    db.flush()
    return ob


# ── G2 tests ──────────────────────────────────────────────────────────────────

def test_mark_done_persists_fulfillment_fields(client, tdb, tenant_id):
    """PATCH status=done with fulfilled_at → persists date, actor, evidence."""
    doc = _make_doc(tdb, tenant_id)
    ob = _make_obligation(tdb, tenant_id, doc.id)
    tdb.commit()

    ev_doc = _make_doc(tdb, tenant_id, file_name="bien_ban.pdf")
    tdb.commit()

    r = client.patch(f"/obligations/{ob.id}", json={
        "status": "done",
        "fulfilled_at": "2025-05-20T10:00:00",
        "fulfilled_by": "tuser",
        "evidence_doc_ids": [ev_doc.id],
    })
    assert r.status_code == 200, r.text
    body = r.json()["obligation"]
    assert body["status"] == "done"
    assert body["fulfilled_at"] is not None
    assert body["fulfilled_by"] == "tuser"
    assert body["evidence_doc_ids"] == [ev_doc.id]


def test_mark_done_without_fulfilled_at_returns_400(client, tdb, tenant_id):
    """PATCH status=done without fulfilled_at → 400 Bad Request (G2 validation)."""
    doc = _make_doc(tdb, tenant_id)
    ob = _make_obligation(tdb, tenant_id, doc.id)
    tdb.commit()

    r = client.patch(f"/obligations/{ob.id}", json={"status": "done"})
    assert r.status_code == 400
    assert "fulfilled_at" in r.json()["detail"]


def test_mark_done_logs_event_with_fulfillment_payload(client, tdb, tenant_id):
    """PATCH status=done → Event payload includes fulfilled_at + fulfilled_by."""
    doc = _make_doc(tdb, tenant_id)
    ob = _make_obligation(tdb, tenant_id, doc.id)
    tdb.commit()

    client.patch(f"/obligations/{ob.id}", json={
        "status": "done",
        "fulfilled_at": "2025-05-20T10:00:00",
    })

    tdb.expire_all()
    ev = (
        tdb.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.entity_type == "obligation",
            Event.entity_id == ob.id,
            Event.event_type == "updated",
        )
        .first()
    )
    assert ev is not None
    payload = json.loads(ev.payload)
    assert payload["new_status"] == "done"
    assert payload["fulfilled_at"] is not None


def test_mark_done_logs_evidence_attached_event(client, tdb, tenant_id):
    """evidence_doc_ids → evidence_attached Event per doc with purpose=obligation_fulfillment."""
    doc = _make_doc(tdb, tenant_id)
    ob = _make_obligation(tdb, tenant_id, doc.id)
    ev_doc = _make_doc(tdb, tenant_id, file_name="evidence.pdf")
    tdb.commit()

    client.patch(f"/obligations/{ob.id}", json={
        "status": "done",
        "fulfilled_at": "2025-05-20T10:00:00",
        "evidence_doc_ids": [ev_doc.id],
    })

    tdb.expire_all()
    ev = (
        tdb.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.entity_type == "obligation",
            Event.entity_id == ob.id,
            Event.event_type == "evidence_attached",
        )
        .first()
    )
    assert ev is not None
    assert ev.purpose == "obligation_fulfillment"
    payload = json.loads(ev.payload)
    assert payload["evidence_doc_id"] == ev_doc.id


def test_mark_done_fulfilled_by_defaults_to_username(client, tdb, tenant_id):
    """fulfilled_by defaults to current username when not provided (P3)."""
    doc = _make_doc(tdb, tenant_id)
    ob = _make_obligation(tdb, tenant_id, doc.id)
    tdb.commit()

    r = client.patch(f"/obligations/{ob.id}", json={
        "status": "done",
        "fulfilled_at": "2025-05-20T10:00:00",
        # fulfilled_by omitted
    })
    assert r.status_code == 200
    assert r.json()["obligation"]["fulfilled_by"] == "tuser"


# ── G1 tests ──────────────────────────────────────────────────────────────────

def test_chain_resolver_uses_fulfilled_at_not_today(client, tdb, tenant_id):
    """Chain propagation: child due = fulfilled_at + delay, NOT today + delay (G1)."""
    doc = _make_doc(tdb, tenant_id)
    parent = _make_obligation(tdb, tenant_id, doc.id, description="handover")
    child = _make_obligation(
        tdb, tenant_id, doc.id,
        description="warranty",
        due_date=None,
        status="waiting_trigger",
        trigger_obligation_id=parent.id,
        trigger_delay_days=30,
    )
    tdb.commit()

    fulfilled_date = "2025-04-01T00:00:00"
    r = client.patch(f"/obligations/{parent.id}", json={
        "status": "done",
        "fulfilled_at": fulfilled_date,
    })
    assert r.status_code == 200
    assert r.json()["activated_count"] == 1

    tdb.expire_all()
    child_refreshed = tdb.query(Obligation).filter(Obligation.id == child.id).first()
    assert child_refreshed.status == "pending"
    # 2025-04-01 + 30 days = 2025-05-01
    assert child_refreshed.due_date == "2025-05-01"


# ── P2 tests ──────────────────────────────────────────────────────────────────

_PDF_MAGIC = b"%PDF-1.4\n%%EOF\n"


def test_evidence_doc_upload_skips_extraction(client, tenant_id, tdb):
    """Upload with is_evidence=true → status=done, no extraction_performed Event."""
    r = client.post(
        "/ingest/upload?is_evidence=true",
        files={"file": ("bien_ban.pdf", io.BytesIO(_PDF_MAGIC), "application/pdf")},
    )
    assert r.status_code == 201, r.text
    doc_id = r.json()["doc_id"]
    assert r.json()["status"] == "done"

    tdb.expire_all()
    doc = tdb.query(Document).filter(Document.id == doc_id).first()
    assert doc.is_evidence is True
    assert doc.contains_personal_data is True
    assert doc.status == "done"

    ev = (
        tdb.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.entity_id == doc_id,
            Event.event_type == "extraction_performed",
        )
        .first()
    )
    assert ev is None, "extraction_performed event must not be logged for evidence docs"


# ── P5 tests ──────────────────────────────────────────────────────────────────

def test_overdue_flip_excludes_fulfilled_obligations(tdb, tenant_id):
    """_flip_overdue_status skips obligations where fulfilled_at IS NOT NULL (P5)."""
    doc = _make_doc(tdb, tenant_id, confirmed=True)
    # Past due, pending, but fulfilled_at set → must NOT flip to overdue.
    ob_fulfilled = Obligation(
        tenant_id=tenant_id,
        document_id=doc.id,
        description="paid already",
        due_date="2024-01-01",
        status="pending",
        fulfilled_at=datetime(2024, 1, 1),
    )
    # Past due, pending, no fulfilled_at → MUST flip to overdue.
    ob_unfulfilled = Obligation(
        tenant_id=tenant_id,
        document_id=doc.id,
        description="not paid",
        due_date="2024-01-01",
        status="pending",
    )
    tdb.add_all([ob_fulfilled, ob_unfulfilled])
    tdb.commit()

    flipped = _flip_overdue_status(tdb, tenant_id, reference_date=date(2025, 6, 1))
    assert flipped == 1  # only the unfulfilled one

    tdb.expire_all()
    assert tdb.query(Obligation).filter(Obligation.id == ob_fulfilled.id).first().status == "pending"
    assert tdb.query(Obligation).filter(Obligation.id == ob_unfulfilled.id).first().status == "overdue"


def test_reminder_window_excludes_fulfilled_obligations(tdb, tenant_id):
    """compute_due_window excludes obligations where fulfilled_at IS NOT NULL (P5)."""
    doc = _make_doc(tdb, tenant_id, confirmed=True)
    today_str = date.today().isoformat()
    # Within reminder window, but already fulfilled → should be suppressed.
    ob_fulfilled = Obligation(
        tenant_id=tenant_id,
        document_id=doc.id,
        description="pay next week",
        due_date=today_str,
        status="pending",
        remind_before_days=30,
        fulfilled_at=datetime.utcnow(),
    )
    # Within reminder window, not fulfilled → should appear.
    ob_due = Obligation(
        tenant_id=tenant_id,
        document_id=doc.id,
        description="renew contract",
        due_date=today_str,
        status="pending",
        remind_before_days=30,
    )
    tdb.add_all([ob_fulfilled, ob_due])
    tdb.commit()

    due_obs = compute_due_window(tdb, tenant_id)
    ids = [ob.id for ob in due_obs]
    assert ob_fulfilled.id not in ids
    assert ob_due.id in ids


# ── F1 review fix: status revert clears fulfillment ─────────────────────────

def test_status_revert_from_done_clears_fulfillment(client, tdb, tenant_id):
    """Reverting status from done→pending clears fulfilled_at/by/evidence (F1)."""
    doc = _make_doc(tdb, tenant_id)
    ob = _make_obligation(tdb, tenant_id, doc.id)
    ev_doc = _make_doc(tdb, tenant_id, file_name="evidence.pdf")
    tdb.commit()

    r = client.patch(f"/obligations/{ob.id}", json={
        "status": "done",
        "fulfilled_at": "2025-05-20T10:00:00",
        "fulfilled_by": "tuser",
        "evidence_doc_ids": [ev_doc.id],
    })
    assert r.status_code == 200
    assert r.json()["obligation"]["fulfilled_at"] is not None

    r2 = client.patch(f"/obligations/{ob.id}", json={"status": "pending"})
    assert r2.status_code == 200
    body = r2.json()["obligation"]
    assert body["fulfilled_at"] is None
    assert body["fulfilled_by"] is None
    assert body["evidence_doc_ids"] is None


# ── F2 review fix: invalid evidence_doc_ids rejected ────────────────────────

def test_invalid_evidence_doc_ids_returns_400(client, tdb, tenant_id):
    """evidence_doc_ids referencing non-existent docs → 400 (F2)."""
    doc = _make_doc(tdb, tenant_id)
    ob = _make_obligation(tdb, tenant_id, doc.id)
    tdb.commit()

    r = client.patch(f"/obligations/{ob.id}", json={
        "status": "done",
        "fulfilled_at": "2025-05-20T10:00:00",
        "evidence_doc_ids": [99999],
    })
    assert r.status_code == 400
    assert "99999" in r.json()["detail"]


def test_backfill_five_past_obligations_no_false_overdue(tdb, tenant_id):
    """Backfill 5 past obligations with fulfilled_at → 0 flipped to overdue (P5)."""
    doc = _make_doc(tdb, tenant_id, confirmed=True)
    for i in range(5):
        tdb.add(Obligation(
            tenant_id=tenant_id,
            document_id=doc.id,
            description=f"milestone {i}",
            due_date=f"202{i}-06-01",
            status="pending",
            fulfilled_at=datetime(2020 + i, 6, 1),
        ))
    tdb.commit()

    flipped = _flip_overdue_status(tdb, tenant_id, reference_date=date(2026, 1, 1))
    assert flipped == 0

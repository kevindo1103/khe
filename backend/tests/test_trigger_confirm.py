"""POST /obligations/{id}/confirm-trigger (#501).

AC:
- waiting_trigger + event_date → pending, due_date = event_date + trigger_delay_days
- event_date omitted → defaults to today
- status != waiting_trigger → 409
- wrong tenant → 404
- trigger_obligation_id set + prereq not done → 409
- trigger_obligation_id set + prereq done → confirm succeeds
- trigger_confirmed Event logged with event_date, due_date, confirmed_by
"""
import os
import sys
from datetime import date, timedelta

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Event, Obligation
from main import app

TENANT = "trigger-confirm-tenant"
OTHER_TENANT = "trigger-confirm-other"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    for tid in (TENANT, OTHER_TENANT):
        init_tenant_db(tid)
    db = MasterSessionLocal()
    for tid, name in ((TENANT, "TC Tenant"), (OTHER_TENANT, "TC Other")):
        if not db.query(Tenant).filter(Tenant.id == tid).first():
            db.add(Tenant(id=tid, name=name, db_path=f"tenants/{tid}.db"))
    db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "tcuser").first():
        db.add(TenantUser(tenant_id=TENANT, username="tcuser",
                          hashed_password=get_password_hash("tcpass"), role="staff"))
    db.commit()
    db.close()


@pytest.fixture
def client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "tcuser", "password": "tcpass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _make_ob(db, **kwargs):
    ob = Obligation(
        tenant_id=TENANT,
        document_id=1,
        description="Test obligation",
        obligation_type="payment",
        recurrence="once",
        status="waiting_trigger",
        **kwargs,
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


# ── Core transition ────────────────────────────────────────────────────────

def test_confirm_trigger_with_event_date(client, db):
    ob = _make_ob(db, trigger_delay_days=30)
    event_date = "2026-08-01"
    r = client.post(f"/obligations/{ob.id}/confirm-trigger",
                    json={"event_date": event_date})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "pending"
    assert data["due_date"] == "2026-08-31"   # 2026-08-01 + 30 days


def test_confirm_trigger_zero_delay(client, db):
    ob = _make_ob(db, trigger_delay_days=0)
    event_date = "2026-09-15"
    r = client.post(f"/obligations/{ob.id}/confirm-trigger",
                    json={"event_date": event_date})
    assert r.status_code == 200
    assert r.json()["due_date"] == event_date
    assert r.json()["status"] == "pending"


def test_confirm_trigger_null_delay_defaults_zero(client, db):
    ob = _make_ob(db, trigger_delay_days=None)
    event_date = "2026-07-10"
    r = client.post(f"/obligations/{ob.id}/confirm-trigger",
                    json={"event_date": event_date})
    assert r.status_code == 200
    assert r.json()["due_date"] == event_date


def test_confirm_trigger_defaults_event_date_to_today(client, db):
    ob = _make_ob(db, trigger_delay_days=5)
    r = client.post(f"/obligations/{ob.id}/confirm-trigger", json={})
    assert r.status_code == 200
    expected_due = (date.today() + timedelta(days=5)).isoformat()
    assert r.json()["due_date"] == expected_due
    assert r.json()["status"] == "pending"


# ── Error cases ────────────────────────────────────────────────────────────

def test_confirm_trigger_wrong_status_409(client, db):
    ob = _make_ob(db)
    ob.status = "pending"
    db.commit()
    r = client.post(f"/obligations/{ob.id}/confirm-trigger", json={})
    assert r.status_code == 409
    assert "waiting_trigger" in r.json()["detail"]


def test_confirm_trigger_done_status_409(client, db):
    ob = _make_ob(db)
    ob.status = "done"
    db.commit()
    r = client.post(f"/obligations/{ob.id}/confirm-trigger", json={})
    assert r.status_code == 409


def test_confirm_trigger_not_found_404(client):
    r = client.post("/obligations/999999/confirm-trigger", json={})
    assert r.status_code == 404


def test_confirm_trigger_other_tenant_isolation(client, db):
    # Per-tenant SQLite DBs have separate auto-increment so IDs can collide.
    # Isolation test: verify the other tenant's obligation is never mutated by
    # a request authenticated as the main tenant.
    other_db = get_tenant_session(OTHER_TENANT)
    try:
        other_ob = Obligation(tenant_id=OTHER_TENANT, document_id=1,
                              description="other tenant ob", obligation_type="payment",
                              recurrence="once", status="waiting_trigger",
                              trigger_delay_days=5)
        other_db.add(other_ob)
        other_db.commit()
        other_db.refresh(other_ob)
        other_id = other_ob.id
    finally:
        other_db.close()

    # Make the call as TENANT user
    client.post(f"/obligations/{other_id}/confirm-trigger",
                json={"event_date": "2026-07-01"})

    # Regardless of what happened in TENANT's DB, OTHER_TENANT's obligation
    # must remain untouched — its status should still be "waiting_trigger".
    other_db = get_tenant_session(OTHER_TENANT)
    try:
        still_waiting = other_db.query(Obligation).filter(
            Obligation.id == other_id,
            Obligation.tenant_id == OTHER_TENANT,
        ).first()
        assert still_waiting is not None
        assert still_waiting.status == "waiting_trigger"
    finally:
        other_db.close()


# ── Prerequisite guard ─────────────────────────────────────────────────────

def test_confirm_trigger_prereq_not_done_409(client, db):
    prereq = _make_ob(db, trigger_delay_days=None)
    prereq.status = "pending"
    db.commit()
    ob = _make_ob(db, trigger_delay_days=10, trigger_obligation_id=prereq.id)
    r = client.post(f"/obligations/{ob.id}/confirm-trigger", json={})
    assert r.status_code == 409
    assert "Prerequisite" in r.json()["detail"]


def test_confirm_trigger_prereq_done_succeeds(client, db):
    prereq = _make_ob(db, trigger_delay_days=None)
    prereq.status = "done"
    db.commit()
    ob = _make_ob(db, trigger_delay_days=7, trigger_obligation_id=prereq.id)
    r = client.post(f"/obligations/{ob.id}/confirm-trigger",
                    json={"event_date": "2026-10-01"})
    assert r.status_code == 200
    assert r.json()["status"] == "pending"
    assert r.json()["due_date"] == "2026-10-08"   # +7 days


# ── D-07 Event logging ─────────────────────────────────────────────────────

def test_confirm_trigger_logs_event(client, db):
    ob = _make_ob(db, trigger_delay_days=14)
    event_date = "2026-11-01"
    r = client.post(f"/obligations/{ob.id}/confirm-trigger",
                    json={"event_date": event_date})
    assert r.status_code == 200

    events = (
        db.query(Event)
        .filter(Event.entity_id == ob.id, Event.event_type == "trigger_confirmed")
        .all()
    )
    assert len(events) == 1
    import json
    payload = json.loads(events[0].payload)
    assert payload["event_date"] == event_date
    assert payload["due_date"] == "2026-11-15"   # +14 days
    assert payload["confirmed_by"] == "tcuser"

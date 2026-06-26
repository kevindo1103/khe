"""Obligation snooze — "Nhắc lại sau 3 ngày" (#214).

- POST /obligations/{id}/snooze sets snoozed_until = now + 3 days + reminder_snoozed Event.
- compute_due_window skips obligations snoozed into the future, resumes after.
- Snooze does NOT mutate status/due_date (D-07); tenant-scoped (D-10).
"""
import os
import sys
from datetime import date, datetime, timedelta

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Event, Obligation
from app.services.reminders import compute_due_window
from main import app

TENANT = "snooze-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Snooze Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "suser").first():
        db.add(TenantUser(tenant_id=TENANT, username="suser",
                          hashed_password=get_password_hash("spass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "suser", "password": "spass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _make_ob(db, due_offset_days=5, status="pending"):
    doc = Document(tenant_id=TENANT, file_name="s.pdf", file_path="x/y.pdf", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    ob = Obligation(
        tenant_id=TENANT, document_id=doc.id, description="Đợt thanh toán",
        recurrence="once", due_date=(date.today() + timedelta(days=due_offset_days)).isoformat(),
        status=status, remind_before_days=30,
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


def test_snooze_sets_until_and_event(auth_client, db):
    ob = _make_ob(db)
    r = auth_client.post(f"/obligations/{ob.id}/snooze")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    snoozed = datetime.fromisoformat(data["snoozed_until"])
    # ~3 days out (allow scheduling slack)
    assert timedelta(days=2, hours=23) < (snoozed - datetime.utcnow()) < timedelta(days=3, minutes=5)

    db.expire_all()
    refreshed = db.query(Obligation).filter(Obligation.id == ob.id).first()
    assert refreshed.snoozed_until is not None
    # D-07: status/due_date untouched
    assert refreshed.status == "pending"
    assert refreshed.due_date == ob.due_date

    ev = (
        db.query(Event)
        .filter(Event.tenant_id == TENANT, Event.event_type == "reminder_snoozed", Event.entity_id == ob.id)
        .first()
    )
    assert ev is not None
    assert str(ob.id) in (ev.payload or "")


def test_snooze_excludes_from_due_window(auth_client, db):
    ob = _make_ob(db, due_offset_days=5)  # within 30-day remind window
    # Before snooze: it IS a reminder candidate.
    assert any(o.id == ob.id for o in compute_due_window(db, TENANT))

    auth_client.post(f"/obligations/{ob.id}/snooze")
    db.expire_all()
    # After snooze: excluded.
    assert all(o.id != ob.id for o in compute_due_window(db, TENANT))


def test_expired_snooze_resumes(db):
    ob = _make_ob(db, due_offset_days=5)
    # Snooze already in the past → must resume (re-enter the window).
    ob.snoozed_until = datetime.utcnow() - timedelta(hours=1)
    db.commit()
    db.expire_all()
    assert any(o.id == ob.id for o in compute_due_window(db, TENANT))


def test_snooze_404_other_tenant(auth_client, db):
    r = auth_client.post("/obligations/99999/snooze")
    assert r.status_code == 404


def test_snooze_requires_auth():
    anon = TestClient(app)
    r = anon.post("/obligations/1/snooze")
    assert r.status_code in (401, 403)

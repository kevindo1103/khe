"""Document confirm → journey NEEDS_REVIEW → CONFIRMED (#238).

- POST /documents/{id}/confirm marks confirmed_by_user_at + writes Event (D-02/D-07).
- Self-party auto-derived from tenant legal_name Setting (no manual pick) → direction.
- Journey advances only when ALL extracted docs confirmed; FE sidebar unlocks.
"""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantProfile, TenantUser
from app.models.tenant import Document, Event, Obligation, Party
from main import app

TENANT = "confirm-tenant"
LEGAL = "Công ty ABC"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Confirm Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "cuser").first():
        db.add(TenantUser(tenant_id=TENANT, username="cuser",
                          hashed_password=get_password_hash("cpass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def master_db():
    d = MasterSessionLocal()
    try:
        yield d
    finally:
        d.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "cuser", "password": "cpass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _reset(master_db, db, stage="NEEDS_REVIEW", legal_name=LEGAL):
    db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
    db.query(Party).filter(Party.tenant_id == TENANT).delete()
    db.query(Document).filter(Document.tenant_id == TENANT).delete()
    db.query(Event).filter(Event.tenant_id == TENANT).delete()
    db.commit()
    t = master_db.query(Tenant).filter(Tenant.id == TENANT).first()
    t.journey_stage = stage
    t.is_first_session = True
    master_db.commit()
    prof = master_db.query(TenantProfile).filter(TenantProfile.tenant_id == TENANT).first()
    if prof:
        prof.legal_name = legal_name
    else:
        master_db.add(TenantProfile(tenant_id=TENANT, legal_name=legal_name))
    master_db.commit()


def _doc(db, status="extracted"):
    d = Document(tenant_id=TENANT, file_name="c.pdf", file_path="x/y.pdf", status=status)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _seed_parties_obligations(db, doc):
    db.add(Party(tenant_id=TENANT, document_id=doc.id, name=LEGAL, role_label="Bên A"))
    db.add(Party(tenant_id=TENANT, document_id=doc.id, name="Đối tác XYZ", role_label="Bên B"))
    db.add(Obligation(tenant_id=TENANT, document_id=doc.id, description="tôi trả",
                      recurrence="once", due_date="2026-12-31", status="pending", obligor="Bên A"))
    db.add(Obligation(tenant_id=TENANT, document_id=doc.id, description="họ giao",
                      recurrence="once", due_date="2026-11-30", status="pending", obligor="Bên B"))
    db.add(Obligation(tenant_id=TENANT, document_id=doc.id, description="vô danh",
                      recurrence="once", due_date="2026-10-01", status="pending", obligor=None))
    db.commit()


def _stage(master_db):
    master_db.expire_all()
    return master_db.query(Tenant).filter(Tenant.id == TENANT).first().journey_stage


def test_confirm_sets_timestamp_event_and_directions(auth_client, master_db, db):
    _reset(master_db, db)
    doc = _doc(db)
    _seed_parties_obligations(db, doc)

    r = auth_client.post(f"/documents/{doc.id}/confirm")
    assert r.status_code == 200
    data = r.json()
    assert data["doc_id"] == doc.id
    assert data["confirmed_at"] is not None
    assert data["directions_recomputed"] == 2   # obligor "Bên A" + "Bên B" set; None stays null

    db.expire_all()
    fresh = db.query(Document).filter(Document.id == doc.id).first()
    assert fresh.confirmed_by_user_at is not None

    # Auto-derived direction from legal_name (no manual pick).
    obs = {o.obligor: o.direction for o in db.query(Obligation).filter(Obligation.document_id == doc.id)}
    assert obs["Bên A"] == "nghĩa_vụ"     # self-party → my obligation
    assert obs["Bên B"] == "quyền_lợi"    # counterparty → their obligation
    assert obs[None] is None              # no obligor → null (D-13)

    ev = db.query(Event).filter(Event.event_type == "document_confirmed_by_user",
                                Event.entity_id == doc.id).first()
    assert ev is not None and ev.actor == "cuser"


def test_journey_advances_only_when_all_confirmed(auth_client, master_db, db):
    _reset(master_db, db, stage="NEEDS_REVIEW")
    d1, d2 = _doc(db), _doc(db)

    # Confirm first of two → still one unconfirmed → no advance.
    r1 = auth_client.post(f"/documents/{d1.id}/confirm").json()
    assert r1["journey_advanced"] is False
    assert r1["new_journey_stage"] == "NEEDS_REVIEW"
    assert _stage(master_db) == "NEEDS_REVIEW"

    # Confirm last → all confirmed → advance + clear is_first_session.
    r2 = auth_client.post(f"/documents/{d2.id}/confirm").json()
    assert r2["journey_advanced"] is True
    assert r2["new_journey_stage"] == "CONFIRMED"
    assert _stage(master_db) == "CONFIRMED"


def test_confirm_without_legal_name_keeps_direction_null(auth_client, master_db, db):
    _reset(master_db, db, stage="NEEDS_REVIEW", legal_name=None)
    doc = _doc(db)
    _seed_parties_obligations(db, doc)
    r = auth_client.post(f"/documents/{doc.id}/confirm").json()
    # No legal_name → can't auto-derive → all directions null (D-13). Still confirms + advances.
    assert r["journey_advanced"] is True
    db.expire_all()
    dirs = [o.direction for o in db.query(Obligation).filter(Obligation.document_id == doc.id)]
    assert all(d is None for d in dirs)


def test_confirm_404_other_tenant(auth_client, master_db, db):
    _reset(master_db, db)
    r = auth_client.post("/documents/99999/confirm")
    assert r.status_code == 404


def test_confirm_requires_auth():
    anon = TestClient(app)
    r = anon.post("/documents/1/confirm")
    assert r.status_code in (401, 403)

"""tenant_journey_stage state machine + endpoints + auto-transition hooks (#213).

NEW → EXTRACTING → NEEDS_REVIEW → CONFIRMED → ACTIVATED → STEADY (forward-only).
"""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.services import chat_query, tenant_journey
from main import app

TENANT = "journey-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Journey Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "juser").first():
        db.add(TenantUser(tenant_id=TENANT, username="juser",
                          hashed_password=get_password_hash("jpass"), role="staff"))
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
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "juser", "password": "jpass"})
    assert r.status_code == 200
    return c


def _set_stage(master_db, stage, first_session=True):
    t = master_db.query(Tenant).filter(Tenant.id == TENANT).first()
    t.journey_stage = stage
    t.is_first_session = first_session
    master_db.commit()


def _stage(master_db):
    master_db.expire_all()
    return master_db.query(Tenant).filter(Tenant.id == TENANT).first()


# ── service: monotonic forward-only ──────────────────────────────────────────
def test_advance_forward(master_db):
    _set_stage(master_db, "NEW")
    assert tenant_journey.advance_stage(master_db, TENANT, "EXTRACTING") == "EXTRACTING"
    assert _stage(master_db).journey_stage == "EXTRACTING"


def test_no_backward(master_db):
    _set_stage(master_db, "CONFIRMED")
    # backward target is a no-op, stage unchanged
    assert tenant_journey.advance_stage(master_db, TENANT, "EXTRACTING") == "CONFIRMED"
    assert _stage(master_db).journey_stage == "CONFIRMED"


def test_extracting_can_skip_to_confirmed(master_db):
    _set_stage(master_db, "EXTRACTING")
    assert tenant_journey.advance_stage(master_db, TENANT, "CONFIRMED") == "CONFIRMED"


def test_confirmed_clears_first_session(master_db):
    """DEC-040 (#259): is_first_session clears at CONFIRMED, not ACTIVATED."""
    _set_stage(master_db, "NEEDS_REVIEW", first_session=True)
    tenant_journey.advance_stage(master_db, TENANT, "CONFIRMED")
    t = _stage(master_db)
    assert t.journey_stage == "CONFIRMED"
    assert t.is_first_session is False  # cleared at CONFIRMED+


def test_activated_clears_first_session(master_db):
    _set_stage(master_db, "CONFIRMED", first_session=True)
    tenant_journey.advance_stage(master_db, TENANT, "ACTIVATED")
    t = _stage(master_db)
    assert t.journey_stage == "ACTIVATED"
    assert t.is_first_session is False  # cleared atomically


def test_self_heal_stuck_first_session(master_db):
    """#259: a tenant left at {CONFIRMED, is_first_session=True} (old threshold)
    self-heals on the next advance_stage call, even when it's a no-op."""
    _set_stage(master_db, "CONFIRMED", first_session=True)   # inconsistent state
    # No-op advance (already CONFIRMED) must still clear is_first_session.
    out = tenant_journey.advance_stage(master_db, TENANT, "CONFIRMED")
    assert out == "CONFIRMED"
    assert _stage(master_db).is_first_session is False


def test_invalid_stage_returns_none(master_db):
    _set_stage(master_db, "NEW")
    assert tenant_journey.advance_stage(master_db, TENANT, "BOGUS") is None
    assert _stage(master_db).journey_stage == "NEW"


def test_unknown_tenant_returns_none(master_db):
    assert tenant_journey.advance_stage(master_db, "does-not-exist", "EXTRACTING") is None


# ── service: require_current_at_least gating ─────────────────────────────────
def test_activated_gate_blocks_premature_jump(master_db):
    """A channel activated while still NEW must NOT skip to ACTIVATED."""
    _set_stage(master_db, "NEW")
    out = tenant_journey.advance_stage(master_db, TENANT, "ACTIVATED", require_current_at_least="CONFIRMED")
    assert out == "NEW"
    assert _stage(master_db).journey_stage == "NEW"
    assert _stage(master_db).is_first_session is True


def test_steady_gate_requires_activated(master_db):
    _set_stage(master_db, "CONFIRMED")
    out = tenant_journey.advance_stage(master_db, TENANT, "STEADY", require_current_at_least="ACTIVATED")
    assert out == "CONFIRMED"  # not activated yet → no promotion


# ── API: GET /tenants/me ─────────────────────────────────────────────────────
def test_get_tenant_me(auth_client, master_db):
    _set_stage(master_db, "NEW", first_session=True)
    r = auth_client.get("/tenants/me")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == TENANT
    assert data["journey_stage"] == "NEW"
    assert data["is_first_session"] is True


# ── API: PATCH /tenants/me/journey ───────────────────────────────────────────
def test_patch_journey_forward(auth_client, master_db):
    _set_stage(master_db, "NEW")
    r = auth_client.patch("/tenants/me/journey", json={"journey_stage": "EXTRACTING"})
    assert r.status_code == 200
    assert r.json()["journey_stage"] == "EXTRACTING"


def test_patch_journey_backward_409(auth_client, master_db):
    _set_stage(master_db, "CONFIRMED")
    r = auth_client.patch("/tenants/me/journey", json={"journey_stage": "NEW"})
    assert r.status_code == 409
    assert _stage(master_db).journey_stage == "CONFIRMED"


def test_patch_journey_invalid_422(auth_client, master_db):
    _set_stage(master_db, "NEW")
    r = auth_client.patch("/tenants/me/journey", json={"journey_stage": "BOGUS"})
    assert r.status_code == 422


def test_patch_journey_clears_is_first_session(auth_client, master_db):
    """#259: PATCH advancing to CONFIRMED clears is_first_session (DEC-040)."""
    _set_stage(master_db, "NEEDS_REVIEW", first_session=True)
    r = auth_client.patch("/tenants/me/journey", json={"journey_stage": "CONFIRMED"})
    assert r.status_code == 200
    assert r.json()["journey_stage"] == "CONFIRMED"
    assert r.json()["is_first_session"] is False
    assert _stage(master_db).is_first_session is False


def test_patch_to_activated_clears_first_session(auth_client, master_db):
    _set_stage(master_db, "CONFIRMED", first_session=True)
    r = auth_client.patch("/tenants/me/journey", json={"journey_stage": "ACTIVATED"})
    assert r.status_code == 200
    assert r.json()["is_first_session"] is False


# ── hook: consent reminder_send activates (gated) ────────────────────────────
def test_consent_channel_activates_when_confirmed(auth_client, master_db):
    _set_stage(master_db, "CONFIRMED", first_session=True)
    r = auth_client.post("/consent", json={
        "purpose": "reminder_send", "channel": "telegram", "channel_target_ref": "12345",
    })
    assert r.status_code == 201
    t = _stage(master_db)
    assert t.journey_stage == "ACTIVATED"
    assert t.is_first_session is False


def test_consent_channel_does_not_skip_spine(auth_client, master_db):
    """reminder_send while still NEW must not jump to ACTIVATED (gated)."""
    _set_stage(master_db, "NEW")
    r = auth_client.post("/consent", json={
        "purpose": "reminder_send", "channel": "telegram", "channel_target_ref": "12345",
    })
    assert r.status_code == 201
    assert _stage(master_db).journey_stage == "NEW"


def test_consent_without_channel_ref_no_activate(auth_client, master_db):
    _set_stage(master_db, "CONFIRMED")
    r = auth_client.post("/consent", json={"purpose": "reminder_send"})  # no channel_target_ref
    assert r.status_code == 201
    assert _stage(master_db).journey_stage == "CONFIRMED"


# ── hook: chat query graduates ACTIVATED → STEADY ────────────────────────────
def test_chat_query_graduates_to_steady(auth_client, master_db, monkeypatch):
    _set_stage(master_db, "ACTIVATED", first_session=False)

    async def _no_tools(*a, **k):
        return [], {}
    monkeypatch.setattr(chat_query, "_select_tools", _no_tools)

    r = auth_client.post("/chat/query", json={"question": "bất kỳ"})
    assert r.status_code == 200
    assert _stage(master_db).journey_stage == "STEADY"


def test_chat_query_no_promote_before_activated(auth_client, master_db, monkeypatch):
    _set_stage(master_db, "CONFIRMED")

    async def _no_tools(*a, **k):
        return [], {}
    monkeypatch.setattr(chat_query, "_select_tools", _no_tools)

    auth_client.post("/chat/query", json={"question": "bất kỳ"})
    assert _stage(master_db).journey_stage == "CONFIRMED"

"""Tests for GET/PUT /tenants/me/compliance-profile (#495)."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantProfile, TenantUser
from main import app


def _ensure_profile(tenant_id: str) -> TenantProfile:
    """Create an empty TenantProfile row if it does not exist."""
    db = MasterSessionLocal()
    try:
        profile = db.query(TenantProfile).filter_by(tenant_id=tenant_id).first()
        if profile is None:
            profile = TenantProfile(tenant_id=tenant_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile
    finally:
        db.close()


def _other_tenant_client():
    """Create a fresh tenant + user in master.db and return a logged-in client."""
    init_master_db()
    tid = f"compliance-iso-{uuid.uuid4().hex[:8]}"
    init_tenant_db(tid)

    db = MasterSessionLocal()
    try:
        db.add(Tenant(id=tid, name=f"ISO {tid}", db_path=f"tenants/{tid}.db"))
        db.add(
            TenantUser(
                tenant_id=tid,
                username="isouser",
                hashed_password=get_password_hash("isopass"),
                role="admin",
            )
        )
        db.commit()
    finally:
        db.close()

    c = TestClient(app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": tid, "username": "isouser", "password": "isopass"},
    )
    assert r.status_code == 200, f"Login failed: {r.text}"
    return c


# ── GET /tenants/me/compliance-profile ─────────────────────────────────────


def test_get_compliance_profile_returns_all_none(auth_client, test_tenant):
    _ensure_profile(test_tenant)
    r = auth_client.get("/tenants/me/compliance-profile")
    assert r.status_code == 200
    data = r.json()
    assert data["legal_form"] is None
    assert data["has_employees"] is None
    assert data["vat_period"] is None
    assert data["fiscal_year_start"] is None


def test_get_compliance_profile_no_profile_row_returns_defaults(auth_client):
    """GET returns empty defaults (not 404) when no TenantProfile row exists (#529)."""
    r = auth_client.get("/tenants/me/compliance-profile")
    assert r.status_code == 200
    data = r.json()
    assert data["legal_form"] is None
    assert data["has_employees"] is None


# ── PUT /tenants/me/compliance-profile ───────────────────────────────────────


def test_put_compliance_profile_updates_fields(auth_client, test_tenant):
    _ensure_profile(test_tenant)
    r = auth_client.put(
        "/tenants/me/compliance-profile",
        json={
            "legal_form": "TNHH",
            "has_employees": True,
            "vat_period": "month",
            "fiscal_year_start": "2026-01-01",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["legal_form"] == "TNHH"
    assert data["has_employees"] is True
    assert data["vat_period"] == "month"
    assert data["fiscal_year_start"] == "2026-01-01"

    # GET reflects the update.
    r = auth_client.get("/tenants/me/compliance-profile")
    assert r.status_code == 200
    data = r.json()
    assert data["legal_form"] == "TNHH"


def test_put_compliance_profile_invalid_vat_period(auth_client, test_tenant):
    _ensure_profile(test_tenant)
    r = auth_client.put(
        "/tenants/me/compliance-profile",
        json={"vat_period": "year"},
    )
    assert r.status_code == 422


# ── Tenant isolation ───────────────────────────────────────────────────────


def test_put_compliance_profile_upsert_no_profile_row(auth_client):
    """PUT creates TenantProfile if missing — first-time tenant (#529)."""
    r = auth_client.put(
        "/tenants/me/compliance-profile",
        json={"legal_form": "TNHH", "has_employees": True, "vat_period": "quarter"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["legal_form"] == "TNHH"
    assert data["has_employees"] is True
    assert data["vat_period"] == "quarter"


def test_get_compliance_profile_is_tenant_isolated(auth_client, test_tenant):
    _ensure_profile(test_tenant)
    auth_client.put(
        "/tenants/me/compliance-profile",
        json={"legal_form": "TNHH"},
    )

    other = _other_tenant_client()
    r = other.get("/tenants/me/compliance-profile")
    assert r.status_code == 200
    assert r.json()["legal_form"] is None

"""Per-tenant extraction cost tracking (#255 pilot monitoring).

- quota.add_extraction_cost increments month + lifetime; reset zeroes month only.
- GET /admin/tenants/cost-summary: admin-only, per-tenant + totals + gm_pct,
  NULL costs summed as 0.
"""
import os
import sys
from datetime import date

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, init_master_db
from app.models.master import Tenant, TenantUser
from app.services import quota
from main import app

TENANT = "cost-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Cost Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    for uname, role in (("costadmin", "admin"), ("coststaff", "staff")):
        if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == uname).first():
            db.add(TenantUser(tenant_id=TENANT, username=uname,
                              hashed_password=get_password_hash("cpass"), role=role))
    db.commit()
    db.close()


@pytest.fixture
def master_db():
    d = MasterSessionLocal()
    try:
        yield d
    finally:
        d.close()


def _client(username):
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": username, "password": "cpass"})
    assert r.status_code == 200
    return c


def _set(master_db, **kw):
    t = master_db.query(Tenant).filter(Tenant.id == TENANT).first()
    for k, v in kw.items():
        setattr(t, k, v)
    master_db.commit()


# ── service ──────────────────────────────────────────────────────────────────
def test_add_extraction_cost_increments_both(master_db):
    _set(master_db, cost_vnd_month=0, cost_vnd_total=0)
    assert quota.add_extraction_cost(master_db, TENANT, 177.0) is True
    quota.add_extraction_cost(master_db, TENANT, 23.0)
    master_db.expire_all()
    t = master_db.query(Tenant).filter(Tenant.id == TENANT).first()
    assert t.cost_vnd_month == 200.0
    assert t.cost_vnd_total == 200.0


def test_add_zero_cost_noop(master_db):
    _set(master_db, cost_vnd_month=50, cost_vnd_total=50)
    assert quota.add_extraction_cost(master_db, TENANT, 0) is False
    master_db.expire_all()
    assert master_db.query(Tenant).filter(Tenant.id == TENANT).first().cost_vnd_month == 50


def test_reset_zeroes_month_keeps_total(master_db):
    _set(master_db, cost_vnd_month=300, cost_vnd_total=300, docs_used_month=23)
    quota.reset_all_quotas(master_db, today=date(2026, 6, 24))
    master_db.expire_all()
    t = master_db.query(Tenant).filter(Tenant.id == TENANT).first()
    assert t.cost_vnd_month == 0          # month reset
    assert t.cost_vnd_total == 300        # lifetime kept
    assert t.docs_used_month == 0


# ── admin endpoint ───────────────────────────────────────────────────────────
def test_cost_summary_admin(master_db):
    _set(master_db, cost_vnd_month=4071.0, cost_vnd_total=4071.0, docs_used_month=23)
    data = _client("costadmin").get("/admin/tenants/cost-summary").json()
    assert data["period"] == date.today().strftime("%Y-%m")
    row = next(r for r in data["tenants"] if r["tenant_id"] == TENANT)
    assert row["docs_month"] == 23
    assert row["cost_vnd_month"] == 4071.0
    assert row["revenue_vnd_month"] == 100_000
    assert row["gm_pct"] == 95.9          # (100000-4071)/100000*100
    assert data["totals"]["cost_vnd_month"] >= 4071.0


def test_cost_summary_non_admin_403():
    r = _client("coststaff").get("/admin/tenants/cost-summary")
    assert r.status_code == 403


def test_cost_summary_requires_auth():
    assert TestClient(app).get("/admin/tenants/cost-summary").status_code in (401, 403)


def test_cost_summary_zero_cost_tenant(master_db):
    """A tenant that hasn't extracted yet (cost 0, the NOT-NULL default) → cost 0,
    gm 100. The endpoint also defends with `or 0.0` if a column were ever NULL."""
    _set(master_db, cost_vnd_month=0, cost_vnd_total=0, docs_used_month=0)
    data = _client("costadmin").get("/admin/tenants/cost-summary").json()
    row = next(r for r in data["tenants"] if r["tenant_id"] == TENANT)
    assert row["cost_vnd_month"] == 0.0
    assert row["gm_pct"] == 100.0   # (100000-0)/100000*100

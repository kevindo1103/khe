"""GET /obligations/summary — server-side dashboard aggregate (#199 follow-up).

Reuses the chat aggregate (count + grouped labels + status_breakdown) so the FE
renders server groups[].label instead of FE-deriving direction counts.
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
from app.models.tenant import Document, Obligation
from main import app

TENANT = "oblsum-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="OblSum Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "ouser").first():
        db.add(TenantUser(tenant_id=TENANT, username="ouser",
                          hashed_password=get_password_hash("opass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "ouser", "password": "opass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _wipe(db):
    db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
    db.query(Document).filter(Document.tenant_id == TENANT).delete()
    db.commit()


def _doc(db):
    d = Document(tenant_id=TENANT, file_name="c.pdf", file_path="x/y.pdf", status="extracted")
    db.add(d); db.commit(); db.refresh(d)
    return d


def _ob(db, doc, **kw):
    kw.setdefault("status", "pending")
    o = Obligation(tenant_id=TENANT, document_id=doc.id, description="x", recurrence="once", **kw)
    db.add(o); db.commit()
    return o


def test_summary_by_direction_with_labels(auth_client, db):
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31")
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-11-30")
    _ob(db, doc, direction="quyền_lợi", due_date="2026-10-01")

    r = auth_client.get("/obligations/summary?group_by=direction")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert data["group_by"] == "direction"
    groups = {g["key"]: g for g in data["groups"]}
    assert groups["nghĩa_vụ"]["count"] == 2
    assert groups["nghĩa_vụ"]["label"] == "Bạn cần"          # server label, not FE-derived
    assert groups["quyền_lợi"]["label"] == "Đối tác cần làm cho bạn"
    assert data["source"]["obligation_count"] == 3
    assert "status_breakdown" in data


def test_summary_active_only_default_excludes_terminal(auth_client, db):
    """#253 FE: dashboard total + cards count active-only by default (no done/cancelled)."""
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31", status="pending")
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-11-30", status="done")       # terminal
    _ob(db, doc, direction="quyền_lợi", due_date="2026-10-01", status="cancelled")  # terminal
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-01-01", status="overdue")     # active (late)

    data = auth_client.get("/obligations/summary?group_by=direction").json()
    assert data["total"] == 2          # 1 pending + 1 overdue; done/cancelled excluded
    groups = {g["key"]: g["count"] for g in data["groups"]}
    assert groups.get("nghĩa_vụ") == 2
    assert "quyền_lợi" not in groups   # its only obligation was cancelled


def test_summary_active_only_false_includes_terminal(auth_client, db):
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31", status="pending")
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-11-30", status="done")

    data = auth_client.get("/obligations/summary?active_only=false").json()
    assert data["total"] == 2          # full historical count includes done


def test_summary_zero_is_valid(auth_client, db):
    _wipe(db)
    r = auth_client.get("/obligations/summary")
    assert r.status_code == 200
    assert r.json()["total"] == 0          # empty tenant → valid 0, not an error


def test_summary_default_group_by_direction(auth_client, db):
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31")
    data = auth_client.get("/obligations/summary").json()
    assert data["group_by"] == "direction"


def test_summary_requires_auth():
    anon = TestClient(app)
    assert anon.get("/obligations/summary").status_code in (401, 403)


def test_summary_does_not_shadow_list(auth_client, db):
    """/summary is a distinct route from the list — both resolve correctly."""
    _wipe(db)
    assert auth_client.get("/obligations/").status_code == 200
    assert auth_client.get("/obligations/summary").status_code == 200

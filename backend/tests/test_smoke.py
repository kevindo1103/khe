import os
import sys

# Ensure backend/ is on path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Seed a test tenant + user before running smoke tests."""
    init_master_db()
    init_tenant_db("test-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "test-tenant").first()
    if not tenant:
        db.add(Tenant(id="test-tenant", name="Test Tenant", db_path="tenants/test-tenant.db"))
        db.commit()

    user = (
        db.query(TenantUser)
        .filter(TenantUser.tenant_id == "test-tenant", TenantUser.username == "testuser")
        .first()
    )
    if not user:
        db.add(
            TenantUser(
                tenant_id="test-tenant",
                username="testuser",
                hashed_password=get_password_hash("testpass"),
                role="staff",
            )
        )
        db.commit()
    db.close()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    response = client.post(
        "/auth/login",
        json={"tenant_id": "test-tenant", "username": "testuser", "password": "testpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" not in data
    assert "user" in data
    assert data["user"]["username"] == "testuser"
    assert data["tenant_id"] == "test-tenant"
    assert "khe_session" in response.cookies
    assert response.cookies["khe_session"] is not None


def test_login_failure():
    response = client.post(
        "/auth/login",
        json={"tenant_id": "test-tenant", "username": "testuser", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_me_authenticated():
    """login → /me 200 → logout → /me 401"""
    # Use separate TestClient instances so cookies are isolated per scenario
    from fastapi.testclient import TestClient
    from main import app

    # 1. Login
    client_auth = TestClient(app)
    login = client_auth.post(
        "/auth/login",
        json={"tenant_id": "test-tenant", "username": "testuser", "password": "testpass"},
    )
    assert login.status_code == 200
    assert "khe_session" in client_auth.cookies

    # 2. /me returns user info from cookie
    me = client_auth.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "testuser"
    assert me.json()["tenant_id"] == "test-tenant"

    # 3. /me 401 without cookie (fresh client = no cookie)
    client_anon = TestClient(app)
    me_no_cookie = client_anon.get("/auth/me")
    assert me_no_cookie.status_code == 401

    # 4. Logout clears cookie
    logout = client_auth.post("/auth/logout")
    assert logout.status_code == 200

    # 5. /me 401 after logout (cookie cleared)
    me_after = client_auth.get("/auth/me")
    assert me_after.status_code == 401


def test_get_tenant_session():
    """get_tenant_session(tid) must return an open Session and create tables."""
    session = get_tenant_session("test-tenant")
    assert session is not None
    # Quick sanity: query something that will fail if tables are missing
    from app.models.tenant import Document
    result = session.query(Document).first()
    session.close()
